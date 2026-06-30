# Phase 5 — Annotation Agreement & Ontology Consolidation

## Cross-role agreement (3 annotators per event, auto-generated)

| dimension | agreement | interpretation |
|-----------|:---:|---|
| preferred_action | **59%** unanimous | moderate — disagreement on NO_OP vs KEEP_FULL (both "don't prune") |
| semantic_role | **96%** | near-perfect — annotators identify same content type |
| semantic_liveness | **100%** | perfect — all agree on "active" (selection bias artifact) |
| redundancy_type | **91%** | strong |
| recoverability | **96%** | near-perfect |
| dependency_risk | **67%** | moderate — disagreement on "directly_referenced" vs "supports_hypothesis" |
| task_phase | **98%** | near-perfect |

## Interpretation
- **Latent-state classification is highly reliable** across annotator roles (91-100% on 5 of 6 dimensions).
- **preferred_action** has lower agreement (59%) but the disagreements are between NO_OP/KEEP_FULL_CONTENT (both mean "don't prune"), not between prune-vs-keep. Substantive agreement on "don't modify this segment" is ~100%.
- **dependency_risk** (67%) is the genuinely uncertain dimension — whether content "directly supports an unresolved hypothesis" vs "is likely needed for verification" requires semantic judgment that varies by annotator role.

## Pattern-name consolidation (107→~15 families)
The 107 distinct names cluster into ~15 semantic families:
- `foundational_task_instruction*` (21 annotations): the task statement or first large context block
- `localization_target_source*` (10): source code being actively localized/examined
- `primary_edit_target*` (8): the file the agent is about to edit
- `test_output*` (4): test execution results
- `exploration_*` (3): broad search results
- `stack_trace*` (2): error stack traces

## Signal Ontology v0 (frozen axes, from 132 annotations + agreement)
See `results/pruning_ab/signal_ontology_v0.json` (generated separately). Key finding: on the tested (largest-observation) decision points, the ontology is dominated by a SINGLE latent state: `{active, none, deterministic_refetch, directly_referenced, localization/exploration}` → KEEP. The ontology will become meaningfully diverse only when the discovery samples genuinely REDUNDANT or SUPERSEDED segments (Phase 8 MRT's broader sampling).
