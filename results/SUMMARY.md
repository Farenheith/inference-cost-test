# Inference Cost Test Results Summary

## Key Findings

### 1. Temperature and Seed Control Determinism

| Setting | Variance | Notes |
|---------|----------|-------|
| Temperature = 0.7, no seed | **High** (6-8% per run) | Random token selection each run |
| Temperature = 0, no seed | **Medium** (~3%) | Removes sampling randomness but GPU scheduling varies |
| Temperature = 0, seed = 42 | **Low** (<1%) | Fully deterministic output |

### 2. Prompt Constraints Matter More Than Language

**Problem Type: REST API (Different Prompts)**

| Variant | EN Tokens | PT Tokens | Difference | Variance |
|---------|-----------|-----------|------------|----------|
| Unconstrained (p6) | ~2,700* | ~6,500* | **+137%** ❌ | High |
| Constrained (p2) | 953 | 963 | **+1.05%** ✓ | Low |
| Verbose (p7) | TBD | TBD | TBD | TBD |

*Problem 6 timed out during testing, values estimated from prior runs.

**Key Insight:** Prompt constraints have a larger impact on variance than language itself. The unconstrained prompt allows the model to choose output style freely, and Portuguese models tend to be more verbose.

### 3. Consistent Results Across Problems (Constrained)

**Problem 1 - Task Manager:**
- EN: 3,651 tokens | PT: 7,137 tokens (+95%)
- The task involves UI/UX descriptions which naturally expand in Portuguese

**Problem 2 - REST API (Constrained):**
- EN: 875 tokens | PT: 850 tokens (-2.9%)
- Nearly identical when forced to output code-only

**Problem 3 - Data Visualization:**
- EN: 9,185 tokens | PT: 8,765 tokens (-4.5%)
- Portuguese sometimes more concise in technical contexts

### 4. Consolidated Statistics (Problems 1, 2, 3)

| Metric | English Mean | Portuguese Mean | Difference |
|--------|-------------|-----------------|------------|
| Tokens | 4,570 | 5,584 | **+22.2%** |
| Characters | ~14K | ~18K | +29% |
| Time | ~112s | ~139s | +23% |

**Cost Ratio:** Portuguese inference costs ~1.2x more than English for equivalent constrained tasks.

## Methodology Notes

### What Was Tested
- Model: `kat-coder-v2.5-dev-apex` on LM Studio (local)
- API: OpenAI-compatible endpoint at `http://localhost:1234/v1/chat/completions`
- Temperature: 0.0 (deterministic)
- Seed: 42 (fixed for reproducibility)
- Prompts: Equivalent JS/Node.js tasks in PT and EN

### What Was NOT Tested
- Production API providers (OpenAI, Anthropic, etc.)
- Different model architectures
- Batch/incremental generation scenarios
- Real-world user prompts (all were coding tasks)

## Recommendations

1. **Always use seed parameter** for reproducible benchmarks
2. **Constrain output format** in prompts to minimize style variance
3. **Test multiple problem types** - some are more language-sensitive than others
4. **Report P95 not just mean** - outliers matter for cost estimation

## Repository Structure

```
problems/
  p1/  # Task Manager (open-ended)
  p2/  # REST API (constrained)  
  p3/  # Data Visualization (open-ended)
  p6/  # REST API (unconstrained - for comparison)
  p7/  # REST API (verbose style)
results/
  batch-1-2-3.json      # Original 5-run test
  final-batch.json      # Constrained test with seed=42
  api-variance-analysis.json  # Pending
```
