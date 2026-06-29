# PROJECT STATE — clean-trace-optimizer-study

state_version: v1
project: clean-trace-optimizer-study
stage: PHASE1_FROZEN
clean_room_status: ACTIVE
semantic_annotation_status: PARALLEL_EXTERNAL
qwen_validation_status: SEALED
paired_outcomes_status: PENDING
clean_feature_status: FROZEN_V1
correlation_protocol_status: FROZEN_V1

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

## 2026-06-28 UPDATE — Qwen UNSEALED as DEVELOPMENT paired-intervention solver (operator decision)
Operator directed: use Qwen2.5-Coder-32B-Instruct-AWQ as the ABLATION/paired-intervention executor
(not as a sealed held-out transfer test). 8B LoRA verification handled separately by operator.
HONEST CONSEQUENCE recorded: this converts Qwen from "held-out transfer validation" to a "development
paired-outcome solver." The final Qwen result is therefore a REAL paired-intervention result on Qwen,
NOT a clean held-out transfer claim. QWEN_TRANSFER_VERDICT stays N/A; instead we report
INTERVENTION_HETEROGENEITY + PAIRED_OUTCOMES on Qwen directly.
paired_outcomes_status: RUNNING (Qwen-32B-AWQ on devgpu014 vLLM:8001, 64 tasks x 4 configs)
qwen_validation_status: UNSEALED_AS_DEVELOPMENT (per operator)

## 2026-06-28 — DUAL-EXECUTOR ABLATION DESIGN (operator pivot: Qwen weak as executor)
Qwen-32B as EXECUTOR is too weak (~10% resolve, 55% empty patches) -> paired regression/improvement
events too sparse. PIVOT (operator-directed):
- STRONG EXECUTORS via PlugBoard shim (mTLS, 127.0.0.1:8731): claude-opus-4-7 (74% base) + 4-6 (69%).
  Real resolve headroom -> measurable paired regression/improvement. VALIDATED: 4.7 DEFAULT resolved
  django-11099 (22/22) in 3 calls via run_interv_pb.py (swebench_backticks.yaml + litellm anthropic/ + drop_params).
- Qwen-32B-AWQ = CONTROLLER candidate (PROMPTED_LOCAL selector arm) + its own executor sweep (running, 122/256).
- PAIRING: of my 64-task pool, 4.7 baseline-resolves 50, 4.6 resolves 48 (vs Qwen ~7) -> strong headroom.
- HARNESS NOTE: intervention arms use mini-swe-agent (backticks); prior HAL 466 baselines used SWE-agent-1.0
  (function_calling). For clean pairing, run DEFAULT in the SAME mini-swe-agent harness as the intervention
  arms; use the 466 HAL baselines as a cross-harness reference only.
INFRA LESSONS (this session): systemd-run --user (survives disconnect; nohup/setsid SIGTERM'd);
  podman not docker (MSWEA_DOCKER_EXECUTABLE); MSWEA_COST_TRACKING=ignore_errors; submission is a DICT
  (agent.run returns {exit_status,submission} — unpacking as tuple silently dropped every patch);
  Claude needs temperature unset (drop_params, only temp=1) + backticks config for format; regrade2.regrade
  (file-based podman cp, NOT heredoc) for grading. Watchdog auto-kills orphan containers + runaway pytest.
