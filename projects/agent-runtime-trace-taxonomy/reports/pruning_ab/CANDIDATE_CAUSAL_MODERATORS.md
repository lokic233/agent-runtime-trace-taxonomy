# Phase 6 — Candidate Causal Moderators (action-specific, from ontology)

## The honest picture from Phase 3-5
The blind discovery overwhelmingly produced `active / keep` patterns (selection bias toward largest = active observation). Only 6/132 annotations recommended an intervention (5 GENTLE_CAP, 1 LINE_DEDUP). This means:

**The current ontology does NOT yet contain enough "prune-recommended" examples to derive moderator hypotheses from observational data.** The hypotheses below are THEORETICAL — grounded in the proven mechanisms (cache tax + intelligence tax) and the ontology's conceptual axes — and REQUIRE Phase 8 MRT to validate. Do not treat them as supported by the blind discovery alone.

## Candidate moderators (action-specific, from the ontology's axes)

### 1. `exact_duplicate + exact_copy_elsewhere + no_active_reference`
→ **LINE_DEDUP should reduce cost with low quality risk.**
- Evidence: INTELLIGENCE_TAX_CAUSALITY.md (redundancy removal = 0 dose-controlled drift).
- Falsification: test whether this pattern predicts LINEDEDUP's local cost-delta differently than on non-matching segments (Phase 8 CATE).
- Current data: INSUFFICIENT (only 1 LINE_DEDUP annotation).

### 2. `large_test_output + only_error_signature_used`
→ **GENTLE_CAP or RETRIEVABLE_REFERENCE should reduce cost.**
- Evidence: 5 GENTLE_CAP annotations in blind discovery; test outputs are among the largest obs.
- Falsification: does capping test-output segments cause reread vs capping source-code segments?
- Current data: PARTIALLY available (5 examples).

### 3. `active_evidence + directly_referenced + unresolved_hypothesis`
→ **KEEP_FULL_CONTENT is the safe action** (any removal → drift).
- Evidence: the overwhelming finding of Phase 3 (93/132 = KEEP).
- Falsification: does removing this content type cause more drift than removing redundant content? (already shown by intelligence tax dose-control: destructive > redundant drift).
- Status: SUPPORTED by mechanism evidence (Phase 2).

### 4. `prefix_rewrite + long_remaining_horizon`
→ **Cache tax especially large** (more future calls to pay the creation penalty).
- Evidence: CACHE_TAX_CAUSALITY.md (10× cache-creation jump from prefix rewrite).
- Falsification: does the interaction `prefix_rewrite × remaining_calls` predict effective-cost-delta? Requires per-event data (Phase 8).
- Status: MECHANISM SUPPORTED; heterogeneity UNTESTED.

### 5. `repeated_file_read + no_intervening_write`
→ **Content is dedupable** (it's literally the same file content restated).
- Evidence: conceptual from the LINEDEDUP mechanism (drops already-seen lines).
- Falsification: are repeated-read segments where LINEDEDUP saves most? (testable from existing ledger activation data).
- Status: TESTABLE from existing data (Phase 7 screening).

## Phase 7 screening targets
From the above, the ONE moderator testable retrospectively (without new runs) is **#5: does LINEDEDUP fire more and save more on segments with high dup-vs-prior**? This uses the existing `candidate_dup_lines_vs_prior` feature from the blind views + the ledger's `chars_removed` field.

The others (1, 2, 4) require the MRT's broader segment sampling to have enough non-keep examples.

## Status
**Current moderators = THEORETICAL hypotheses grounded in proven mechanisms.** Not yet observationally validated (except #3 which is the intelligence tax result). Phase 8 MRT is REQUIRED for CATE estimation on the action-specific moderators.
