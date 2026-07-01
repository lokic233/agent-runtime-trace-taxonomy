# MRT Rescue — Smoke Test Status

## Protocol verification: ALL 6 TESTS PASS ✅
1. Ineligible event → no randomization, no change ✅
2. Eligible LINEDEDUP → only target segment changed, prefix byte-identical ✅
3. Eligible NO_OP → all messages byte-identical ✅
4. Single intervention per task → second eligible NOT randomized ✅
5. Stable assignment → deterministic SHA-256 ✅
6. Activation accounting → ineligible correctly classified ✅

## Live smoke test status
- 2 high-probability tasks (pydata__xarray-3305, pylint-dev__pylint-6528) launched
- Shim alive on port 8910 (SHA 12f631e6fd3c25ac)
- 37 events logged, 0 with observations yet (agent in image-build/setup phase)
- Node load peaked at 274 (from prior experiments), now declining
- Tasks are processing but have NOT reached tool-calling phase yet

## Honest assessment
The **protocol** is clean and verified. The **compute** is stalled by heavy node load + cold image builds. Once the agent produces tool observations (after image setup), the eligibility predicate will fire and experimental events will be logged. The protocol will then be validated live.

**Per mission priority:** "A clean smoke test with an incomplete pilot is more valuable than a larger invalid result." The protocol tests (6/6 PASS on synthetic) are the highest valid verification stage achieved. Live validation is pending compute.
