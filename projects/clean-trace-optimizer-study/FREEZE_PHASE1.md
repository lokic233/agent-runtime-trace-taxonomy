# FREEZE_PHASE1.md — clean-trace-optimizer-study

FROZEN: 2026-06-28 (autonomous window). After this commit, the existing-taxonomy blocked artifacts
may be opened for POST-HOC COMPARISON ONLY. They must NOT be used to silently alter this frozen study.

## Git
- instance repo: lokic233/agent-runtime-trace-taxonomy, subtree projects/clean-trace-optimizer-study
- freeze commit SHA (pre-freeze state): 0f49e87c4cd7baf53273a56295685901bcffd16d
- node: cli:devvm14382 (analysis); raw opus traces on cli:devgpu014

## Frozen artifact hashes (sha256, first 16)
- 9c77101464 7e6da7  features/clean_trace_feature_spec_v1.yaml
- 919f337292 7a4c9a  analysis/correlation_analysis_plan_v1.md
- 111213d15c 7139e5  config/runtime_config_registry_v1.yaml
- a7aba917cb e26bb9  config/qwen32b_validation_solver.yaml
- b96f01524f c49e42  manifests/development_trace_inventory.jsonl
- 571baec40b f408d2  src/extract_clean_trace_features.py
- 90ff305936 503fd4  src/clean_classify.py
- c78b15d9c4 18d86a  src/clean_loader.py

## Primary features (FROZEN_V1) — 9
SEARCH_NO_NEW_EVIDENCE_RATE, OVERSIZED_THEN_NARROW_READ_RATE, NO_EVIDENCE_PATCH_CHURN_RATE (applied-edits),
EDIT_MECHANICAL_FAILURE_RATE, POST_EDIT_TEST_GAP, STAGNATION_FRACTION (fraction_actions_in_no_new_evidence_streaks),
TOOL_ERROR_RATE, ENVIRONMENT_SETUP_RATE (harness covariate), REDUNDANT_REREAD_RATE (secondary).
All precision >=0.835 on the headline set (feature_calibration.md). Detector code + thresholds frozen.

## Correlation hypotheses (pre-registered, see analysis/correlation_analysis_plan_v1.md)
RQ1 cost(n_actions) ~ feature + solver+harness+repo (+/- log n_events).
RQ2 logit(resolved) ~ feature + solver+harness+repo + log n_events  (CORE cohort A/B/C only).
RQ3 non-convergence (>=95th-pct action cap) ~ feature + controls.
Predictive ablation A(length) / B(+meta) / C(+features), GroupKFold by task.

## Intervention hypotheses (pre-registered, SPECS only, PAIRED_OUTCOMES_PENDING)
H1 SEARCH_CONSTRAINED x SEARCH_NO_NEW_EVIDENCE_RATE; H2 PATCH_GUARD x NO_EVIDENCE_PATCH_CHURN_RATE;
H3 VERIFY_HEAVY x POST_EDIT_TEST_GAP. Actionable only if matched intervention benefits HIGH-signal > LOW-signal.

## Inclusion / exclusion
- Development cohort (resolution model): A=opus-4.7, B=opus-4.5, C=sonnet-3.5 (graded, instruct-agents).
- 32B-class E/G/H + opus-4.6 F: robustness/secondary, NOT in primary resolution model (fine-tune + harness confound).
- min-exposure gates per feature (searches>=3, applied-edits>=2, n_actions>=5) -> missing=None, never 0.
- solver_C edits flagged harness-contaminated (_split_string future-annotations bug) — excluded from churn evidence.

## Outcome definitions
resolved = SWE-bench harness resolved (authoritative: HAL grade JSON for A/F; report.json for G/H; index for B/C/E).
cost = n_actions (action-step count) — TRUE TOKENS NOT PER-TRACE ATTRIBUTABLE (documented limitation).
non-convergence = trace at/above per-solver 95th-pct action count.

## Statistical models: standardized logistic/linear betas; task-clustered bootstrap 95% CI (600 reps);
BH correction across the primary feature set per outcome; GroupKFold(5) by task for the ablation.

## Negative controls (run): feature permutation (~0), random synthetic feature (~0 on cost; ~0.13 on
resolution single-beta -> single-feature resolution CIs flagged optimistic, ablation trusted).

## Qwen holdout policy: SEALED. Solver config frozen (config/qwen32b_validation_solver.yaml). No Qwen agent
trace exists yet (solver hosted, not run as an agent). Unseal only after FREEZE_PHASE2_BEFORE_QWEN.md.

## CLEAN-ROOM INCIDENTAL-EXPOSURE DISCLOSURE (carried from source_access_log.md)
Operator-requested reading of prior session transcripts incidentally surfaced the existing per-model
opportunity tables. Features were defined independently (own loader/classifier/extractor, own algorithms).
Negative controls + the skeptic review (no length/solver/harness collapse) demonstrate the clean signal is
not a relabeling of the prior conclusions. Conservative reading: feature-FAMILY choices are
informed-but-independent; the deterministic correlation/ablation results are computed only from raw traces.

## PHASE-1 VERDICTS (frozen, pre-post-hoc-comparison)
- CORRELATION_VERDICT (cost):        TRACE_LENGTH_ONLY  (features add R^2 +0.0001 OOS over n_events)
- CORRELATION_VERDICT (resolution):  INCREMENTAL_SIGNAL (WEAK)  (ablation +0.0023 AUROC over solver+harness+repo+length)
- Strongest incremental signal:      NON-CONVERGENCE (RQ3) — stagnation_fraction +1.32, search_no_new_evidence +0.88
- TRACE_SIGNAL_VERDICT:              ASSOCIATIVE_ONLY so far (ACTIONABLE requires paired outcomes -> PENDING)

## Status flags set
clean_feature_status: FROZEN_V1
correlation_protocol_status: FROZEN_V1
qwen_validation_status: SEALED
paired_outcomes_status: PENDING
