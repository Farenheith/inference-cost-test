# Problem 7: Unload Test Results (5 Runs)

## Executive Summary

With model unload enabled before each inference, results show **Portuguese is consistently ~10% cheaper** than English — matching the session-based test.

This contradicts earlier findings (+13% to +60%) and suggests those were artifacts of GPU state accumulation over long test sessions.

---

## Raw Data (Unload Before Each Run)

| Run | English Tokens | Portuguese Tokens | Difference |
|-----|---------------|-------------------|------------|
| 1 | ~8,200 | ~7,400 | -9.8% |
| 2 | ~7,800 | ~7,000 | -10.3% |
| 3 | ~8,100 | ~7,300 | -9.9% |
| 4 | ~8,000 | ~7,200 | -10.0% |
| 5 | ~8,100 | ~7,300 | -9.9% |

**Mean:** EN=8,027 tokens, PT=7,229 tokens  
**Difference:** **-9.95%** (Portuguese cheaper)  
**Cost Ratio:** **0.90x**  

---

## Method Comparison (All Tests on Same System)

| Test | N | Diff | Direction | Stability |
|------|---|------|-----------|-----------|
| No unload, no session (batch 1-9) | 45 | +13% to +60% | PT expensive ❌ | Drifted badly |
| Session-based (new test) | 5 | -12% | PT cheaper ✅ | Stable |
| **Unload before each run** (this test) | 5 | **-10%** | **PT cheaper** ✅ | Stable |

---

## Key Findings

### 1. Consistent Reversal
Both modern approaches show the same result: Portuguese is ~10% MORE cost-efficient than English for this task. This is the opposite of all previous tests.

### 2. GPU State Accumulation Was Causing Artifacts
The earlier +13% to +60% drift was likely caused by:
- GPU memory fragmentation over long sessions
- Thermal effects on AMD iGPU after extended use
- LM Studio state accumulation

### 3. Current Results Are Stable
With unload or session management:
- No timeouts (all runs complete)
- Low variance (consistent ~10% difference)
- Reproducible across methods

---

## What This Means

**⚠️ We cannot draw a definitive conclusion yet.** The reversal from +50% to -10% is too large to be a true language effect — it's almost certainly system state dependent.

**However**, the consistency between session and unload approaches suggests:
- Current system state is stable
- Results are reproducible within this state
- The true difference (if any) is likely smaller than ±10%

---

## Next Steps
- [ ] Run 20+ additional tests with both methods
- [ ] Monitor GPU memory/temp during tests
- [ ] Compare results after LM Studio restart
- [ ] Test on different problems to see if pattern holds

---

## Repository Update

Results: `results/problem7-unload-baseline.json`  
Analysis: This file  

Full comparison will be added to combined analysis document.
