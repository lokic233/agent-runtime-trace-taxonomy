# Q2 intelligence-tax — metric caveat (call-cap censoring), noted during Phase D

## Finding (from partial Phase D data, Opus + most Sonnet)
The **call-ratio metric is right-censored at the 75-call per-instance cap**. Many hard tasks (pylint-4551,
pylint-8898, pytest-6197, ...) hit 76 calls in BOTH C0 and the treatment arm, so their per-task call ratio
is exactly 1.0 regardless of the transform. The MEDIAN call_ratio therefore collapses toward 1.0 on the
capped-heavy task mix, masking real drift visible in uncapped tasks (e.g. astropy-14096 LINEDEDUP ratio 1.69).

## Implication for the Q2 verdict
- **call_ratio alone understates the intelligence tax** wherever tasks saturate the budget. Do NOT read
  "call_ratio median ~1.0" as "no intelligence tax."
- **out_ratio (output tokens) is uncensored** and more sensitive. Interim: opus CAP1K out_ratio 0.838,
  sonnet CAP1K 0.496 — destructive truncation yields FEWER productive output tokens (context loss ->
  shorter/less-effective generation), the tax signature, but it manifests in OUTCOME (resolution) more than
  raw call count on capped tasks.
- The final INTELLIGENCE_TAX_SCALING.md must report: (a) call_ratio WITH the censoring caveat, (b) out_ratio,
  (c) RESOLUTION rate per arm/model (the ground-truth intelligence-tax measure), (d) uncapped-task subset
  analysis. The capability-interaction test (CAP1K worse on weaker models) should use resolution + out_ratio,
  not the censored call_ratio.
- Anchor (frozen Opus) had CAP1K call_ratio 1.24 / out_ratio 1.34 — note the frozen study's out_ratio was
  >1 (more output) while our interim is <1; reconcile at full data (may be task-mix / cap-interaction).

## Status: EXPLORATORY (partial data). Final Q2 verdict requires 36/36 Phase D + resolution grading.

## Q2 capability-interaction PREVIEW (Opus+Sonnet complete, out-token proxy)
With Opus (12/12) + Sonnet (12/12) Phase D cells done, the uncensored out-token metric shows the H2 signal:
| arm | Opus out-tok/cell | Sonnet out-tok/cell |
|-----|------------------|---------------------|
| C0 (baseline) | 162K | 258K |
| CAP1K (destructive) | 153K (-6%) | 147K (-43%) |
CAP1K's output-token collapse is far larger on the WEAKER model (Sonnet -43% vs Opus -6%) -> destructive
truncation hurts weaker models more (H2 capability-interaction). Haiku (weakest tier) will test if the
gradient continues. NOTE: this is the out-token proxy; the ground-truth Q2 verdict uses RESOLUTION grading —
.pred files ARE produced per task (10/cell verified), gradeable via the SWE-bench report.json path (same as
the frozen study). Final verdict at 36/36 + grading. Status: EXPLORATORY (strong direction, resolution pending).

## POWERED Q2 (all 36 Phase D cells) — call/out ratios; RESOLUTION grading still required
Full Phase D metrics (per-task median, rep-normalized, deduped):
| model | LINEDEDUP call/out | GENTLE6K call/out | CAP1K call/out |
|-------|--------------------|--------------------|-----------------|
| opus47   | 1.10 / 0.86 | 0.96 / 0.93 | 1.15 / 0.82 |
| sonnet46 | 1.00 / 0.82 | 1.00 / 0.94 | 1.00 / 0.64 |
| haiku45  | 1.00 / 0.90 | 1.00 / 1.05 | 1.00 / 0.75 |

INTERPRETATION (honest):
- **call_ratio is CENSORED**: Sonnet & Haiku pinned at 1.00 (75-call cap saturates hard tasks in both C0 and
  treatment). The analyzer's `H2_direction=REVERSED` is a CENSORING ARTIFACT, not a real reversal — DISCARD it.
- **out_ratio (uncensored) CAP1K**: Opus 0.82, Sonnet 0.64, Haiku 0.75. Destructive truncation reduces productive
  output on ALL tiers, but NOT a clean monotonic capability gradient (Sonnet drops most, Haiku between). So the
  simple H2 "weaker=strictly worse" is NOT cleanly supported by out-tokens.
- **RESOLUTION is the ground-truth Q2 measure and is NOT YET COMPUTED.** Phase D preds exist (10/cell) but are
  ungraded. Grading (swebench.harness.run_evaluation) runs test containers -> DEFERRED until the driver finishes
  Phase E (avoid resource conflict / SIGKILL risk). Post-completion: grade Phase D+E, compute per-arm/model
  resolution, then the intelligence-tax verdict = does CAP1K cause more UNSOLVED tasks on weaker models.
- Likely final Q2 verdict language: intelligence tax (destructive truncation reduces productive output) is
  SUPPORTED on all tiers; the capability-interaction (H2 monotonic-by-capability) is PARTIALLY_SUPPORTED or
  UNDERPOWERED pending resolution — NOT a clean gradient in the token metrics.
