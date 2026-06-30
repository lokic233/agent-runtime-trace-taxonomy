# Phase 7 — Retrospective Signal Screening (negative result)

## The one testable hypothesis (from Phase 6 moderator #5)
> Does `candidate_dup_lines_vs_prior` (the number of lines in the candidate segment that already appeared in prior observations) predict LINEDEDUP's cost-saving on that task?

## Result (auto-generated from blind views + sealed outcomes, n=48)
- **Spearman correlation: +0.026** (essentially zero — no predictive signal)
- Permuted negative control: +0.161 (higher than real → confirms no signal)
- Bin analysis: tasks with 2-10 dup lines show −42.9% (LINEDEDUP *hurt* — opposite to hypothesis)

## Verdict: NOT_SUPPORTED
The segment-level dup-lines feature (the ontology's "redundancy" axis computed at the selected decision point) does NOT predict LINEDEDUP's task-level cost effect. The permuted control out-performs the real feature → the signal is absent at this granularity.

## Why (interpretation consistent with Phases 3-5)
The decision points selected (largest observations) are mostly **active, non-redundant content** (100% liveness=active in the ontology). The genuinely-redundant segments that LINEDEDUP successfully prunes are **elsewhere in the trajectory** (smaller, repeated, later observations) — not at this decision point. A per-call segment-level test requires the Phase 8 MRT, which samples ALL eligible segments at each call, not just the largest.

## Comparison: annotated labels vs scalar features (from prior Phase 4 study)
| predictor | target | signal | status |
|-----------|--------|--------|--------|
| task-level dup_line_ratio (scalar) | LINEDEDUP task-cost-delta | Spearman +0.19, fails SHAM control | NOT_SUPPORTED (Phase 4 prior) |
| event-level dup_lines_vs_prior (annotation-aligned) | LINEDEDUP task-cost-delta | Spearman +0.03, permuted > real | NOT_SUPPORTED (this phase) |
| frontier-model blind pattern | task-cost-direction (adjudication) | 48% validated / 50% rejected | selection-biased (see above) |

**Verdict for BLIND_SEMANTIC_SIGNAL_VALUE: UNDERPOWERED** — the tested decision points don't contain the pruning signal (they're the wrong segments), so failure is a selection artifact, not a falsification of semantic signals in general. The MRT tests the right segments.
