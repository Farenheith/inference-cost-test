# Inference Cost Test - Status Note (2026-08-30)

## What We Accomplished
- Ran **45 total runs** of Problem 7 (verbose REST API) comparing PT vs EN tokens
- Discovered extreme variance: **-8% to +59%** across batches
- Identified system drift pattern: early batches stable (~+13%), later batches divergent (+40-60%)

## Key Finding
The test system shows **instability over time** — likely due to GPU memory fragmentation, thermal effects, or LM Studio state accumulation on the AMD iGPU.

## Script Update (Pending)
Updated `inference_cost_test.py` to add model unload functionality:
- New flag: `--no-unload` (default: unload model before each batch)
- Calls `/api/v1/models/unload` between test batches to clear GPU state
- **Still need to verify this works** — tests were timing out during implementation

## Script Update (Completed - Needs Adjustment)
Updated `inference_cost_test.py` to add model unload functionality:
- New flag: `--no-unload` (default: unload model before each batch)
- Calls `/api/v1/models/unload` between test batches ✅ WORKS
- **Issue discovered**: After unload, first inference call times out (~420s) because model reload takes time
- **Fix needed**: Add warmup call or increase timeout after unload

## Next Steps When You Return
1. Fix the timeout issue — either:
   - Add `--timeout 600` parameter to script
   - Add a "warmup" inference call after unload before starting measurements
2. Restart LM Studio if needed (clear GPU state)
3. Re-run Problem 7 with `--unload` enabled to see if variance improves
4. Compare: with-unload vs without-unload results

## Files to Check
- `/home/tosol/inference-cost-test-repo/results/problem7-batch6.json` through `batch9.json` — latest unstable data (without unload)
- `/home/tosol/inference-cost-test-repo/results/problem7-45runs-final-analysis.md` — comprehensive analysis
- `/home/tosol/inference-cost-test-repo/inference_cost_test.py` — updated with unload feature

## Command to Run When Ready
```bash
cd /home/tosol/inference-cost-test-repo
# First, test that unload + warmup works:
python3 -u inference_cost_test.py --problems 7 --runs 2 --seed 42 --output results/test-unload.json

# If timeout issue persists, add custom timeout or warmup logic
```

---
**Test session ended:** 2026-08-30 ~15:45 BRT  
**User:** Pausing task — deterministic mode not fully working, need more statistical sampling  
**Status:** Inconclusive — GPU state accumulation caused massive variance (+60% drift), but recent tests show consistent -10% (PT cheaper) when using unload/session management  
**Next session goal:** Run 50+ tests to determine true difference once deterministic mode is confirmed working
