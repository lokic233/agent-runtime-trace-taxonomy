# Phase 5 — Oracle Gap & Controller Justification

**Question:** Is a trace-based controller justified — i.e., can a deployable policy beat the best static method?

## Total effective cost over 49 tasks (auto-generated from controller_policies.json)

| policy | total eff-cost | saving vs C0 | deployable? |
|--------|---:|---:|:--:|
| always_C0 | 5,507,153 | +0.0% | — |
| always_LINEDEDUP | 5,184,359 | +5.9% | ✅ |
| **always_GENTLE6K** | 4,951,455 | **+10.1%** | ✅ best static |
| **oracle (post-hoc per-task min)** | 4,019,692 | **+27.0%** | ❌ uses outcomes |
| dup>0.20→LD (Tier-1 policy) | 5,002,202 | +9.2% | ✅ |
| dup>0.25→LD (Tier-1 policy) | 4,997,664 | +9.3% | ✅ |
| dup>0.30→LD (Tier-1 policy) | 5,120,094 | +7.0% | ✅ |

## The decisive result
- **A large oracle gap exists: +27.0% (oracle) vs +10.1% (best static).** Real heterogeneity — a perfect per-task picker would save ~3× the best static method. The treatment effects ARE heterogeneous.
- **But no deployable trace policy closes it.** The best dup-threshold policy (+9.3%) is **worse than simply always using GENTLE6K (+10.1%).** The Tier-1 trace signal routes tasks no better than a constant choice.

## Decision (per mission rule)
> "If the oracle gap is substantial but the deployable policy cannot close it, report that trace signals are insufficient."

**The oracle gap is substantial (+27% vs +10%), but the deployable dup-threshold policy (+9.3%) does not beat the best static method (+10.1%).** → **Trace signals are insufficient to support a controller that improves on the best static method.**

## Caveats on the comparison
- This is **cost-only**; quality/regression budget not yet imposed (Phase 6). Under a regression budget GENTLE6K's +10.1% must be discounted for its regressions (whose attribution is unresolved).
- 49 tasks, single run each (development data) — the threshold was even tuned on these same tasks (optimistic for the policy, yet it still loses). On untouched data it would likely do no better.
- Oracle uses post-hoc cost only (not quality); a quality-aware oracle may differ.

## Verdict
**ORACLE_GAP: SUPPORTED (large gap exists, +27%).**
**DEPLOYABLE_CONTROLLER_VALUE: NOT_SUPPORTED** — no Tier-1 trace policy beats the best static method, even with in-sample threshold tuning.
