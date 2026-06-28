# Source Access Log — clean-trace-optimizer-study

Records every repository/file accessed, and the clean-room firewall status.
Append-only. Timestamps in UTC.

## Clean-room firewall (Phase-1)

BLOCKED until Phase-1 freeze (exist on disk at
`~agent_runtime_trace_taxonomy/projects/agent-runtime-trace-taxonomy/`):
- reports/per_model_opportunity.md          [BLOCKED — not opened]
- reports/opportunity_analysis.json         [BLOCKED — not opened]
- src/compute_opportunity.py                [BLOCKED — not opened]
- taxonomy/waste_to_intervention_map.yaml   [BLOCKED — not opened]
- src/extract_deterministic_features.py     [BLOCKED — treated as "existing detector thresholds"]
- taxonomy/waste_taxonomy_v1.yaml           [BLOCKED — existing claims about which solver exhibits which waste]
- mappings/per_model_*.json, reports/per_model_*  [BLOCKED — per-model opportunity rankings]

ALLOWED (trace-source inventory, normalization schemas, raw trace loaders,
parser tests, generic annotation schemas, file-layout docs):
- src/normalize_traces.py                   [ALLOWED — raw trace loader/parser]
- src/trace_index.py                        [ALLOWED — file-layout/inventory]
- schemas/*                                 [ALLOWED — normalization schemas]
- tests/* (parser tests)                    [ALLOWED]
- config/trace_sources.yaml (existing)      [ALLOWED — trace-source inventory]

## HONEST DISCLOSURE — incidental exposure (recorded 2026-06-28)

The operator asked me to read three prior Navi session transcripts to extract
trace paths and the Qwen hosting config. Those transcripts (session
7dd580a4 "Attached Text Files Analysis") INCIDENTALLY contained the existing
project's per-model opportunity tables and a heuristic waste->intervention
mapping. I did not seek them; they were embedded in the conversation I was
asked to read.

Mitigation, so the clean-room derivation remains genuinely independent:
- I am defining ALL features from scratch in clean code (src/extract_clean_trace_features.py),
  with my own algorithms, denominators, and thresholds — NOT copied from the
  existing extract_deterministic_features.py or compute_opportunity.py.
- The exposed conclusions were OPPORTUNITY RANKINGS (a heuristic prevalence x
  capability-gap score), NOT the deterministic correlation/intervention results
  this clean lane produces. My primary quantitative chain (features -> calibration
  -> correlation -> ablation) is computed only from raw traces.
- This exposure is logged here and repeated in FREEZE_PHASE1.md and FINAL_REPORT.md
  so reviewers can weigh it. The conservative reading: treat the clean lane's
  feature-FAMILY choices as informed-but-independent, and lean on the negative
  controls (trace-length-only, permutation, solver-ID-only) to demonstrate the
  signal is not merely a relabeling of the prior conclusions.

## Access entries

| time (UTC) | node | path | role | phase |
|---|---|---|---|---|
| 2026-06-28T16:20 | cli:devgpu014 | ~research-os/engine/ros.py --help | engine API | setup |
| 2026-06-28T16:22 | cli:devvm14382 | src/normalize_traces.py (header only) | ALLOWED loader | TRACE_INVENTORY |
| 2026-06-28T16:22 | cli:devvm14382 | /tmp/index_all.jsonl (schema inspect) | existing index (features ignored) | TRACE_INVENTORY |
| 2026-06-28T16:24 | cli:devgpu014 | hal_work/runs/full_opus4{6,7}/ (file listing) | raw trace inventory | TRACE_INVENTORY |
| 2026-06-28T16:25 | cli:devvm14382 | swebench_traces/verified/* (file listing) | raw trace inventory | TRACE_INVENTORY |
