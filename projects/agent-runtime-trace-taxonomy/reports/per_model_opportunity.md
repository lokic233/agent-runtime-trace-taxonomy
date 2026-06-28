# Improvement-Opportunity Analysis (per waste pattern, overall + per model)

**Generated:** 2026-06-28 · `src/compute_opportunity.py` · all 1500+ traces

> ⚠️ **HEURISTIC, not empirical.** Opportunity = prevalence + capability-gap + observability.
> It marks *where waste is worth targeting*, NOT proven efficacy. Proving an intervention
> improves outcomes needs paired config outcomes → `PARETO_POLICY_DATA_VERDICT = NOT_EMPIRICALLY_GROUNDED`.
> Detectors are DETERMINISTIC PROXIES over the normalized index, not the semantic labels;
> full Stage-B annotation will sharpen the exact percentages (directional ranking should hold).

## Overall opportunity (sorted)

| tier | waste pattern | all% | weak−strong gap | interpretation |
|------|---------------|----:|----:|----|
| 🟢 HIGH | VERIFICATION_GAP | 72% | +26 | strong weak-model discriminator |
| 🟢 HIGH | SEARCH_WITHOUT_NEW_EVIDENCE | 48% | +66 | strong weak-model discriminator |
| 🟡 MED | PATCH_CHURN | 54% | +5 | systemic (all models) |
| 🟡 MED | REDUNDANT_FILE_REREAD | 32% | +10 | moderate |
| 🟡 MED | CONTEXT_BLOAT | 32% | +10 | moderate |
| 🟡 MED | STAGNATION | 17% | +24 | strong weak-model discriminator |
| 🔴 LOW | DEPENDENCY_SETUP_DRIFT | 61% | -92 | HARNESS/strong-model artifact — intervening HURTS |
| 🔴 LOW | PREEMPTIVE_HELPER_TOOL_BUILD | 56% | -87 | HARNESS/strong-model artifact — intervening HURTS |
| 🔴 LOW | FILENAME_SEARCH_THRASH | 42% | -26 | HARNESS/strong-model artifact — intervening HURTS |
| 🔴 LOW | FAILED_RECOVERY | 13% | -8 | moderate |
| 🔴 LOW | EDIT_TOOL_MECHANICAL_FAILURE | 10% | +2 | moderate |
| 🔴 LOW | REDUNDANT_TEST | 4% | +10 | moderate |
| 🔴 LOW | HELPER_TOOL_FAILURE_LOOP | 3% | -1 | moderate |
| 🔴 LOW | ENVIRONMENT_BLOCKED | 3% | -1 | moderate |
| 🔴 LOW | BUDGET_EXHAUSTION_NONCONVERGENCE | 2% | +1 | moderate |
| 🔴 LOW | PREMATURE_SCRATCH_REPRO | 2% | -1 | moderate |

## Per-model opportunity (prevalence % + tier)

| waste pattern | opus-4.5 (79%) | sonnet-3.5 (35%) | qwen-32B* (40%,HELD) | opus-4.7 (live) |
|---|---|---|---|---|
| VERIFICATION_GAP | 57% 🟢 | 82% 🟢 | 82% 🟢 | 65% 🟢 |
| SEARCH_WITHOUT_NEW_EVIDENCE | 6% 🔴 | 72% 🟢 | 82% 🟢 | 33% 🟡 |
| PATCH_CHURN | 69% 🟢 | 74% 🟢 | 45% 🟢 | 33% 🟡 |
| REDUNDANT_FILE_REREAD | 57% 🟢 | 67% 🟢 | 0% — | 5% — |
| CONTEXT_BLOAT | 57% 🟢 | 67% 🟢 | 0% — | 5% — |
| STAGNATION | 2% — | 26% 🟡 | 38% 🟡 | 2% — |
| DEPENDENCY_SETUP_DRIFT | 97% ⚪ | 5% ⚪ | 54% ⚪ | 93% ⚪ |
| PREEMPTIVE_HELPER_TOOL_BUILD | 91% ⚪ | 4% ⚪ | 49% ⚪ | 86% ⚪ |
| FILENAME_SEARCH_THRASH | 49% ⚪ | 24% ⚪ | 58% ⚪ | 40% ⚪ |
| FAILED_RECOVERY | 20% 🟡 | 12% 🔴 | 6% 🔴 | 14% 🔴 |
| EDIT_TOOL_MECHANICAL_FAILURE | 7% 🔴 | 8% 🔴 | 23% 🟡 | 2% — |
| REDUNDANT_TEST | 1% — | 11% 🔴 | 4% — | 0% — |
| HELPER_TOOL_FAILURE_LOOP | 2% — | 2% — | 8% 🔴 | 0% — |
| ENVIRONMENT_BLOCKED | 2% — | 2% — | 8% 🔴 | 0% — |
| BUDGET_EXHAUSTION_NONCONVERGENCE | 1% — | 1% — | 8% 🔴 | 1% — |
| PREMATURE_SCRATCH_REPRO | 1% — | 0% — | 0% — | 7% 🔴 |

🟢 HIGH ≥40% · 🟡 MED 15–40% · 🔴 low 5–15% · ⚪ harness-artifact (skip — intervening hurts strong models) · — <5%

\* solver_E (qwen-32B) is the HELD-OUT model — shown for transfer reference only; it never shaped the taxonomy.

## Controller playbook (solver-aware)

- **opus-4.5 / opus-4.7 (strong):** only PATCH_CHURN + REDUNDANT reads/CONTEXT_BLOAT are real opportunities. Intervene rarely (DELAY_EDIT / SUMMARIZE_CONTEXT). Their high helper-build/dep-setup % is the SWE-agent harness, not waste — SKIP.
- **sonnet-3.5 (weak):** top targets SEARCH_WITHOUT_NEW_EVIDENCE (72%) + VERIFICATION_GAP (82%) + emerging STAGNATION (26%). → CONSTRAIN_SEARCH + INCREASE_TARGETED_VERIFICATION.
- **qwen-32B (held-out local):** most distinctive — SEARCH_WITHOUT_NEW_EVIDENCE (82%), STAGNATION (38%, highest), unique EDIT_TOOL_MECHANICAL_FAILURE (23%). Explores endlessly, gets stuck. → CONSTRAIN_SEARCH + ESCALATE_SOLVER on stagnation. (Exactly the transfer signal the holdout was reserved for.)

## Headline
The controller should be **solver-aware**: same trace pattern, different action. Strong models need light touch (patch scope); weak/local models need search discipline + verification. The biggest single discriminator is **SEARCH_WITHOUT_NEW_EVIDENCE** (6% strong vs 72-82% weak).