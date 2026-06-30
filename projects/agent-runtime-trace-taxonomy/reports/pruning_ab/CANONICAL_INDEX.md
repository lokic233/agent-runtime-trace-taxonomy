# Canonical Index — Context-Pruning + Causality Study

Single source of truth. Reports not listed as CURRENT are superseded (kept for provenance).

## ⭐ START HERE
- **TRACE_CAUSALITY_FINAL.md** — the causal study + 8-part verdict (CURRENT, definitive)
- **COMPREHENSIVE_TABLE.md** — all methods × all metrics (CURRENT)
- **CAUSAL_DATA_AUDIT.md** — data freeze + contradiction reconciliation (CURRENT)

## Causal study (CURRENT — this mission)
| report | content |
|--------|---------|
| TRACE_CAUSALITY_FINAL.md | 8-verdict synthesis |
| CAUSAL_DATA_AUDIT.md | Phase 0: freeze, manifest, reconcile, RETRACT "A/A noise" framing |
| CACHE_TAX_CAUSALITY.md | Phase 2A: cache tax SUPPORTED (SHAM-controlled) |
| INTELLIGENCE_TAX_CAUSALITY.md | Phase 2B: intelligence tax SUPPORTED (dose-controlled) |
| TRACE_FEATURE_DICTIONARY.md | Phase 3: feature lineage + deployability tiers |
| HETEROGENEOUS_TREATMENT_EFFECTS.md | Phase 4: HTE weak, negative control fails |
| ORACLE_GAP.md | Phase 5: +27% oracle, but controller NOT_SUPPORTED |
| CONTROLLER_PREREGISTRATION.md | Phase 6: frozen prereg, untouched PENDING |
| CROSS_MODEL_SMOKE_TEST.md | Phase 7: cross-model EXPLORATORY |
| ROBUSTNESS_FALSIFICATION.md | Phase 4D/F: leave-top-k, SHAM cost control, repo-cluster bootstrap (saving NOT robust) |
| CAUSAL_ESTIMANDS.md | Phase 1: formal ATE/CATE/objective definitions |
| BUDGET_CONTROLLER_DEV.md | Phase 5: controller construction (NOT_SUPPORTED) |

## Empirical study (CURRENT facts, saving-number caveats apply)
| report | status |
|--------|--------|
| COMPREHENSIVE_TABLE.md | CURRENT — all 15 methods, all metrics |
| PARETO_FRONTIER_v3_TASK_LEVEL.md | CURRENT — task-level cost framing |
| EXPERIMENT4_FRONTIER.md | CURRENT — line-level/retrieval methods |
| HYBRID1_FREEZE.md | CURRENT — frozen method hashes |

## SUPERSEDED (provenance only — disputed numbers corrected in CAUSAL_DATA_AUDIT)
| report | why superseded |
|--------|---------------|
| PARETO_FRONTIER_v1.md | submission-proxy (pre-grading) |
| PARETO_FRONTIER_v2_VERIFIED.md | per-call saving (cache-naive) |
| REGRESSION_BUDGET_PARETO.md | used +24% partial + "noise" framing |
| REGRESSION_BUDGET_FINAL.md | "0 real regression" language RETRACTED |
| FINAL_VERDICT.md | pre-causal; mechanism claims now in causal reports |
| AA_NOISE_FLOOR.md | A/A flips reframed as "unresolved attribution" not "noise" |

## Key corrected facts (authoritative)
- Canonical C0 baseline: stable tagged C0 = **46/50** resolved (not 48 — that was a different run)
- LINEDEDUP: **+6.3% bill-weighted eff-cost / −1.1% task-weighted median**, **2 regressions** (unresolved attribution), drift-free
- GENTLE6K: **+10.1% bill-weighted** (best static), 1 regression (unresolved)
- Best deployable trace controller: **+9.3% < +10.1% best-static → controller NOT justified**
- ⚠️ Saving NOT ROBUST: leave-top-3-out flips LINEDEDUP to −4.0%, GENTLE6K to −7.1%; repo-cluster CI [−9.9%,+18%]; SHAM cost control fails (dup_ratio↔SHAM spearman −0.76 = predicts noise)
- Mechanisms: cache tax + intelligence tax both **causally SUPPORTED**
