#!/usr/bin/env python3
"""
Inference Cost Test: Portuguese vs English Token Generation Comparison

Configurable parameters: API base URL, API key, model name, number of rounds.
Uses equivalent JavaScript task prompts in each language without language hints.
Extracts rich statistics including mean, std dev, CI, paired t-test.
"""

import json
import urllib.request
import time
import math
import argparse
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Optional


# ========== DEFAULT CONFIG ==========
DEFAULT_API_URL = "http://localhost:1234/v1/chat/completions"
DEFAULT_API_KEY = ""  # Empty for local LM Studio (no auth)
DEFAULT_MODEL = "kat-coder-v2.5-dev-apex"
DEFAULT_NUM_RUNS = 50
DEFAULT_TEMPERATURE = 0.0


# ========== PROMPTS - Equivalent JavaScript Task ==========

PROMPT_ENGLISH = """Create a simple task management application in JavaScript with the following requirements:

1. The app should allow users to add new tasks with a title and description
2. Each task should have a status: 'pending', 'in_progress', or 'completed'
3. Users can toggle task completion by clicking on it
4. Display tasks grouped by their status (Pending, In Progress, Completed sections)
5. Include a filter to show only pending tasks, in-progress tasks, or completed tasks
6. Add the ability to delete tasks
7. Use localStorage to persist tasks between sessions
8. The UI should be clean and responsive using vanilla JavaScript (no frameworks)

Provide:
- index.html with the HTML structure
- styles.css for styling
- app.js with all the logic
- Clear comments explaining each major section
- A README.md with setup instructions"""

PROMPT_PORTUGUESE = """Crie um aplicativo simples de gerenciamento de tarefas em JavaScript com os seguintes requisitos:

1. O aplicativo deve permitir que os usuários adicionem novas tarefas com título e descrição
2. Cada tarefa deve ter um status: 'pendente', 'em_andamento' ou 'concluído'
3. Os usuários podem alternar a conclusão da tarefa clicando nela
4. Exiba as tarefas agrupadas por seu status (Seções Pendentes, Em Andamento, Concluídos)
5. Inclua um filtro para mostrar apenas tarefas pendentes, em andamento ou concluídas
6. Adicione a capacidade de excluir tarefas
7. Use localStorage para persistir as tarefas entre sessões
8. A interface deve ser limpa e responsiva usando JavaScript puro (sem frameworks)

Forneça:
- index.html com a estrutura HTML
- styles.css para estilização
- app.js com toda a lógica
- Comentários claros explicando cada seção importante
- Um README.md com instruções de configuração"""


@dataclass
class RunResult:
    run_number: int
    language: str
    completion_tokens: int
    prompt_tokens: int
    total_tokens: int
    char_count: int
    elapsed: float
    response: str = ""  # Full response text for validation


# ========== STATISTICS FUNCTIONS ==========

def mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0


def std_dev(values: List[float], ddof: int = 1) -> float:
    if len(values) < 2:
        return 0.0
    m = mean(values)
    variance = sum((x - m) ** 2 for x in values) / (len(values) - ddof)
    return math.sqrt(variance)


def ci_95(values: List[float]) -> tuple:
    n = len(values)
    if n < 2:
        return (values[0], values[0]) if values else (0, 0)
    m = mean(values)
    se = std_dev(values) / math.sqrt(n)
    t_val = 1.96 if n >= 30 else 2.0
    return (m - t_val * se, m + t_val * se)


def paired_t_test(en_values: List[float], pt_values: List[float]) -> tuple:
    if len(en_values) != len(pt_values):
        return 0.0, 1.0, False
    
    n = len(en_values)
    diffs = [pt - en for en, pt in zip(en_values, pt_values)]
    mean_diff = mean(diffs)
    
    if n < 2:
        return mean_diff, 1.0, False
    
    std_diff = std_dev(diffs)
    se = std_diff / math.sqrt(n)
    
    if se == 0:
        return mean_diff, float('inf'), True
    
    t_stat = mean_diff / se
    from math import erf
    p_value = 1 - erf(abs(t_stat) / math.sqrt(2))
    
    significant = p_value < 0.05
    return mean_diff, t_stat, significant


def coefficient_of_variation(values: List[float]) -> float:
    m = mean(values)
    if m == 0:
        return 0.0
    return (std_dev(values) / m) * 100


def percentile(values: List[float], p: int) -> float:
    sorted_vals = sorted(values)
    k = (len(sorted_vals) - 1) * (p / 100)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)


# ========== INFERENCE FUNCTIONS ==========

def run_inference(
    prompt: str, 
    api_url: str, 
    model: str, 
    api_key: str = "",
    session_name: str = "Test", 
    run_num: int = 1,
    temperature: float = 0.0
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
        "temperature": temperature
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        api_url,
        data=data,
        headers=headers,
        method='POST'
    )
    
    start_time = time.time()
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            elapsed = time.time() - start_time
            result = json.loads(response.read().decode('utf-8'))
            
            usage = result.get('usage', {})
            completion_tokens = usage.get('completion_tokens', 0)
            prompt_tokens = usage.get('prompt_tokens', 0)
            total_tokens = usage.get('total_tokens', 0)
            response_text = result['choices'][0]['message']['content']
            
            return RunResult(
                run_number=run_num,
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
            run_number=run_num,
            language=session_name,
            completion_tokens=0,
            prompt_tokens=0,
            total_tokens=0,
            char_count=0,
            elapsed=0.0
        )


def print_stats(title: str, values: List[float], unit: str = ""):
    """Print statistics for a list of values."""
    if not values:
        print(f"  {title}: No data")
        return
    
    m = mean(values)
    sd = std_dev(values)
    ci_low, ci_high = ci_95(values)
    cv = coefficient_of_variation(values)
    
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")
    print(f"  N:                  {len(values):,}")
    print(f"  Mean:               {m:>12,.2f} {unit}")
    print(f"  Std Dev:            {sd:>12,.2f} {unit}")
    print(f"  CV%:                {cv:>12.2f}%")
    print(f"  Min:                {min(values):>12,.2f} {unit}")
    print(f"  Max:                {max(values):>12,.2f} {unit}")
    print(f"  P25:                {percentile(values, 25):>12,.2f} {unit}")
    print(f"  Median (P50):       {percentile(values, 50):>12,.2f} {unit}")
    print(f"  P75:                {percentile(values, 75):>12,.2f} {unit}")
    print(f"  95% CI for Mean:    [{ci_low:>10.2f}, {ci_high:.2f}] {unit}")


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
                        help=f'Number of test rounds (default: {DEFAULT_NUM_RUNS})')
    parser.add_argument('--temperature', type=float, default=DEFAULT_TEMPERATURE,
                        help=f'Temperature for inference (default: {DEFAULT_TEMPERATURE}, deterministic)')
    parser.add_argument('--output', default='/home/tosol/inference_cost_results.json',
                        help='Output JSON file path')
    
    args = parser.parse_args()
    
    print(f"\n🚀 Starting Inference Cost Test")
    print(f"   Model: {args.model}")
    print(f"   API: {args.api_url}")
    print(f"   Runs: {args.runs}")
    print(f"   Temperature: {args.temperature}")
    print(f"   API Key: {'***' if args.api_key else '(none - local)'}")
    
    all_results = []
    en_tokens_list = []
    pt_tokens_list = []
    en_chars_list = []
    pt_chars_list = []
    en_time_list = []
    pt_time_list = []
    
    # Run test rounds
    for run in range(1, args.runs + 1):
        print(f"\n{'='*70}")
        print(f"  RUN {run}/{args.runs}")
        print(f"{'='*70}")
        
        # English inference
        en_result = run_inference(PROMPT_ENGLISH, args.api_url, args.model, 
                                  args.api_key, "English", run, args.temperature)
        all_results.append(en_result)
        en_tokens_list.append(en_result.completion_tokens)
        en_chars_list.append(en_result.char_count)
        en_time_list.append(en_result.elapsed)
        
        print(f"  ✅ English: {en_result.completion_tokens:,} tokens, "
              f"{en_result.char_count:,} chars, {en_result.elapsed:.1f}s")
        
        # Brief pause
        time.sleep(1)
        
        # Portuguese inference
        pt_result = run_inference(PROMPT_PORTUGUESE, args.api_url, args.model,
                                  args.api_key, "Portuguese", run, args.temperature)
        all_results.append(pt_result)
        pt_tokens_list.append(pt_result.completion_tokens)
        pt_chars_list.append(pt_result.char_count)
        pt_time_list.append(pt_result.elapsed)
        
        print(f"  ✅ Portuguese: {pt_result.completion_tokens:,} tokens, "
              f"{pt_result.char_count:,} chars, {pt_result.elapsed:.1f}s")
    
    # ========== STATISTICAL ANALYSIS ==========
    print(f"\n\n{'█'*70}")
    print(f"  STATISTICAL ANALYSIS RESULTS")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'█'*70}")
    
    # Per-language statistics
    print_stats("English Output Tokens", en_tokens_list, "tokens")
    print_stats("Portuguese Output Tokens", pt_tokens_list, "tokens")
    print_stats("English Characters", en_chars_list, "chars")
    print_stats("Portuguese Characters", pt_chars_list, "chars")
    print_stats("English Inference Time", en_time_list, "seconds")
    print_stats("Portuguese Inference Time", pt_time_list, "seconds")
    
    # Paired comparison statistics
    print(f"\n{'─'*60}")
    print(f"  PAIRED COMPARISON (English vs Portuguese)")
    print(f"{'─'*60}")
    
    token_diffs = [pt - en for pt, en in zip(pt_tokens_list, en_tokens_list)]
    char_diffs = [pt - en for pt, en in zip(pt_chars_list, en_chars_list)]
    time_diffs = [pt - en for pt, en in zip(pt_time_list, en_time_list)]
    
    print(f"\n  Token Difference (PT - EN):")
    print(f"    Mean: {mean(token_diffs):>+,.2f} tokens")
    print(f"    Std Dev: {std_dev(token_diffs):,.2f}")
    print(f"    Min: {min(token_diffs):>+,.2f}")
    print(f"    Max: {max(token_diffs):>+,.2f}")
    
    print(f"\n  Character Difference (PT - EN):")
    print(f"    Mean: {mean(char_diffs):>+,.2f} chars")
    print(f"    Std Dev: {std_dev(char_diffs):,.2f}")
    print(f"    Min: {min(char_diffs):>+,.2f}")
    print(f"    Max: {max(char_diffs):>+,.2f}")
    
    print(f"\n  Time Difference (PT - EN):")
    print(f"    Mean: {mean(time_diffs):>+,.2f} seconds")
    print(f"    Std Dev: {std_dev(time_diffs):,.2f}")
    print(f"    Min: {min(time_diffs):>+,.2f}")
    print(f"    Max: {max(time_diffs):>+,.2f}")
    
    # Paired t-tests
    token_mean, token_t, token_sig = paired_t_test(en_tokens_list, pt_tokens_list)
    char_mean, char_t, char_sig = paired_t_test(en_chars_list, pt_chars_list)
    time_mean, time_t, time_sig = paired_t_test(en_time_list, pt_time_list)
    
    print(f"\n  {'='*50}")
    print(f"  SIGNIFICANCE TESTS (Paired t-test)")
    print(f"  {'='*50}")
    print(f"\n  Token count:")
    print(f"    Mean diff: {token_mean:+,.2f}, t-stat: {token_t:.2f}", end="")
    print(f"  {'✓ SIGNIFICANT' if token_sig else '✗ NOT significant'} (α=0.05)")
    
    print(f"\n  Character count:")
    print(f"    Mean diff: {char_mean:+,.2f}, t-stat: {char_t:.2f}", end="")
    print(f"  {'✓ SIGNIFICANT' if char_sig else '✗ NOT significant'} (α=0.05)")
    
    print(f"\n  Inference time:")
    print(f"    Mean diff: {time_mean:+,.2f}s, t-stat: {time_t:.2f}", end="")
    print(f"  {'✓ SIGNIFICANT' if time_sig else '✗ NOT significant'} (α=0.05)")
    
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
    print(f"\n  {'='*50}")
    print(f"  DISTRIBUTION ANALYSIS")
    print(f"  {'='*50}")
    
    ratios = [pt/en for pt, en in zip(pt_tokens_list, en_tokens_list) if en > 0]
    print(f"\n  PT/EN Token Ratio:")
    print(f"    Mean: {mean(ratios):.3f}x")
    print(f"    Min:  {min(ratios):.3f}x")
    print(f"    Max:  {max(ratios):.3f}x")
    print(f"    Std:  {std_dev(ratios):.3f}")
    
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
    print(f"     for equivalent JavaScript tasks on this model.")
    
    # Save results
    output_file = args.output
    summary_data = {
        'timestamp': datetime.now().isoformat(),
        'model': args.model,
        'api_url': args.api_url,
        'num_runs': args.runs,
        'summary_statistics': {
            'english_tokens_mean': en_tokens_mean,
            'portuguese_tokens_mean': pt_tokens_mean,
            'token_percentage_diff': pct_token_diff,
            'char_percentage_diff': pct_char_diff,
            'time_percentage_diff': pct_time_diff,
            'cost_ratio': cost_ratio,
        },
        'significance_tests': {
            'tokens_significant': token_sig,
            'chars_significant': char_sig,
            'time_significant': time_sig,
        },
        'all_runs': [
            {
                'run': r.run_number,
                'language': r.language,
                'completion_tokens': r.completion_tokens,
                'char_count': r.char_count,
                'elapsed': round(r.elapsed, 2),
                'response': r.response
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
