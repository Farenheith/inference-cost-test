# Problem 7: 5-Round Test Results (Verbose REST API)

## Raw Data

| Run | English Tokens | Portuguese Tokens | Difference | Ratio PT/EN |
|-----|---------------|-------------------|------------|-------------|
| 1 | 7,377 | 10,364 | +40.5% | 1.40x |
| 2 | 10,730 | 10,304 | -4.0% | 0.96x |
| 3 | 13,248 | 10,954 | -17.3% | 0.83x |
| 4 | 11,213 | 12,779 | +14.0% | 1.14x |
| 5 | 7,368 | 11,907 | +61.6% | 1.62x |

## Statistical Summary

| Metric | English | Portuguese | Difference |
|--------|---------|------------|------------|
| **Mean** | 9,987 | 11,262 | **+12.76%** |
| **Min** | 7,368 | 10,304 | - |
| **Max** | 13,248 | 12,779 | - |
| **Std Dev** | 2,254 | 941 | - |
| **P95** | 12,841 | 12,605 | - |
| **Cost Ratio** | - | - | **1.13x** |

## Variance Analysis

### English Token Range
- Min: 7,368 (Run 5)
- Max: 13,248 (Run 3)
- **Range: 5,880 tokens (80% variation)**

### Portuguese Token Range  
- Min: 10,304 (Run 2)
- Max: 12,779 (Run 4)
- **Range: 2,475 tokens (24% variation)**

**Key Observation:** English shows significantly higher variance than Portuguese in this problem type.

## What This Data Shows

### Confirmed:
1. **Mean difference is +12.76%** - Portuguese generates more tokens on average
2. **High variance exists** - Even with seed=42, runs vary by up to 80% for English
3. **No single run is representative** - Individual data points are unreliable

### NOT Confirmed (Insufficient Evidence):
1. Whether the +12.76% difference is statistically significant (need more runs)
2. Whether Portuguese is inherently less efficient
3. Whether the variance difference (EN 80% vs PT 24%) is real or noise

## Comparison with Previous Runs

| Dataset | N | EN Mean | PT Mean | Diff | Conclusion |
|---------|---|---------|---------|------|------------|
| Problem 7, Run 1-2 only | 2 | 9,792 | 9,061 | -7.5% | ❌ Inconclusive |
| **Problem 7, Runs 1-5** | **5** | **9,987** | **11,262** | **+12.8%** | ⚠️ Trend, not proof |

The direction changed from -7.5% to +12.8% with more data, demonstrating why n=2 is insufficient.

## Statistical Note

With n=5:
- Standard error of mean: ~1,008 tokens (English), ~421 tokens (Portuguese)
- 95% CI for EN mean: [7,696, 12,278]
- 95% CI for PT mean: [10,035, 12,489]

**The confidence intervals overlap significantly**, meaning we cannot rule out that the true means are equal.

## Recommendation

To draw valid conclusions:
1. **Run at least 30 iterations** to stabilize the mean
2. **Report full distribution** (min, max, percentiles, std dev)
3. **Use paired t-tests** to validate significance
4. **Avoid single-run comparisons** - they're meaningless

## Current State: UNANSWERED

The question "Is Portuguese more/less efficient than English?" remains **UNANSWERED**. We have a trend (+12.8%) but insufficient evidence to confirm it's real rather than noise.
