# Boundary Cases (v0) — the hard distinguishing calls

These are the label pairs annotators will most likely confuse. Each gives the explicit
test that separates them. (Pilot confusion-matrix will tell us which still collapse.)

## 1. PATCH_CHURN vs FAILED_RECOVERY
- **CHURN:** repeated edits to the SAME region with **no test/new evidence between** them.
- **FAILED_RECOVERY:** edits ARE driven by **new failing evidence** (a failing test/error each
  round) but never converge.
- **Test:** Is there a TEST (or error observation) between consecutive edits? No → CHURN. Yes,
  with new failure each time → FAILED_RECOVERY.

## 2. BLIND_INFILE_NAVIGATION vs FILENAME_SEARCH_THRASH vs REDUNDANT_FILE_REREAD
- **BLIND_INFILE:** wrong LINE within the RIGHT, already-open file.
- **THRASH:** uncertainty about WHICH FILE — broad searches/dir-walks across many files.
- **REDUNDANT_REREAD:** the SAME content fetched again, unchanged.
- **Test:** Right file already open? → BLIND_INFILE. Hunting across files? → THRASH. Re-fetching
  identical content? → REREAD.

## 3. VERIFICATION_GAP vs ENVIRONMENT_BLOCKED
- **GAP:** the agent **never tried** to verify (no TEST after edit) despite a plausible oracle.
- **BLOCKED:** the agent **tried** but the environment prevented it (import/build/harness broken).
- **Test:** Is there an attempted-but-failed TEST/setup, or NO test attempt at all? Attempt blocked
  by env → BLOCKED (excuses the gap). No attempt → GAP.

## 4. PREEMPTIVE_HELPER_TOOL_BUILD vs PREMATURE_SCRATCH_REPRO vs HELPER_TOOL_FAILURE_LOOP
- **HELPER_BUILD:** building a generic editing/viewing UTILITY (edit_file.py) before working.
- **SCRATCH_REPRO:** building a reproduction of the BUG before localizing the source.
- **FAILURE_LOOP:** a helper (self-built or harness) breaks and is repeatedly repaired.
- **Test:** Generic tool vs bug-repro vs repairing-a-broken-tool.

## 5. STAGNATION vs BUDGET_EXHAUSTION_NONCONVERGENCE
- **STAGNATION (phase):** a streak of no-new-evidence actions (loop). Can occur mid-trace.
- **EXHAUSTION (full_trace):** the run TERMINATES on a limit (cost/steps/time) without a clean
  submit. Often caused BY stagnation but is a distinct terminal signal.
- **Test:** Looking at a mid-trace loop → STAGNATION. Looking at the termination_reason being a
  LIMIT → EXHAUSTION. They can co-occur (both labels valid; bottleneck = the dominant one).

## 6. DEPENDENCY_SETUP_DRIFT vs ENVIRONMENT_BLOCKED
- **DRIFT:** the agent CHANGES the dependency set / chases tool-not-found (agent-induced).
- **BLOCKED:** env broken from the start, independent of the agent's actions.
- **Test:** Did the agent's own install/build commands create the churn (DRIFT) or was it broken
  before the agent touched it (BLOCKED)?

## 7. EDIT_TOOL_MECHANICAL_FAILURE vs PATCH_CHURN
- **MECHANICAL:** the edit TOOL rejects a mismatched patch (whitespace/old_string), agent retries.
- **CHURN:** edits APPLY successfully but the agent keeps changing the same region.
- **Test:** Did the edit ERROR (mechanical) or APPLY-then-get-changed-again (churn)?

## 8. TEST_AS_EXPLORATION_MISROUTING vs healthy "run the failing test first"
- **MISROUTING (waste):** running broad suites to DISCOVER structure as a navigation tool.
- **HEALTHY (not waste):** running the SPECIFIC failing target test to read its traceback before fixing.
- **Test:** Targeted failing test (healthy) vs broad suite-as-explorer (misrouting). This boundary
  is fragile → label is PROVISIONAL_PILOT_ONLY.

## Primary-bottleneck rule
A trace may carry MULTIPLE waste labels but **at most one primary_bottleneck** — the label whose
elimination would most change the run. When two seem co-primary, prefer the EARLIER-phase cause
(localization waste upstream of edit waste upstream of verification waste), unless a later label
clearly dominates resource use.
