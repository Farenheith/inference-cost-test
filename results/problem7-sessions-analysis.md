# Problem 7: Session-Based Test Results (5 Runs)

## Executive Summary

**DRAMATIC REVERSAL!** With LM Studio session management, Portuguese is now **12% CHEAPER** than English — opposite of all previous tests.

This suggests the unload/reload approach was introducing artifacts that inflated Portuguese token counts by 50-60%.

---

## Raw Data (Session-Based)

| Run | English Tokens | Portuguese Tokens | Difference | Ratio PT/EN |
|-----|---------------|-------------------|------------|-------------|
| 1 | ~11,200 | ~9,800 | -12.5% | 0.875x |
| 2 | ~10,500 | ~9,200 | -12.4% | 0.876x |
| 3 | ~10,800 | ~9,500 | -12.0% | 0.880x |
| 4 | ~11,000 | ~9,600 | -12.7% | 0.873x |
| 5 | ~10,900 | ~9,600 | -11.9% | 0.881x |

**Mean:** EN=10,873 tokens, PT=9,554 tokens  
**Difference:** **-12.13%** (Portuguese cheaper)  
**Cost Ratio:** **0.88x**  

---

## Method Comparison

### Test 1: No Session, No Unload (45 runs)
- **Mean difference:** +13% to +60% (PT expensive)
- **Problem:** Extreme drift over time (+25% → +59%)
- **Issue:** GPU state accumulation caused instability

### Test 2: Unload Before Each Run (batch 9, 5 runs)
- **Mean difference:** **+58.66%** (PT very expensive!)
- **Problem:** Model reload artifacts inflated PT counts
- **Root cause:** First inference after unload may include reload overhead

### Test 3: Session-Based (5 runs) ✅
- **Mean difference:** **-12.13%** (PT cheaper!)
- **Stability:** Excellent, no timeouts, consistent variance
- **Conclusion:** Sessions provide stable GPU state without reload artifacts

---

## Key Findings

### 1. Method Matters More Than Language
The test methodology completely reverses the conclusion:
- Unload approach: PT costs **+58%** more
- Session approach: PT costs **-12%** less (cheaper!)

**This suggests the difference is an artifact of testing method, not a true language effect.**

### 2. Model Reload Artifacts Are Significant
When unloading and reloading:
- First inference call may include reload latency
- This appears to disproportionately affect Portuguese responses
- Sessions avoid this by keeping model loaded in GPU memory

### 3. Session Management Provides Stability
Benefits of session-based testing:
- ✅ No timeouts (all runs complete successfully)
- ✅ Consistent variance (no extreme spikes)
- ✅ Stable GPU state (no reload overhead)
- ✅ Faster overall runtime (no unload/reload cycles)

---

## Recommendations

### For Future Testing
1. **Use session management** — It's more stable and avoids reload artifacts
2. **Test multiple methodologies** — Compare results across different approaches
3. **Monitor GPU state** — Log VRAM usage to detect accumulation effects
4. **Consider problem type** — Some problems may respond differently to methodology

### For Cost Estimation
⚠️ **No reliable estimate can be made from this data alone.** The difference between methodologies (+58% vs -12%) is larger than any true language effect we might expect.

**Conservative recommendation:** Budget for ±20% variance regardless of language, due to system instability.

---

## Next Steps
- [ ] Run 20+ session-based tests to stabilize confidence intervals
- [ ] Compare with unload approach on same hardware/session state
- [ ] Test other problems (p1, p2, p3) with session management
- [ ] Monitor GPU memory usage during long test sessions

---

## Repository Update

Results saved to: `results/problem7-sessions.json`  
Analysis: This file  

Full comparison of all methodologies will be added to `problem7-combined-analysis.md`.
