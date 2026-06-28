# Red-Team Audit (Section 17)

Hostile self-audit of the taxonomy + annotation dataset before declaring readiness.
Verdict legend: ✅ pass · ⚠️ pass-with-caveat · ❌ fail.

## 1. MODEL IDENTITY LEAKAGE ✅ (one real leak caught + fixed)
A REAL leak was found and fixed: opus-4.7 traces embed the tool path
`/root/tools/edit_anthropic/bin/str_replace_editor` — the SWE-agent scaffold names its editor
`edit_anthropic`, leaking the vendor via tool format. Fix: `render_trace.scrub()` neutralizes
`edit_anthropic→edit_tool`, vendor/model names→`the_model`, harness names→`agent_harness`, and
user paths→`/USER`; `render()` HARD-ASSERTS no fingerprint survives, for every cutoff. All
committed annotator-facing artifacts (manifests, packets, raw votes, taxonomy, examples) pass a
banned-substring scan (validate_all_artifacts blinding check = ✅). Solver names appear only as
solver_A..F; coder/annotator backend names (claude/codex/gemini) are disclosed PROVENANCE, not
solver identity.

## 2. FUTURE LEAKAGE ✅
generate_trace_prefixes.py strips outcome/submission/total-tokens/later-tests from every prefix
view; test_no_future_leakage.py (7/7) enforces: prefix is a true subset of FULL, T0=metadata-only,
monotonic growth, forbidden keys absent, tokens hard-nulled in prefixes. render() refuses to print
outcome for ANY cutoff.

## 3. TASK LEAKAGE ✅
Pilot manifest is disjoint from bootstrap (verified 0 overlap). test_split_leakage.py (5/5)
detects same-task-across-train/test and prefix/full-of-same-trace-across-splits. export split is
repo-disjoint.

## 4. REPOSITORY LEAKAGE ✅
export_lora_dataset.split_by_repo() makes train/test repo-disjoint and reserves a dedicated
repo_transfer_test; check_split() flags any repo appearing in both train and repo-transfer.
Claimed cross-repo generalization is therefore real, not random trace splitting.

## 5. OUTCOME-DEFINED LABELS ✅ (actively rejected)
All 3 open coders independently REJECTED outcome-in-disguise labels (FAILED_TO_SOLVE,
BAD_REASONING, LOW_QUALITY_PATCH, NO_TESTS_MEANS_FAILURE, MANY_SEARCHES_MEANS_WASTE). The two
labels that flirt with outcome (VERIFICATION_GAP, BUDGET_EXHAUSTION_NONCONVERGENCE) carry explicit
outcome_collapse_mitigation defining them by observable behavior independent of the hidden resolve
status. Annotators never see outcome.

## 6. TAXONOMY OVERLAP ⚠️
Every L2 label has an explicit distinguishing_rule + boundary_cases.md gives 8 hard pairwise tests.
CAVEAT: the pilot confusion matrix shows residual confusion in the edit/recovery cluster
(EDIT_TOOL_MECHANICAL_FAILURE ↔ PATCH_CHURN ↔ FAILED_RECOVERY) — v1 added an explicit decision
order to sharpen it, but Stage B should monitor this cluster's adjudication rate.

## 7. UNOBSERVABLE LABELS ✅
Categories needing hidden CoT / per-event tokens / gold patch / wall-clock were QUARANTINED
(rejected_and_merged_labels.md): TOKENS_PER_EVENT, HIDDEN_REASONING, FINAL_PATCH_CORRECTNESS,
PER_CALL_WALLCLOCK, LOW_RESULT_UTILIZATION. Memory-retrieval L2 dropped (SWE-agent has no memory layer).

## 8. AUTOMATIC-METRIC OVERREACH ✅
Deterministic metrics are EVIDENCE, never labels. The taxonomy + annotator prompt explicitly state:
low result-utilization ≠ UNUSED_RESULT; many searches ≠ REDUNDANT_SEARCH (justified after
hypothesis-falsification); many tests ≠ REDUNDANT_TEST (code/env may have changed). Inherited from
the TokenSaver lexical-similarity caveat. result_utilization is null at L0 (LOW observability).

## 9. MODEL-STEREOTYPE BIAS ⚠️
Annotators are blinded to model identity (only STRONG/MEDIUM/WEAK tier + local/remote), which
prevents reputation bias. CAVEAT: capability_tier IS shown (required by the downstream controller),
so a "WEAK" tier could in principle prime harsher labeling. Mitigation: tier is generic (not a model
name) and the per-model analysis reports BOTH raw and matched-task-adjusted distributions
(aggregate_per_model) so identical behavior can be compared across tiers. Stage B should spot-check
whether WEAK-tier traces get more SEVERE severities for identical deterministic signatures.

## 10. CONFIG GOLD FABRICATION ✅
No agent declared a Pareto/config winner. waste_to_intervention_map.yaml is explicitly WEAK
SUPERVISION (provenance HEURISTIC/MULTI_MODEL_CONSENSUS) with a "not gold config" caveat.
recommended_config=null, pareto_label_status=NOT_EMPIRICALLY_GROUNDED. config_outcome.schema.json
defines regression strictly as (baseline succeeds AND candidate fails), paired — the ONLY valid gold
source, NOT produced by annotation.

## 11. CLASS IMBALANCE ⚠️
pilot_label_prevalence.csv shows PREEMPTIVE_HELPER_TOOL_BUILD dominates (~32% of labels). KEY
FINDING: this is largely a HARNESS ARTIFACT (the SWE-agent edit_file.py scaffold), now flagged
harness_conditioned in v1 with guidance to OMIT unless MODERATE+. Rare labels (some CONTROL_RECOVERY)
will need oversampling or merging before LoRA training — flagged for the full-annotation export.

## 12. EVIDENCE INTEGRITY ✅
The annotation schema REQUIRES evidence_action_ids per waste label; the annotator prompt rejects any
label without cited [i] indices; the adjudicator drops labels lacking valid evidence. Pilot evidence
overlap median ≈ 0.4-0.5 (annotators cite overlapping but not identical action ids).

## 13. SCHEMA INTEGRITY ✅
All 4 schemas are valid JSON; test_annotation_schema.py (5/5) validates a conformant record + the
solver_alias pattern + the no-numeric-confidence rule + the paired-regression definition.

## 14. PROVENANCE ✅
Every label traces to: raw blinded trace (locator, gitignored) → per-annotator raw votes
(annotations/raw_votes/pilot_round{1,2}/) → adjudication (pilot_adjudication.json) → taxonomy_version
(v0/v1 with revision_history) → prompt_version (v1). Open-coding provenance (support = # coders)
recorded per label. research-os CLAIM-0001/EXP-0001 ties it to the durable research ledger.

## Summary
- **Hard pass:** 1,2,3,4,5,7,8,10,12,13,14 (11/14)
- **Pass-with-caveat:** 6 (edit-cluster confusion), 9 (tier-priming risk), 11 (helper-build dominance + rare-label imbalance)
- **Fail:** none
The caveats are documented and carried into Stage B (2 annotators + adjudicator + 10% audit) and into
the export (rare-label handling). No fabrication, no leakage, no outcome-collapse.
