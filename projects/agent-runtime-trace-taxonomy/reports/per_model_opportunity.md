# Improvement-Opportunity Table (REAL semantic labels)

**Generated:** 2026-06-29 · from full Stage-B annotation (clean cohort: opus-4.7/4.5/sonnet-3.5).

## Executive Summary

We annotated **2,000 SWE-agent traces** (4 models × 500) with 2 independent annotators + adjudicate-on-disagreement under the frozen v1 waste taxonomy (16 labels), then ranked each waste pattern by *improvement opportunity* = prevalence × capability-gap (how much more the weak model does it than the strong one), penalizing harness artifacts.

**Top finding — three waste patterns are the real capability discriminators** (weak sonnet-3.5 vs strong opus), and they're where a runtime controller has the most leverage:

| Rank | Waste pattern | sonnet-3.5 | opus | what to do |
|------|---------------|-----------:|-----:|-----------|
| 1 | **EDIT_TOOL_MECHANICAL_FAILURE** | 32% | 7-12% | detect repeated edit-tool errors → switch edit strategy |
| 2 | **FAILED_RECOVERY** | 24% | 5-8% | loops on failing tests → ESCALATE_SOLVER |
| 3 | **BUDGET_EXHAUSTION** | 17% | 0-8% | runs out of budget → earlier escalation |
| 4 | **VERIFICATION_GAP** | 14% | 0.4% | submits unverified → INCREASE_TARGETED_VERIFICATION |

**Second finding — three "high-prevalence" patterns are HARNESS ARTIFACTS, not waste.** CONTEXT_BLOAT, HELPER_TOOL_FAILURE_LOOP, PREEMPTIVE_HELPER_TOOL_BUILD are ~13-17% in opus-4.5's live-SWE-agent scaffold but **near-zero in opus-4.7's classic scaffold** — same model family, different harness. Annotation proved these are scaffold behaviors; a controller intervening on them would fix the harness, not the agent. **Skip them.**

**Controller takeaway:** be **solver-aware**. Weak/local models need verify-and-recover discipline (targets 1-4 above); strong models need only light patch-scope limits. The same trace pattern means different things at different capability tiers.

**Honesty line:** these are *observed prevalences + heuristic opportunity*, NOT proven efficacy. Confirming an intervention actually helps needs paired config outcomes (`PARETO_POLICY_DATA_VERDICT = NOT_EMPIRICALLY_GROUNDED`). The open-weight Skywork-32B cohort is reported separately (`per_model_analysis.md`), not mixed into this clean-cohort ranking.

---


> ⚠️ HEURISTIC opportunity, NOT proven efficacy. Tier = prevalence + capability-gap (weak−strong on clean cohort) + harness-penalty. Proving an intervention HELPS still needs paired config outcomes → PARETO_POLICY_DATA_VERDICT = NOT_EMPIRICALLY_GROUNDED. Now computed on SEMANTIC labels (annotated), upgrading the earlier deterministic-proxy version.

## Clean-cohort opportunity (opus-4.7/4.5/sonnet-3.5)

| tier | waste label | clean avg % | weak−strong gap | read |
|------|-------------|------------:|----------------:|------|
| 🟢 HIGH | EDIT_TOOL_MECHANICAL_FAILURE | 17.0% | +25.0 | strong weak-model discriminator |
| 🟢 HIGH | FAILED_RECOVERY | 12.3% | +15.4 | strong weak-model discriminator |
| 🟢 HIGH | PATCH_CHURN | 12.2% | +5.2 | capability-linked |
| 🟢 HIGH | BUDGET_EXHAUSTION_NONCONVERGENCE | 8.2% | +17.0 | strong weak-model discriminator |
| 🟡 MED | PREMATURE_SCRATCH_REPRO | 6.3% | +13.8 | capability-linked |
| 🟡 MED | VERIFICATION_GAP | 4.8% | +13.4 | capability-linked |
| 🟡 MED | DEPENDENCY_SETUP_DRIFT | 4.4% | +7.4 | capability-linked |
| 🟡 MED | ENVIRONMENT_BLOCKED | 4.1% | +2.4 | moderate |
| 🟡 MED | REDUNDANT_FILE_REREAD | 3.5% | +5.8 | capability-linked |
| 🔴 LOW | CONTEXT_BLOAT | 6.3% | -15.6 | systemic/strong-side |
| 🔴 LOW | HELPER_TOOL_FAILURE_LOOP | 4.6% | -12.8 | systemic/strong-side |
| 🔴 LOW | STAGNATION | 3.5% | +3.8 | moderate |
| 🔴 LOW | SEARCH_WITHOUT_NEW_EVIDENCE | 3.2% | +3.4 | moderate |
| 🔴 LOW | FILENAME_SEARCH_THRASH | 3.0% | +4.8 | moderate |
| 🔴 LOW | PREEMPTIVE_HELPER_TOOL_BUILD | 2.5% | -7.6 | harness artifact — skip |
| 🔴 LOW | REDUNDANT_TEST | 2.1% | -2.0 | systemic/strong-side |

## The high-opportunity targets (real labels confirm the proxy story + sharpen it)
- **EDIT_TOOL_MECHANICAL_FAILURE** (sonnet 32% vs opus 7%, gap +25): the single biggest capability discriminator. Weak models fail the edit tool (whitespace/match) and retry — a controller could detect repeated edit-tool errors and switch edit strategy.
- **VERIFICATION_GAP** (sonnet 13.8% vs opus 0.4%, gap +13): weak models submit without verifying. → INCREASE_TARGETED_VERIFICATION.
- **FAILED_RECOVERY** (sonnet 24% vs opus 8%, gap +15): weak models loop on failing tests without converging. → ESCALATE_SOLVER.
- **BUDGET_EXHAUSTION_NONCONVERGENCE** (sonnet 17% vs opus-4.5 0%): weak models run out of budget. → earlier escalation.

## What to SKIP (harness artifacts, confirmed by real labels)
- CONTEXT_BLOAT, HELPER_TOOL_FAILURE_LOOP, PREEMPTIVE_HELPER_TOOL_BUILD are concentrated in opus-4.5's live-SWE-agent scaffold (16.6%/13.2%/7.6%) and near-ZERO in opus-4.7's classic scaffold — proving they're scaffold-conditioned, not model waste. Intervening on them would target the harness, not the agent.

## Controller takeaway (solver-aware)
Weak/local models: target EDIT_TOOL_MECHANICAL_FAILURE + VERIFICATION_GAP + FAILED_RECOVERY (verify-and-recover discipline). Strong models: light touch — mainly PATCH_CHURN scope limits. Same trace pattern, different action.
