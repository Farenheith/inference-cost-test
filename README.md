# Inference Cost Test

Compare token generation costs between Portuguese and English LLM inference. This tool runs equivalent prompts through an API in both languages and produces statistical analysis of the differences.

## Why?

When deploying multilingual AI applications, understanding the cost difference between languages is crucial for budgeting and optimization. This test reveals:

- **Token ratio** between Portuguese and English outputs
- **Statistical significance** of observed differences  
- **Cost implications** for production deployments
- **Consistency** across multiple runs

## Quick Start

```bash
# Run with defaults (local LM Studio, 50 rounds)
python3 -u inference_cost_test.py

# Custom configuration
python3 -u inference_cost_test.py \
    --api-url http://localhost:1234/v1/chat/completions \
    --model kat-coder-v2.5-dev-apex \
    --runs 50 \
    --output ./results/my-test.json

# With API key (remote providers like OpenAI, Anthropic)
python3 -u inference_cost_test.py \
    --api-url https://api.openai.com/v1/chat/completions \
    --api-key "sk-..." \
    --model gpt-4 \
    --runs 10
```

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--api-url` | API base URL for completions endpoint | `http://localhost:1234/v1/chat/completions` |
| `--api-key` | Authentication key (leave empty for local) | `(none)` |
| `--model` | Model name to test | `kat-coder-v2.5-dev-apex` |
| `--runs` | Number of sequential test rounds | 50 |
| `--output` | Output JSON file path | `./inference_cost_results.json` |

## How It Works

### Test Methodology

1. **Equivalent Prompts**: The same JavaScript task is described in both English and Portuguese without specifying the output language, allowing the model to respond naturally in each language.

2. **Sequential Execution**: Each pair runs sequentially (English → Portuguese) to avoid GPU memory conflicts and ensure consistent conditions.

3. **No Output Constraints**: No `max_tokens` limit allows models to complete naturally, revealing true token generation behavior.

### The Task Prompt

**English:**
> Create a simple task management application in JavaScript with requirements for adding tasks, toggling completion, filtering by status, deletion, localStorage persistence, and clean responsive UI using vanilla JS.

**Portuguese:**
> Crie um aplicativo simples de gerenciamento de tarefas em JavaScript com requisitos para adicionar tarefas, alternar conclusão, filtrar por status, exclusão, persistência localStorage e UI responsiva limpa usando JS puro.

Both prompts require identical functionality — only the language differs.

### Metrics Collected

- **Completion tokens**: Primary cost metric (what you pay for)
- **Character count**: Alternative length measure
- **Inference time**: Speed comparison
- **Statistical significance**: Paired t-tests to validate differences

## Output Format

The script outputs a JSON file with:

```json
{
  "timestamp": "2026-08-28T23:35:18",
  "model": "kat-coder-v2.5-dev-apex",
  "num_runs": 2,
  "summary_statistics": {
    "english_tokens_mean": 7420.5,
    "portuguese_tokens_mean": 7676.5,
    "token_percentage_diff": 3.45,
    "cost_ratio": 1.03
  },
  "significance_tests": {
    "tokens_significant": false
  },
  "all_runs": [...]
}
```

## Current Results

See the [`results/`](./results) folder for experimental data:

| File | Description | Key Finding |
|------|-------------|-------------|
| `validation-2026-08-28.json` | JavaScript task, 2 runs | +3.45% tokens (PT vs EN), not significant |
| `logic-puzzle-single-run.json` | Logic puzzle, 1 run | +154% tokens (PT vs EN) |

## Interpreting Results

### Token Difference

- **Positive %**: Portuguese generates MORE tokens → higher cost
- **Negative %**: Portuguese generates FEWER tokens → lower cost
- **Near 0%**: Comparable costs

### Statistical Significance

Results marked with "✓ SIGNIFICANT" show real differences, not random variation. With small sample sizes (N<30), tests may lack power to detect true effects.

### Cost Ratio

```
Cost Ratio = Total Portuguese Tokens / Total English Tokens
```

A ratio of 1.05 means Portuguese inference costs ~5% more on average.

## Requirements

- Python 3.8+
- No external dependencies (uses only stdlib: `json`, `urllib`, `argparse`)
- Network access to the target API

## Extending the Test

### Add New Task Types

Edit `PROMPT_ENGLISH` and `PROMPT_PORTUGUESE` in `inference_cost_test.py`:

```python
PROMPT_ENGLISH = """Your new task description here..."""

PROMPT_PORTUGUESE = """Tradução equivalente da tarefa..."""
```

### Batch Testing Multiple Models

```bash
for model in gpt-4 claude-3 opus; do
    python3 inference_cost_test.py \
        --model "$model" \
        --output "./results/${model}.json"
done
```

## License

MIT License — use freely for your own cost analysis.
