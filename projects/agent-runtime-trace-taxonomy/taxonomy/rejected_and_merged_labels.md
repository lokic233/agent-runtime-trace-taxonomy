# Rejected & Merged Labels (v0)

Preserving disagreements and rejections is mandatory (Section 4/8). This is the audit trail.

## REJECTED — outcome-in-disguise (cannot be observed; ≈ "the run failed")
| label | proposed by | why rejected |
|-------|-------------|--------------|
| FAILED_TO_SOLVE | coder_B | pure outcome; outcomes are hidden from annotators by design |
| BAD_REASONING | coder_B | relies on hidden cognition, not commands/observations |
| LOW_QUALITY_PATCH | coder_B | needs gold-patch/diff comparison, not trace behavior |
| NO_TESTS_MEANS_FAILURE | coder_B | "no tests" is a process pattern only when an oracle was plausible; not = failure |
| MANY_SEARCHES_MEANS_WASTE | coder_B | search count alone can reflect a cross-file task; must judge vs new evidence |
| "incapable of string replacement" | coder_C | the str_replace_editor harness script crashes on multiline — a TOOL bug, not agent incapacity (→ became EDIT_TOOL_MECHANICAL_FAILURE) |

## QUARANTINED — require unavailable information (not in v0; revisit if data arrives)
| candidate | by | missing data |
|-----------|----|--------------|
| TOKENS_PER_EVENT / TOKEN_WASTE_PER_EVENT | A,B | per-event token counts (only aggregate model_stats in .traj) |
| LOW_RESULT_UTILIZATION | B | needs full content + lexical compare; truncated transcripts unreliable (TokenSaver lexical caveat) |
| HIDDEN_REASONING_CONFUSION | A,B | agent intent / chain-of-thought is out of scope by protocol |
| FINAL_PATCH_CORRECTNESS | A,B | gold patch + outcome hidden |
| PER_CALL_WALLCLOCK | A | no timing in .traj |
| LATER_RECOVERY_AFTER_TRUNCATION | B | some transcripts truncated before late recovery (fix: bigger pilot text budget) |

## MERGED — near-duplicate proposals collapsed into one canonical label
| canonical (v0) | merged-in proposals | rationale |
|----------------|---------------------|-----------|
| BLIND_INFILE_NAVIGATION | coder_C BLIND_DIRECTORY_WALK (sibling: cd/ls thrash) | both are "navigation without targeting"; directory-walk noted as a variant under FILENAME_SEARCH_THRASH |
| PATCH_CHURN | coder_B PATCH_CHURN_WITHOUT_VALIDATION | same concept, name normalized |
| VERIFICATION_GAP | coder_B NO_VERIFICATION_AFTER_PATCH + coder_A VERIFICATION_GAP_BEFORE_SUBMIT | same observable (edited, never tested before submit) |
| CONTEXT_BLOAT | coder_B BROAD_FILE_DUMP_THEN_NARROW_READ + coder_C OUTPUT_TRUNCATION_RECOVERY | oversized read forcing narrow re-reads |
| DEPENDENCY_SETUP_DRIFT | coder_B ENVIRONMENT_DEPENDENCY_DRIFT + coder_C ENVIRONMENT_TOOL_NOT_FOUND | both = chasing a runnable verification env via dep/tool changes |
| EDIT_TOOL_MECHANICAL_FAILURE | coder_C EXACT_MATCH_REPLACE_FAILURE + coder_C HARNESS_SYNTAX_ERROR_BLOCK | mechanical edit-tool rejection (whitespace/match), not reasoning |
| PREMATURE_SCRATCH_REPRO | coder_B PREMATURE_SCRATCH_REPRO_CHURN + coder_A UNOPENED_FILE_EDIT_ATTEMPT (partial) | editing scratch/repro before localization |

## SYNTHESIZER FALSE-MERGES corrected by the human synthesizer (Lane 6)
The automatic clusterer (single-link on name+def similarity) over-merged a few; corrected:
- `LIMIT_EXIT_STAGNATION` was auto-clustered with BLIND_INFILE_NAVIGATION → **split**: it is
  BUDGET_EXHAUSTION_NONCONVERGENCE (CONTROL_RECOVERY), not a localization pattern.
- `NON_CONVERGENT_LOCALIZATION` straddles localization + control → assigned to
  BUDGET_EXHAUSTION_NONCONVERGENCE with a localization co-signal, NOT a new label
  (avoids an outcome-collapse "the run that didn't finish" label).

## DROPPED seeds (from the prompt's candidate list) not instantiated in v0
| seed | reason |
|------|--------|
| MEMORY_OVER_RETRIEVAL, MEMORY_RECALL_MISS | SWE-agent has no memory subsystem → structurally unobservable |
| IRRELEVANT_CONTEXT | not separately observable from CONTEXT_BLOAT w/o content scoring → folded in |
| WRONG_LOCALIZATION, LOCALIZATION_DRIFT | need gold location to call "wrong" → outcome-ish; deferred (pilot may add if distinguishable from THRASH/BLIND_INFILE) |
| PREMATURE_EDIT | overlaps PREMATURE_SCRATCH_REPRO + PATCH_CHURN → folded; revisit in pilot |
| INSUFFICIENT_VERIFICATION | kept as VERIFICATION_GAP (clearer observable); "insufficient" (vs absent) needs oracle knowledge |
| WRONG_TEST_SELECTION | needs gold-test knowledge → quarantined |
| PREMATURE_ESCALATION, LATE_ESCALATION | SWE-agent runs are single-solver (no escalation events observed) → out of scope for this data |
| TOOL_FAILURE_LOOP | instantiated as HELPER_TOOL_FAILURE_LOOP (the observed form) |
