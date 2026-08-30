#!/usr/bin/env python3
"""
Inference Cost Test: Portuguese vs English Token Generation Comparison

Configurable parameters: API base URL, API key, model name, seed, problems list.
Runs equivalent prompts from problems/ folder and produces consolidated statistics.
"""

import json
import urllib.request
import time
import math
import argparse
import os
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


# ========== DEFAULT CONFIG ==========
DEFAULT_API_URL = "http://localhost:1234/v1/chat/completions"
DEFAULT_API_BASE = "http://localhost:1234"  # Base URL for model management
DEFAULT_API_KEY = ""  # Empty for local LM Studio (no auth)
DEFAULT_MODEL = "kat-coder-v2.5-dev-apex"
DEFAULT_NUM_RUNS = 1  # One round per problem
DEFAULT_TEMPERATURE = 0.0
DEFAULT_SEED = None  # None = random seed each run
DEFAULT_PROBLEMS = "1"  # Default to problem 1
DEFAULT_UNLOAD_MODEL = True  # Unload model before each test batch
PROBLEMS_DIR = Path(__file__).parent / "problems"


@dataclass
class RunResult:
    problem_id: str
    language: str
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int
    char_count: int
    elapsed: float
    response: str = ""  # Full response text for validation


# ========== STATISTICS FUNCTIONS ==========

def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def std_dev(values: List[float], ddof: int = 1) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    variance = sum((x - m) ** 2 for x in values) / (len(values) - ddof)
    return math.sqrt(variance)


def percentile(values: List[float], p: int) -> float:
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * (p / 100)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)


def p95(values: List[float]) -> float:
    return percentile(values, 95)


# ========== MODEL MANAGEMENT ==========

def unload_model(api_base: str, model: str) -> bool:
    """Unload (eject) a model from LM Studio memory via REST API."""
    url = f"{api_base}/api/v1/models/unload"
    payload = json.dumps({"instance_id": model}).encode('utf-8')
    
    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('instance_id') == model:
                print(f"  ✅ Model {model} unloaded from memory")
                return True
            else:
                print(f"  ⚠️  Model unload returned unexpected response: {result}")
                return False
    except Exception as e:
        print(f"  ⚠️  Failed to unload model: {e}")
        return False


def wait_for_model_load(api_base: str, model: str, timeout: int = 60) -> bool:
    """Wait for model to be loaded in LM Studio after unload."""
    url = f"{api_base}/api/v1/models"
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                for m in data.get('models', []):
                    if m.get('key') == model and m.get('loaded_instances'):
                        print(f"  ✅ Model {model} is loaded")
                        return True
        except:
            pass
        time.sleep(1)
    
    print(f"  ⚠️  Timeout waiting for model {model} to load")
    return False


# ========== PROMPT LOADING ==========

def load_prompt(problem_id: str, language: str) -> str:
    """Load prompt from problems/{pN}/{language}.txt or problems/{N}/{language}.txt"""
    # Try both p1 and 1 formats
    for prefix in ['p', '']:
        file_path = PROBLEMS_DIR / f"{prefix}{problem_id}" / f"{language}.txt"
        if file_path.exists():
            return file_path.read_text(encoding='utf-8').strip()
    raise FileNotFoundError(f"Prompt not found for problem {problem_id} (tried p{problem_id}/ and {problem_id}/)")


def get_problem_ids() -> List[str]:
    """Get list of available problems from problems/ directory"""
    if not PROBLEMS_DIR.exists():
        return []
    return sorted([d.name for d in PROBLEMS_DIR.iterdir() if d.is_dir()])


# ========== INFERENCE FUNCTIONS ==========

def run_inference(
    prompt: str, 
    api_url: str, 
    model: str, 
    api_key: str = "",
    session_name: str = "Test", 
    run_num: int = 1,
    temperature: float = 0.0,
    seed: Optional[int] = None
) -> RunResult:
    """Run a single inference request and return metrics."""
    headers = {'Content-Type': 'application/json'}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant that writes clean, well-structured code."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": -1
    }
    
    # Add seed for deterministic output if specified
    if seed is not None:
        payload["seed"] = seed
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        api_url,
        data=data,
        headers=headers,
        method='POST'
    )
    
    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as response:  # 5 minute timeout
            elapsed = time.time() - start_time
            result = json.loads(response.read().decode('utf-8'))
            
            usage = result.get('usage', {})
            completion_tokens = usage.get('completion_tokens', 0)
            prompt_tokens = usage.get('prompt_tokens', 0)
            total_tokens = usage.get('total_tokens', 0)
            response_text = result['choices'][0]['message']['content']
            
            return RunResult(
                problem_id=f"run_{run_num}",
                language=session_name,
                completion_tokens=completion_tokens,
                prompt_tokens=prompt_tokens,
                total_tokens=total_tokens,
                char_count=len(response_text),
                elapsed=elapsed,
                response=response_text
            )
    except Exception as e:
        print(f"  ❌ Error in {session_name} run {run_num}: {e}")
        return RunResult(
            problem_id=f"run_{run_num}",
            language=session_name,
            completion_tokens=0,
            prompt_tokens=0,
            total_tokens=0,
            char_count=0,
            elapsed=0.0,
            response=""
        )


def print_consolidated_stats(title: str, values: List[float], unit: str = ""):
    """Print consolidated statistics for a list of values."""
    if not values:
        print(f"  {title}: No data")
        return
    
    m = mean(values)
    sd = std_dev(values)
    p95_val = p95(values)
    
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")
    print(f"  N:                  {len(values):,}")
    print(f"  Min:                {min(values):>12,.2f} {unit}")
    print(f"  Avg (Mean):         {m:>12,.2f} {unit}")
    print(f"  Max:                {max(values):>12,.2f} {unit}")
    print(f"  Std Dev:            {sd:>12,.2f} {unit}")
    print(f"  P95:                {p95_val:>12,.2f} {unit}")


# ========== MAIN EXECUTION ==========

def main():
    parser = argparse.ArgumentParser(
        description='Inference Cost Test: Portuguese vs English Token Comparison'
    )
    parser.add_argument('--api-url', default=DEFAULT_API_URL, 
                        help=f'API base URL (default: {DEFAULT_API_URL})')
    parser.add_argument('--api-key', default=DEFAULT_API_KEY,
                        help='API key for authentication (leave empty for local)')
    parser.add_argument('--model', default=DEFAULT_MODEL,
                        help=f'Model name (default: {DEFAULT_MODEL})')
    parser.add_argument('--runs', type=int, default=DEFAULT_NUM_RUNS,
                        help=f'Number of runs per problem (default: {DEFAULT_NUM_RUNS})')
    parser.add_argument('--temperature', type=float, default=DEFAULT_TEMPERATURE,
                        help=f'Temperature for inference (default: {DEFAULT_TEMPERATURE}, deterministic)')
    parser.add_argument('--seed', type=int, default=DEFAULT_SEED,
                        help='Random seed for deterministic output (default: random each run)')
    parser.add_argument('--problems', type=str, default=DEFAULT_PROBLEMS,
                        help=f'Comma-separated problem IDs (default: {DEFAULT_PROBLEMS}, e.g., "1,2,3")')
    parser.add_argument('--output', default='/home/tosol/inference_cost_results.json',
                        help='Output JSON file path')
    parser.add_argument('--no-unload', action='store_true',
                        help='Disable automatic model unload before each test batch')
    
    args = parser.parse_args()
    
    # Parse problems list
    problem_ids = [p.strip() for p in args.problems.split(',')]
    
    print(f"\n🚀 Starting Inference Cost Test")
    print(f"   Model: {args.model}")
    print(f"   API: {args.api_url}")
    print(f"   Problems: {', '.join(problem_ids)}")
    print(f"   Runs per problem: {args.runs}")
    print(f"   Temperature: {args.temperature}")
    print(f"   Seed: {args.seed if args.seed else 'random (variance expected)'}")
    print(f"   API Key: {'***' if args.api_key else '(none - local)'}")
    print(f"   Unload model: {not args.no_unload} (before each batch)")
    
    all_results = []
    en_tokens_list = []
    pt_tokens_list = []
    en_chars_list = []
    pt_chars_list = []
    en_time_list = []
    pt_time_list = []
    
    # Run test for each problem
    for prob_id in problem_ids:
        print(f"\n{'='*70}")
        print(f"  PROBLEM: {prob_id}")
        print(f"{'='*70}")
        
        # Unload model before starting new problem batch (to clear GPU state)
        if not args.no_unload and DEFAULT_UNLOAD_MODEL:
            print(f"\n  🔄 Unloading model to clear GPU state...")
            unload_model(args.api_url.replace('/v1/chat/completions', ''), args.model)
            time.sleep(2)  # Brief pause to ensure unload completes
        
        try:
            # Load prompts
            prompt_en = load_prompt(prob_id, "en")
            prompt_pt = load_prompt(prob_id, "pt")
            
            for run in range(1, args.runs + 1):
                print(f"\n--- Run {run}/{args.runs} ---")
                
                # English inference
                en_result = run_inference(prompt_en, args.api_url, args.model, 
                                          args.api_key, "English", run, args.temperature, args.seed)
                en_result.problem_id = prob_id
                all_results.append(en_result)
                en_tokens_list.append(en_result.completion_tokens)
                en_chars_list.append(en_result.char_count)
                en_time_list.append(en_result.elapsed)
                
                print(f"  ✅ English: {en_result.completion_tokens:,} tokens, "
                      f"{en_result.char_count:,} chars, {en_result.elapsed:.1f}s")
                
                # Brief pause
                time.sleep(1)
                
                # Portuguese inference
                pt_result = run_inference(prompt_pt, args.api_url, args.model,
                                          args.api_key, "Portuguese", run, args.temperature, args.seed)
                pt_result.problem_id = prob_id
                all_results.append(pt_result)
                pt_tokens_list.append(pt_result.completion_tokens)
                pt_chars_list.append(pt_result.char_count)
                pt_time_list.append(pt_result.elapsed)
                
                print(f"  ✅ Portuguese: {pt_result.completion_tokens:,} tokens, "
                      f"{pt_result.char_count:,} chars, {pt_result.elapsed:.1f}s")
        
        except FileNotFoundError as e:
            print(f"\n  ⚠️  Skipping problem {prob_id}: {e}")
            continue
        except Exception as e:
            print(f"\n  ❌ Error running problem {prob_id}: {e}")
            continue
    
    # ========== CONSOLIDATED STATISTICS ==========
    print(f"\n\n{'█'*70}")
    print(f"  CONSOLIDATED STATISTICS (All Problems)")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'█'*70}")
    
    # Per-language consolidated statistics
    print_consolidated_stats("English Output Tokens", en_tokens_list, "tokens")
    print_consolidated_stats("Portuguese Output Tokens", pt_tokens_list, "tokens")
    print_consolidated_stats("English Characters", en_chars_list, "chars")
    print_consolidated_stats("Portuguese Characters", pt_chars_list, "chars")
    print_consolidated_stats("English Inference Time", en_time_list, "seconds")
    print_consolidated_stats("Portuguese Inference Time", pt_time_list, "seconds")
    
    # Paired comparison statistics
    if len(en_tokens_list) == len(pt_tokens_list):
        token_diffs = [pt - en for pt, en in zip(pt_tokens_list, en_tokens_list)]
        char_diffs = [pt - en for pt, en in zip(pt_chars_list, en_chars_list)]
        time_diffs = [pt - en for pt, en in zip(pt_time_list, en_time_list)]
        
        print(f"\n{'─'*60}")
        print(f"  PAIRED COMPARISON (English vs Portuguese)")
        print(f"{'─'*60}")
        
        print(f"\n  Token Difference (PT - EN):")
        if token_diffs:
            print(f"    Mean: {mean(token_diffs):>+,.2f} tokens")
            print(f"    Min:  {min(token_diffs):>+,.2f}")
            print(f"    Max:  {max(token_diffs):>+,.2f}")
            print(f"    P95:  {p95(token_diffs):>+,.2f}")
        else:
            print(f"    No data")
        
        print(f"\n  Character Difference (PT - EN):")
        if char_diffs:
            print(f"    Mean: {mean(char_diffs):>+,.2f} chars")
            print(f"    Min:  {min(char_diffs):>+,.2f}")
            print(f"    Max:  {max(char_diffs):>+,.2f}")
            print(f"    P95:  {p95(char_diffs):>+,.2f}")
        else:
            print(f"    No data")
        
        print(f"\n  Time Difference (PT - EN):")
        if time_diffs:
            print(f"    Mean: {mean(time_diffs):>+,.2f} seconds")
            print(f"    Min:  {min(time_diffs):>+,.2f}")
            print(f"    Max:  {max(time_diffs):>+,.2f}")
            print(f"    P95:  {p95(time_diffs):>+,.2f}")
        else:
            print(f"    No data")
    
    # Percentage differences
    en_tokens_mean = mean(en_tokens_list)
    pt_tokens_mean = mean(pt_tokens_list)
    pct_token_diff = ((pt_tokens_mean - en_tokens_mean) / en_tokens_mean) * 100 if en_tokens_mean > 0 else 0
    
    en_chars_mean = mean(en_chars_list)
    pt_chars_mean = mean(pt_chars_list)
    pct_char_diff = ((pt_chars_mean - en_chars_mean) / en_chars_mean) * 100 if en_chars_mean > 0 else 0
    
    en_time_mean = mean(en_time_list)
    pt_time_mean = mean(pt_time_list)
    pct_time_diff = ((pt_time_mean - en_time_mean) / en_time_mean) * 100 if en_time_mean > 0 else 0
    
    print(f"\n  {'='*50}")
    print(f"  PERCENTAGE DIFFERENCE SUMMARY")
    print(f"  {'='*50}")
    print(f"\n  Token generation:   {pct_token_diff:+.2f}% (PT vs EN)")
    print(f"  Character count:    {pct_char_diff:+.2f}% (PT vs EN)")
    print(f"  Inference time:     {pct_time_diff:+.2f}% (PT vs EN)")
    
    # Distribution analysis
    ratios = [pt/en for pt, en in zip(pt_tokens_list, en_tokens_list) if en > 0]
    if ratios:
        print(f"\n  {'='*50}")
        print(f"  DISTRIBUTION ANALYSIS")
        print(f"  {'='*50}")
        
        print(f"\n  PT/EN Token Ratio:")
        print(f"    Mean: {mean(ratios):.3f}x")
        print(f"    Min:  {min(ratios):.3f}x")
        print(f"    Max:  {max(ratios):.3f}x")
        print(f"    P95:  {p95(ratios):.3f}x")
    
    # Cost implication
    total_en_tokens = sum(en_tokens_list)
    total_pt_tokens = sum(pt_tokens_list)
    cost_ratio = total_pt_tokens / total_en_tokens if total_en_tokens > 0 else 0
    
    print(f"\n  {'='*50}")
    print(f"  COST IMPLICATION")
    print(f"  {'='*50}")
    print(f"\n  Total tokens (English):      {total_en_tokens:,}")
    print(f"  Total tokens (Portuguese):   {total_pt_tokens:,}")
    print(f"  Cost ratio:                  {cost_ratio:.2f}x")
    print(f"\n  💰 Portuguese inference costs ~{cost_ratio:.1f}x more than English")
    print(f"     for equivalent tasks on this model.")
    
    # Save results
    output_file = args.output
    summary_data = {
        'timestamp': datetime.now().isoformat(),
        'model': args.model,
        'api_url': args.api_url,
        'temperature': args.temperature,
        'seed': args.seed,
        'problems': problem_ids,
        'num_runs_per_problem': args.runs,
        'summary_statistics': {
            'english_tokens_mean': en_tokens_mean,
            'portuguese_tokens_mean': pt_tokens_mean,
            'token_percentage_diff': pct_token_diff,
            'char_percentage_diff': pct_char_diff,
            'time_percentage_diff': pct_time_diff,
            'cost_ratio': cost_ratio,
        },
        'consolidated_stats': {
            'english_tokens': {
                'min': min(en_tokens_list) if en_tokens_list else 0,
                'max': max(en_tokens_list) if en_tokens_list else 0,
                'avg': en_tokens_mean,
                'p95': p95(en_tokens_list) if en_tokens_list else 0,
            },
            'portuguese_tokens': {
                'min': min(pt_tokens_list) if pt_tokens_list else 0,
                'max': max(pt_tokens_list) if pt_tokens_list else 0,
                'avg': pt_tokens_mean,
                'p95': p95(pt_tokens_list) if pt_tokens_list else 0,
            },
        },
        'all_runs': [
            {
                'problem': r.problem_id,
                'run': int(r.problem_id.split('_')[1]) if '_' in r.problem_id else 1,
                'language': r.language,
                'completion_tokens': r.completion_tokens,
                'char_count': r.char_count,
                'elapsed': round(r.elapsed, 2),
                'response': r.response  # Full response for quality analysis
            }
            for r in all_results
        ]
    }
    
    with open(output_file, 'w') as f:
        json.dump(summary_data, f, indent=2)
    
    print(f"\n💾 Full results saved to {output_file}")
    print(f"{'█'*70}\n")


if __name__ == "__main__":
    main()
