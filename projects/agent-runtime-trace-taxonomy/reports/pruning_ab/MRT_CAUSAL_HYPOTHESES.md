# Phase 3 — Three Causal Moderator Hypotheses (FROZEN before outcome collection)

Preregistered. These are the three primary tests the MRT pilot will evaluate. Frozen before any annotation results or randomized outcomes are observed.

## Hypothesis A — Safe exact redundancy removal
**Pattern:** `A_exact_redundancy` stratum (>40% lines are exact duplicates of prior content, ≥5 dup lines).
**Action:** LINE_DEDUP vs NO_OP
**Expected:** LINE_DEDUP reduces local effective cost; no increase in rereads/repeated commands; no quality degradation.
**Falsification:** effect is NOT larger in A-stratum events than in E-stratum (active) events; or reread rate rises.
**Eligibility:** event in stratum A with ≥2000 chars segment.
**Primary outcome:** incremental eff-cost over H=1 call.
**Secondary:** reread of removed content, repeated file access, task resolution.

## Hypothesis B — Safe compression of large recoverable output
**Pattern:** `C_large_output` stratum (>4000 chars, tool output).
**Action:** GENTLE_CAP vs NO_OP
**Expected:** GENTLE_CAP reduces local cost; limited reread; benefit larger when remaining horizon is long.
**Falsification:** reread rate is high (content needed) OR cost reduction < cap overhead.
**Eligibility:** event in stratum C with ≥4000 chars.
**Primary outcome:** incremental eff-cost over H=1 call.
**Secondary:** rereads, output growth, test-state regression.

## Hypothesis C — Unsafe removal of active evidence (the harm hypothesis)
**Pattern:** `E_active_dependency` stratum (<10% dup, >1000 chars novel content).
**Action:** LINE_DEDUP or GENTLE_CAP vs NO_OP
**Expected:** removal INCREASES reread/repeated commands, trajectory drift; little or negative cost benefit.
**Falsification:** cost savings materialize without increased drift on active content.
**Eligibility:** event in stratum E with ≥2000 chars.
**Primary outcome:** reread/repeated-command rate at H=3.
**Secondary:** output growth, trajectory divergence, quality regression.

## The key causal test (per mission)
> Does the annotated pattern modify the causal effect of the action?
`ATE(LINE_DEDUP | A_redundancy) vs ATE(LINE_DEDUP | E_active)` — the interaction is the evidence. If LINE_DEDUP helps on redundant content but harms on active content, the pattern is causally actionable.

## Statistical plan
- 50/50 randomization within each eligible stratum (single intervention per task).
- Bootstrap CIs, repo-clustered bootstrap, leave-top-k.
- Success = effect estimate + interaction both have expected sign with CI excluding zero.
