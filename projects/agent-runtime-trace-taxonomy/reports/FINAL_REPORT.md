# FINAL REPORT — SWE-Agent Trace Waste Taxonomy & LoRA-Ready Controller Dataset

**Project:** agent-runtime-trace-taxonomy · **Engine:** research-os (CLAIM-0001 / EXP-0001, CPU-only)
**Repo:** lokic233/agent-runtime-trace-taxonomy · **Date:** 2026-06-28

## Verdicts (up front)
- **TAXONOMY_VERDICT: READY_WITH_LIMITATIONS**
- **SEMANTIC_ANNOTATION_VERDICT: PARTIAL** (pilot complete; full Stage-B over all roots not yet run)
- **LORA_SEMANTIC_DATA_VERDICT: PARTIAL** (schema + split + scaffold ready; full export pends full annotation)
- **PARETO_POLICY_DATA_VERDICT: NOT_EMPIRICALLY_GROUNDED** (no paired config outcomes exist — by design)

---

## 1. Repositories & source files read
- **research-os** (engine): lifecycle CLI (`ros init/seed/exp/report/commit`), config schema. Engine NOT modified.
- **TokenSaver** (Peterren/tokensaver @ 78ab263): README, docs/metrics.md, model.py (RooflineVector),
  effectiveness/{scorecard,tools,memory,text}.py, analyze/waste.py. → context/tokensaver_contract.md.
  Key inheritance: the **honest-null rule** (missing = null + content_available=false, never fabricated 0).

## 2. Trace sources available (validated on disk)
| alias | model (unblinded HERE only) | resolve | trajs | layout | role |
|-------|------|--------:|------:|--------|------|
| solver_A | claude-opus-4-7 (live run) | ungraded | ~466→500 | nested_traj | dev |
| solver_B | live-SWE-agent + opus-4.5 | 79.2% | 500 | mini_swe_agent | dev (SOTA ceiling) |
| solver_C | SWE-agent + claude-3.5-sonnet | 33.6% | 500 | flat_traj | dev (mid/weak) |
| solver_E | SWE-agent-LM-32B (Qwen2.5) | 40.2% | 500 | flat_traj | **HELD OUT** |
| solver_F | claude-opus-4-6 (live run) | ungraded | ~40 | nested_traj | capability audit |
| solver_D | Qwen2.5-Code-Agent-8B | — | **0 (absent)** | — | dev slot EMPTY |
Normalization coverage: **1500/1500 reference traces parse, 0 errors, 0 warnings** (4 on-disk layouts).

## 3. Models used for taxonomy discovery
solver_A (opus-4.7), solver_B (opus-4.5), solver_C (sonnet-3.5) — the available dev models.

## 4. Models held out
solver_E (Qwen2.5-32B) — firewalled: never shaped the taxonomy, excluded from LoRA training, reserved
as a model-transfer eval set. (See the policy/data mismatch in §18.)

## 5. Sampling method
Diversity-maximizing stratified sampling (seeded, reproducible). Bootstrap = 60 traces for open coding;
pilot = 114 FRESH traces (0 overlap) for closed-label agreement. Strata: outcome × token-tertile ×
length-tertile × behavior-mix (search/edit/test) × error-hi/lo × stagnation. Outcome used for BALANCE
only, firewalled from coders.

## 6. Final Workload taxonomy (v1)
6 L1 primary (LOCALIZATION / PATCH_REASONING / VERIFICATION / CONTEXT / ENVIRONMENT _DOMINANT, MIXED_END_TO_END
= last-resort) + 6 L2 axes (localization, patch-scope, verification, context, failure-observability, state),
21 attributes. Task-level; cross-model-stable by design.

## 7. Final Waste taxonomy (v1) — 6 L1 / 16 L2
- **CONTEXT_MEMORY:** REDUNDANT_FILE_REREAD, CONTEXT_BLOAT
- **SEARCH_LOCALIZATION:** FILENAME_SEARCH_THRASH, SEARCH_WITHOUT_NEW_EVIDENCE
  (BLIND_INFILE_NAVIGATION moved to online-control annex — see §8)
- **EDIT_PATCH:** PATCH_CHURN, PREMATURE_SCRATCH_REPRO, EDIT_TOOL_MECHANICAL_FAILURE
- **VERIFICATION:** VERIFICATION_GAP, REDUNDANT_TEST
- **CONTROL_RECOVERY:** STAGNATION, FAILED_RECOVERY, BUDGET_EXHAUSTION_NONCONVERGENCE
- **ENVIRONMENT_TOOLING:** PREEMPTIVE_HELPER_TOOL_BUILD (harness-conditioned), HELPER_TOOL_FAILURE_LOOP,
  DEPENDENCY_SETUP_DRIFT, ENVIRONMENT_BLOCKED
Each label: definition, observable-unit, indicators, required-evidence, exclusions, counterexamples,
neighbors, distinguishing-rule, severity rubric, candidate interventions, metric signals, observability.

## 8. Labels merged / rejected / left ambiguous
- **REJECTED (outcome-in-disguise):** FAILED_TO_SOLVE, BAD_REASONING, LOW_QUALITY_PATCH, NO_TESTS_MEANS_FAILURE,
  MANY_SEARCHES_MEANS_WASTE.
- **QUARANTINED (unobservable):** TOKENS_PER_EVENT, HIDDEN_REASONING, FINAL_PATCH_CORRECTNESS, PER_CALL_WALLCLOCK,
  LOW_RESULT_UTILIZATION; memory-retrieval L2 dropped (no memory layer).
- **MERGED:** BROAD_FILE_DUMP+OUTPUT_TRUNCATION→CONTEXT_BLOAT; ENV_DEPENDENCY_DRIFT+TOOL_NOT_FOUND→DEPENDENCY_SETUP_DRIFT;
  EXACT_MATCH_REPLACE+HARNESS_SYNTAX→EDIT_TOOL_MECHANICAL_FAILURE; etc.
- **DROPPED at v1 (pilot):** OVER_BROAD_EDIT, TEST_AS_EXPLORATION_MISROUTING (weak observability / confused).
- **MOVED to online-control annex:** BLIND_INFILE_NAVIGATION (unanimous in OPEN coding, NEVER selected by
  closed-label annotators on abbreviated full-trace transcripts → valid for prefix/online control only).

## 9. Pilot agreement statistics (round-1 v0 → round-2 v1)
| metric | R1 | R2 | gate |
|--------|---:|---:|------|
| Waste L1 raw | 0.50 | **0.70** | ≥0.70 ✅ |
| Waste L1 α | 0.34 | **0.52** | ≥0.70 |
| Primary L2 (bottleneck) | 0.39 | **0.586** | ≥0.60 |
| Workload L1 α | 0.21 | 0.15 | ≥0.70 (WEAK AXIS) |
| Multi-label Jaccard | 0.45 | 0.33 | ≥0.65 |
| OTHER/UNKNOWN | 0.0 | 0.0 | ≤0.05 ✅ |
Two revision rounds used (Section-11 max). Core waste metrics improved materially; workload L1 + Jaccard
remain weak (documented limitations, not iteration failures).

## 10. Coverage & OTHER rates
Taxonomy coverage 0.74-0.90 (partial-data; ann3 incomplete). OTHER/UNKNOWN = 0.0%. All 16 v1 labels used
(0 never-selected after revision).

## 11. Annotation volume by model & task
Bootstrap 60 (open coding, 3 coders). Pilot 114 traces × up to 3 annotators × 2 rounds. Raw votes preserved
in annotations/raw_votes/pilot_round{1,2}/. Full Stage-B over all roots: NOT yet run.

## 12. Per-model waste distributions
mappings/per_model_summary.json (pilot smoke test). Reports raw + matched-task set (matched-task overlap
was small in the diversity-stratified pilot; full annotation will enrich it). Deterministic separation
already visible: solver_C (weak) had ~13% tool-error rate vs solver_B (strong) ~1%.

## 13. Per-task L1/L2 mapping
mappings/per_task_l1_l2.jsonl — 108 tasks. workload primary_l1 + cross_model_stability + per-solver waste +
shared-vs-solver-specific labels. (Most pilot tasks had 1 supporting solver → cross_model_stability mostly
INSUFFICIENT; full annotation across shared task IDs fixes this.)

## 14. Matched-task cross-model differences
Smoke-test only (matched-task set = 1 in pilot). The machinery (aggregate_per_model matched-task set +
raw-vs-adjusted reporting) is built and validated; meaningful matched-task analysis requires the full
Stage-B annotation where solvers share task IDs.

## 15. Dataset split & leakage audit
export split is repo-disjoint (train/val/test), held-out solver_E excluded from train, dedicated model- &
repo-transfer test splits. test_split_leakage.py (5/5) + reports/red_team_audit.md (checks 3,4) confirm no
task/repo/prefix leakage. dataset_leakage_audit covered by the test + red-team.

## 16. Label-source classification
- **Deterministic** (reproducible, no model): all of §5 in normalize/extract — tool/file/patch/test/stagnation
  metrics + roofline from model_stats.
- **Semantic** (model judgment, evidence-cited): workload L1/L2, execution phase/progress, waste L1/L2, primary
  bottleneck, intervention hints, abstain.
- **Weak supervision:** waste_to_intervention_map (HEURISTIC / MULTI_MODEL_CONSENSUS).
- **Empirical:** NONE yet (config_outcome.schema.json defined; no paired outcomes exist).

## 17. Readiness
- Semantic LoRA training: **PARTIAL** — schema, split, scaffold, and a validated pilot exist; the full
  semantic export needs the full Stage-B annotation over all trace roots.
- Config-selection LoRA training: **NOT READY / NOT_EMPIRICALLY_GROUNDED** — requires paired config outcomes.

## 18. Limitations
1. **Workload L1 agreement is weak** (α≈0.15-0.21) — MIXED_END_TO_END is a fuzzy human-judgment boundary.
   Treat workload labels as lower-confidence; lean on per-task cross-model voting.
2. **Multi-label Jaccard noisy** (0.33) — materiality threshold varies by annotator; needs a hard ≤3-L2 cap.
3. **No Qwen-8B dev model** (solver_D absent on disk) — the weak open-weight DEV perspective is under-sampled;
   held-out 32B was preserved as specified rather than silently swapped in.
4. **solver_A/F live runs ungraded** — outcome unknown for opus-4.7/4.6 traces (no effect on blind coding).
5. **PREEMPTIVE_HELPER_TOOL_BUILD is a harness artifact** (~32% of labels) — flagged harness_conditioned.
6. **Pilot, not full annotation** — agreement/aggregation are validated on 114 traces; full Stage-B over all
   roots (2 annotators + adjudicator + 10% audit) is the next action.
7. claude-as-annotator is slow (~12 min/batch); gemini wrapper dies after ~8 batches → ann3 reduced n.

## 19. Exact next action
Run **full Stage-B annotation** over all validated trace roots (solver_A/B/C dev; solver_E held-out
post-freeze for transfer audit only): 2 independent annotators/trace + adjudicator on disagreement + 10%
triple-audit, using the FROZEN v1 taxonomy and the closed_label_annotator_v1 prompt. Then regenerate the
per-task/per-model mappings and the semantic LoRA export over the full set, and re-run the red-team audit.
Config-selection data remains blocked on real paired config outcomes (out of this project's CPU-only scope).
