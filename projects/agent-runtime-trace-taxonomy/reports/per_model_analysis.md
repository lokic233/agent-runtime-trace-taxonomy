# Per-Model Semantic Waste Analysis (REAL annotated labels)

**Generated:** 2026-06-29 · full Stage-B annotation · 2 annotators (codex+claude) + adjudicate-on-disagreement · taxonomy v1 (frozen)

**Annotation volume:** 2,000 traces (500 each × 4 models). Both-voted: A 470, B 491, C 481, G 493 (97% overall). Adjudication-flagged conflicts upgraded separately.

> COHORT NOTE: opus-4.7/4.5/sonnet-3.5 = CLEAN instruct-agent cohort (comparable). Skywork-32B = SEPARATE open-weight-32B cohort (RL-tuned, OpenHands scaffold) — shown for reference, NOT mixed into clean-cohort conclusions. solver_E (SWE-agent-LM-32B) + solver_H (EntroPO) archived as tuning outliers.

## Waste-label prevalence (% of each model's 500 traces)

| waste L2 label | opus-4.5 | opus-4.7 | sonnet-3.5 | Skywork-32B* |
|----------------|---------:|---------:|-----------:|-------------:|
| EDIT_TOOL_MECHANICAL_FAILURE | 7.0% | 12.0% | 32.0% | 26.2% |
| FAILED_RECOVERY | 8.4% | 4.6% | 23.8% | 11.4% |
| VERIFICATION_GAP | 0.4% | 0.2% | 13.8% | 32.6% |
| PATCH_CHURN | 8.2% | 15.0% | 13.4% | 4.4% |
| ENVIRONMENT_BLOCKED | 2.6% | 4.8% | 5.0% | 15.2% |
| DEPENDENCY_SETUP_DRIFT | 2.4% | 1.0% | 9.8% | 13.8% |
| BUDGET_EXHAUSTION_NONCONVERGENCE | 0.0% | 7.6% | 17.0% | 0.0% |
| PREMATURE_SCRATCH_REPRO | 2.2% | 0.8% | 16.0% | 3.4% |
| CONTEXT_BLOAT | 16.6% | 1.2% | 1.0% | 2.0% |
| STAGNATION | 1.8% | 3.0% | 5.6% | 9.4% |
| HELPER_TOOL_FAILURE_LOOP | 13.2% | 0.2% | 0.4% | 0.6% |
| SEARCH_WITHOUT_NEW_EVIDENCE | 1.2% | 3.8% | 4.6% | 4.2% |
| REDUNDANT_FILE_REREAD | 2.4% | 0.0% | 8.2% | 2.4% |
| FILENAME_SEARCH_THRASH | 1.6% | 1.0% | 6.4% | 3.0% |
| REDUNDANT_TEST | 2.6% | 3.0% | 0.6% | 1.4% |
| PREEMPTIVE_HELPER_TOOL_BUILD | 7.6% | 0.0% | 0.0% | 0.0% |

\* Skywork-32B is the SEPARATE open-weight cohort — compare with caution (different scaffold/tuning).

## Key findings (clean cohort: opus-4.5 / opus-4.7 / sonnet-3.5)

1. **Capability gradient is real and semantic.** sonnet-3.5 (weakest, 33.6% resolve) shows dramatically more EDIT_TOOL_MECHANICAL_FAILURE (32% vs opus 7-12%), FAILED_RECOVERY (24% vs 5-8%), and BUDGET_EXHAUSTION (17% vs 0-8%). The strong opus models rarely hit these.
2. **VERIFICATION_GAP separates weak from strong sharply:** sonnet 13.8% vs opus-4.5 0.4% / opus-4.7 0.2%. Strong models verify before submitting; the weak one often doesn't.
3. **opus-4.5's signature is CONTEXT_BLOAT (16.6%) + HELPER_TOOL_FAILURE_LOOP (13.2%) + PREEMPTIVE_HELPER_TOOL_BUILD (7.6%)** — these are largely its live-SWE-agent *scaffold* behaviors (harness-conditioned), not reasoning waste. opus-4.7 (classic SWE-agent scaffold) shows almost none of these → confirms they're harness artifacts.
4. **opus-4.7's main real waste is PATCH_CHURN (15%)** — it edits aggressively. Plus BUDGET_EXHAUSTION (7.6%) on hard tasks.
5. **Primary bottleneck distribution** (per model) is in mappings/per_model_summary.json.

## Skywork-32B (open-weight, separate)
Highest VERIFICATION_GAP (32.6%), ENVIRONMENT_BLOCKED (15.2%), DEPENDENCY_SETUP_DRIFT (13.8%) — the open-weight-32B struggles most with verification discipline and environment handling. Treated separately so it doesn't skew the clean-cohort opportunity signal.

## Honesty notes
- Labels are from MULTI_MODEL_CONSENSUS (2 annotators + adjudicate-on-disagreement); ~32-57% of traces had a disagreement flagged for adjudication (mostly workload-L1 + primary-bottleneck — the known fuzzy axes). The percentages above use auto-merged labels (agreed intersection, or union/single where 1 vote); full gemini adjudication of flagged conflicts refines but is not expected to change the directional story.
- These are OBSERVED waste prevalences, NOT efficacy claims. See per_model_opportunity.md.