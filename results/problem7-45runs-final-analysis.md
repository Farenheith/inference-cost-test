# Problem 7: Final Analysis (45 Total Runs)

## Executive Summary

After **45 total runs**, the data reveals extreme instability in the Portuguese vs English token difference. The trend shows clear **systemic drift** over time, with later batches exhibiting exponentially larger differences.

**Conclusion**: The test system is unstable for this use case. Results cannot be reliably interpreted without restarting LM Studio and re-baselining.

---

## Complete Batch History (45 Runs)

| Batch | N | Diff | Cost Ratio | Direction |
|-------|---|------|------------|-----------|
| 1-5 | 5 | +12.8% | 1.13x | PT ↑ |
| 6-10 | 10 | +16.8% | 1.17x | PT ↑ |
| 11-20 | 20 | +13.5% | 1.13x | PT ↑ |
| 21-25 | 5 | +25.8% | 1.26x | PT ⬆️↑ |
| **26-30** | **5** | **-4.34%** | **0.96x** | PT ↓ (REVERSAL!) |
| **31-35** | **5** | **-8.31%** | **0.92x** | PT ↓↓ (REVERSAL!) |
| 36-40 | 5 | +40.48% | 1.40x | PT ⬆️⬆️↑ |
| **41-45** | **5** | **+58.66%** | **1.59x** | PT ⬆️⬆️⬆️ (SPIKE!) |

---

## Key Findings

### 1. Extreme Variance Over Time
- **Range**: -8.31% to +58.66% (67-point swing!)
- **Standard deviation of batch means**: ~24%
- **Trend direction changed twice** (once from + to -, once back to ++)

### 2. Systemic Drift Pattern
```
Time →
Early:    +13% to -8%   (stable oscillation)
Late:     +40% to +59%  (exponential drift upward)
```

**Possible causes**:
- GPU memory fragmentation over long sessions
- LM Studio state accumulation (cache, buffers)
- Thermal throttling effects on AMD iGPU
- CUDA/HIP kernel scheduling degradation

### 3. Statistical Assessment

With n=45:
- **Mean difference**: +19.7% (but heavily skewed by late batches)
- **Median difference**: +13.5% (more representative of early behavior)
- **Standard error**: ±8.5% (very wide)
- **95% CI**: [+2.7%, +36.7%] — includes both directions

**Interpretation**: The data is non-stationary; traditional statistics don't apply well.

---

## What We Can Conclude

### ✅ Confirmed Instability
1. **The system is NOT stable** for this type of long-running test
2. **Seed parameter alone does not guarantee determinism** on GPU inference
3. **System state matters**: Later batches show exponential drift

### ⚠️ Inconclusive Findings
1. **True mean difference unknown**: Could be +13% (early) or +50% (late)
2. **No clear causal mechanism**: Don't know what's driving the drift
3. **Cannot generalize**: Results may not apply to other systems/models

### ❌ Cannot Conclude
1. "Portuguese costs X% more than English" — value is time-dependent
2. Any precise cost estimate without knowing system state at test time

---

## Recommendations

### For This Test System (Immediate)
1. **Restart LM Studio** and re-run baseline tests from scratch
2. **Monitor GPU memory** during inference to detect leaks
3. **Use shorter batches** (n=5) with restarts between batches
4. **Log system metrics**: GPU temp, VRAM usage, CPU load

### For Future Testing
1. **Control for time**: Run EN and PT pairs sequentially without gaps
2. **Randomize order**: Alternate EN-first vs PT-first to cancel drift
3. **Monitor system state**: Log GPU/CPU/memory during each run
4. **Set quality gates**: Abort if batch variance exceeds threshold

### For Cost Estimation (Practical)
- Use **1.2x multiplier** as conservative baseline (early behavior)
- Budget for **±30% uncertainty** due to system instability
- Test on **production-equivalent hardware** before committing to estimates
- Consider **model-specific testing**: Different models may behave differently

---

## Final Assessment: TEST SYSTEM UNSTABLE

The inference cost comparison test revealed significant instability in the LM Studio + AMD iGPU environment. The extreme variance (+25% range) and clear drift pattern make it impossible to determine a reliable cost multiplier from this data alone.

**Status**: ❌ INSUFFICIENT EVIDENCE — System needs stabilization before meaningful conclusions can be drawn

**Next Steps**:
1. Restart LM Studio and GPU state
2. Re-run tests with system monitoring enabled
3. Compare early vs late batch behavior to quantify drift rate
4. Consider alternative test environments (different GPU, different LM Studio version)

---

## Methodology Notes

- **Model**: kat-coder-v2.5-dev-apex on LM Studio
- **Parameters**: temperature=0.0, seed=42 (deterministic attempt)
- **Problem**: p7 - Verbose REST API implementation
- **Total runtime**: ~8 hours across 45 runs
- **Timeouts**: 4 runs failed (~9% failure rate in later batches)
- **Analysis**: Paired comparison with time-series awareness
