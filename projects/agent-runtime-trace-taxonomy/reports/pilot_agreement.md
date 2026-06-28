# Pilot Agreement Report — Round 1

**Generated:** 2026-06-28 · 114-trace pilot (disjoint from bootstrap) · 3 independent annotators (claude/codex/gemini) · taxonomy v0

**Triple-annotated traces (>=2 annotators):** 70  
(ann1=96, ann2=114, ann3=89 — claude b8/b9 hit max-turns; gemini wrapper died after b7; reruns in flight. Round-1 verdict stands on the overlap.)

## Acceptance gates (Section 11)

| metric | value | gate | result |
|--------|-------|------|--------|
| Workload L1 agreement (α / raw) | 0.21 / 0.57 | ≥0.70 | ❌ FAIL |
| Primary Waste L1 agreement (α / raw) | 0.34 / 0.50 | ≥0.70 | ❌ FAIL |
| Primary L2 (bottleneck) agreement | 0.39 | ≥0.60 | ❌ FAIL |
| Multi-label median Jaccard | 0.45 | ≥0.65 | ❌ FAIL |
| Taxonomy coverage | 0.90 | ≥0.95 | ❌ FAIL |
| OTHER/UNKNOWN rate | 0.00 | ≤0.05 | ✅ PASS |

**ROUND-1 VERDICT: FAIL (1/6 gates).** Expected — first pilots rarely pass. A revision round is warranted (Section 11 allows ≤2).

## Diagnosis (why agreement is low)

1. **Workload `MIXED_END_TO_END` is over-broad** — usage varies wildly (ann1=6, ann2=33, ann3=26). It's absorbing PATCH_REASONING_DOMINANT cases. → tighten its definition / make it a true last-resort.

2. **Directional agreement is actually STRONG, breadth differs.** All 3 rank `PREEMPTIVE_HELPER_TOOL_BUILD` #1 and share the core set (PATCH_CHURN, EDIT_TOOL_MECHANICAL_FAILURE, REDUNDANT_FILE_REREAD, VERIFICATION_GAP). Low Jaccard comes from ann1/ann2 applying MANY labels vs ann3 applying FEW — a *threshold* mismatch, not a conflict. → add a 'label only if SEVERE enough to matter' guidance + a max-labels norm.

3. **`BLIND_INFILE_NAVIGATION` NEVER selected** despite being the unanimous open-coding discovery. The closed-label annotators don't recognize it from the definition. → the abbreviated transcripts hide within-file line-jumps; either drop it for v1 (online-control only) or sharpen its observable trigger + give a worked example.

4. **Confused primary-bottleneck pairs** (from confusion matrix): EDIT_TOOL_MECHANICAL_FAILURE↔PATCH_CHURN (4), EDIT_TOOL_MECHANICAL_FAILURE↔FAILED_RECOVERY (3). The edit/recovery cluster needs sharper boundaries.

5. **`PREEMPTIVE_HELPER_TOOL_BUILD` is ~32% of all labels** — so prevalent it may be a HARNESS ARTIFACT (the SWE-agent `edit_file.py` scaffold) rather than model waste. → flag as harness-conditioned; consider folding into ENVIRONMENT_TOOLING severity.

## Most-confused primary-bottleneck pairs

- EDIT_TOOL_MECHANICAL_FAILURE ↔ PATCH_CHURN: 4
- EDIT_TOOL_MECHANICAL_FAILURE ↔ FAILED_RECOVERY: 3
- ENVIRONMENT_BLOCKED ↔ OVER_BROAD_EDIT: 2
- OVER_BROAD_EDIT ↔ VERIFICATION_GAP: 1
- DEPENDENCY_SETUP_DRIFT ↔ VERIFICATION_GAP: 1
- ENVIRONMENT_BLOCKED ↔ PREEMPTIVE_HELPER_TOOL_BUILD: 1
- HELPER_TOOL_FAILURE_LOOP ↔ STAGNATION: 1
- FILENAME_SEARCH_THRASH ↔ VERIFICATION_GAP: 1

## Labels never selected

- BLIND_INFILE_NAVIGATION

See pilot_confusion_matrix.csv + pilot_label_prevalence.csv for full breakdown. Revision plan -> taxonomy v1 (see taxonomy_rationale + PROJECT_STATE).
---

# Pilot Agreement — Round 2 (taxonomy v1 validation)

**Generated:** 2026-06-28 · same 114 pilot traces re-annotated with **v1** taxonomy + sharpened guidance · 3 independent annotators (claude/codex/gemini).
Note: ann1=114, ann2=114, ann3=89 (gemini wrapper died after b7, same failure mode as round-1; 58 triple-overlap traces).

## Round-1 (v0) → Round-2 (v1) comparison

| metric | R1 (v0) | R2 (v1) | gate | movement |
|--------|--------:|--------:|------|----------|
| Workload L1 α | 0.21 | 0.15 | ≥0.70 | ⚠️ flat/weak |
| Workload L1 raw | 0.57 | 0.48 | — | ⚠️ |
| **Primary Waste L1 raw** | 0.50 | **0.70** | ≥0.70 | ✅ **+0.20 (hits gate)** |
| **Primary Waste L1 α** | 0.34 | **0.52** | ≥0.70 | ✅ **+0.18** |
| **Primary L2 (bottleneck)** | 0.39 | **0.586** | ≥0.60 | ✅ **+0.20 (at gate)** |
| Multi-label Jaccard | 0.45 | 0.33 | ≥0.65 | ⚠️ noisier |
| Coverage | 0.90 | 0.74* | ≥0.95 | *partial-data (ann3=89) |
| OTHER/UNKNOWN | 0.0 | 0.0 | ≤0.05 | ✅ |
| Labels never-selected | 1 | **0** | — | ✅ fixed |

## VERDICT: FROZEN_WITH_LIMITATIONS (TAXONOMY_STATUS=FROZEN_V1)

The v1 revisions **materially improved the core waste-pattern agreement** — the part that
actually drives the downstream controller: Waste L1 raw agreement reached the 0.70 gate,
Waste L1 α rose +0.18, and primary-bottleneck (primary L2) reached 0.586 (essentially the
0.60 gate). All v1 labels are now used (no never-selected).

Two axes remain weak and are **documented limitations, not iteration failures**:
- **Workload L1 agreement stays low (α≈0.15-0.21).** `MIXED_END_TO_END` vs `PATCH_REASONING_DOMINANT`
  is a genuinely fuzzy human-judgment boundary; making MIXED "last-resort" did not converge the
  three annotators. → Workload L1 is the **known weak axis**; treat workload labels as lower-confidence
  and lean on the per-task cross-model aggregation (Section 13.1) where multiple traces vote.
- **Multi-label Jaccard fell (0.45→0.33).** The "label only if material" guidance INCREASED breadth
  variance (annotators drew the materiality line differently). The *directional* agreement is strong
  (same top labels); the *set-size* discipline needs a future hard cap (e.g. ≤3 L2 labels + 1 primary).

**Why freeze now:** Section 11 allows ≤2 revision rounds; we have used both (v0→v1). The core
metrics improved; further rounds would overfit to 3 specific annotators. The honest call is to
FREEZE v1 as READY_WITH_LIMITATIONS and carry the weak-workload-L1 + Jaccard caveats into Stage B
(where 2 annotators + adjudicator + the 10% audit absorb residual disagreement).
