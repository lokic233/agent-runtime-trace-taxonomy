# PROJECT STATE — clean-trace-optimizer-study

state_version: v1
project: clean-trace-optimizer-study
stage: TRACE_INVENTORY
clean_room_status: ACTIVE
semantic_annotation_status: PARALLEL_EXTERNAL
qwen_validation_status: SEALED
paired_outcomes_status: PENDING
clean_feature_status: DRAFT
correlation_protocol_status: DRAFT

## Lane model (single-operator, multi-pass)
- Lane A Raw Trace Auditor — neutral one-by-one memos (delegated to an independent sub-agent w/o opportunity access)
- Lane B Measurement Engineer — deterministic feature impl (src/extract_clean_trace_features.py)
- Lane C Measurement Skeptic — falsification pass (analysis/skeptic_review_v1.md)
- Lane D Statistics Lead — pre-registered correlation/intervention plans
- Lane E Runtime Intervention Engineer — config registry SPECS only (no paired outcomes this window)
- Lane F Reproducibility/Leakage Auditor — leakage + source-access audits

## Compute
- node: devvm14382 (96c, has all 5 reference trace sets + stats stack + ros)
- opus-4.7/4.6 raw traces: devgpu014:/data/users/dengcchi/hal_work/runs/full_opus4{7,6} (pulled via feature extraction there)
- Qwen solver: HOSTED devgpu014 vLLM:8001 (NO agent traces yet -> sealed placeholder)

## Honest scope for the autonomous window
Phases A-D + correlation + ablation + Phase-1 freeze are FULLY EXECUTED on graded dev traces.
Phase E paired interventions + LoRA require re-running SWE-agent x100s + 8B training -> NOT feasible now ->
  exact specs written, experiments registered, PAIRED_OUTCOMES_PENDING. No fabricated efficacy.
Qwen stays SEALED (config frozen, traces not generated/inspected).

## Incidental-exposure disclosure
Operator-requested reading of prior session transcripts incidentally surfaced the existing per-model
opportunity tables. Features are defined independently in clean code; negative controls quantify
independence. See reports/source_access_log.md.
