# FINAL VERDICT — Context-Pruning Falsification Pass

**Status: COMPLETE.** All 7 phases executed. The result is a clean, well-evidenced **NEGATIVE_STUDY_RESULT**.

## Executive summary

HYBRID1 has **one real, verified win**: it reduces the **per-call prompt by ~40%** (+42.8% mean / +38.7% median, confirmed on clean task-tagged ledgers — the original "+41.5%" was real-but-on-a-contaminated-ledger). **But this per-call win does NOT propagate to task-level cost.** Under correct paired task-level accounting, HYBRID1 saves **~0% (median −0.8% to −2.5%)** of tokens and **costs more** (median cost −52% on held-out) — because the prompt-cache-busting tax converts cheap cached tokens into expensive re-created ones, arbitraging the per-call reduction away. The per-task "universal canary" (pylint-4551) and "universal improvement" (pytest-6197) were **single-sample artifacts** — on repeated runs the identity baseline fails pylint-4551 5/5 times and solves pytest-6197 5/5 times, with zero pruning. The agent's **run-to-run nondeterminism (5/10 boundary tasks flip at temp=0)** fully accounts for every per-task "pruning effect." On 167 held-out tasks, HYBRID1 preserves solve rate exactly (160=160) with regressions balanced by improvements — the signature of noise, not damage.

**Bottom line: large per-call context compression does not translate into reliable task-level cost reduction for frontier coding agents.**

## Evidence chain (all 7 phases)

| phase | finding | artifact |
|-------|---------|----------|
| 1 FREEZE | HYBRID1 locked: hybrid_m7_agg2 @6c9ab8b6, opus-4.7, temp0, thinking OFF, SWE-agent 1.1.0 | HYBRID1_FREEZE.md |
| 2 ACCOUNTING | task-tagged shim v2; old ledger contaminated (1910 vs 1190 calls) | task_level_ledger.jsonl |
| 3 A/A NOISE | C0 5/10, **SHAM 8/10**, HYBRID1 7/10 flip across 5 reps (SHAM no-op flips MOST) | AA_NOISE_FLOOR.md, aa_noise_results.json |
| 4 REPLICATION | 0 TRUE_FRAGILITY, 0 TRUE_IMPROVEMENT, 9/10 INHERENTLY_UNSTABLE | FRAGILITY_REPLICATION.md, interesting_task_repeats.jsonl |
| 5 TASK FRONTIER | every method negative mean saving; HYBRID1 median −2.5% sent | PARETO_FRONTIER_v3_TASK_LEVEL.md, frontier_v3.json |
| 6 HELD-OUT | 167 tasks: solve 160=160, median saving −0.8%, cost −52%, loss_UB 0.055 | HELDOUT_VALIDATION.md, heldout_outcomes.jsonl |
| 7 SAFETY GATE | no gate beats always-C0; no saving frontier to protect | SAFETY_GATE_EVALUATION.md, safety_gate_results.json |

## HARD KILL RULES — final status

| # | rule | status |
|---|------|--------|
| 1 | total task-level tokens do not improve | **TRIGGERED** (held-out median −0.8%) |
| 2 | output/call growth cancels prompt reduction | **TRIGGERED** (cache-bust, held-out cost −52%) |
| 3 | held-out excess regression > A/A noise floor | NOT triggered (regression within noise; loss_UB 0.055) |
| 4 | golden-50 advantage disappears held-out | **TRIGGERED** (the +41.5% artifact does not transfer) |
| 5 | safety gating no better than length-only | **TRIGGERED** (no gate beats always-C0; no frontier) |
| 6 | result depends on few unstable tasks/artifacts | **TRIGGERED** (entire per-task signal is run-to-run noise) |

**5 of 6 hard-kill rules triggered.** (Rule 3 not triggered only because HYBRID1 is *noninferior* on resolution — it doesn't actively break tasks beyond noise; it simply provides no benefit.)

## THE 8 REQUIRED VERDICTS

```
TASK_LEVEL_COST_VERDICT:      NEUTRAL
  (HYBRID1 has a REAL, verified per-call prompt reduction of +42.8% mean / +38.7% median (clean
   task-tagged ledgers) — the one genuine win. But it does NOT propagate to task-level cost:
   paired median tokens_sent −2.5%, held-out median −0.8%, cost median −52% (cache-busting).
   The per-call win is arbitraged away by the provider prompt cache. Task-level: NEUTRAL.)

AA_NOISE_VERDICT:             DOMINANT
  (C0 identity flips 5/10, SHAM 8/10, HYBRID1 7/10 across 5 identical reps. SHAM (a no-op code
   path, byte-identical messages) flips MORE than HYBRID1 -> instability is pipeline nondeterminism,
   provably independent of pruning. The noise floor dominates every per-task "pruning effect.")

HYBRID1_RESOLUTION_VERDICT:   NONINFERIOR
  (held-out solve rate 160/167 = C0 160/167, net 0; 4 regressions balanced by 4 improvements;
   regression loss_UB 0.055. HYBRID1 does not break tasks beyond the noise floor.)

CANARY_VERDICT:               NOT_SUPPORTED
  (pylint-4551 is resolved 0/5 by the fresh identity baseline — a task the agent reliably FAILS,
   not a pruning fragility. The original single pass was the outlier. No task meets TRUE_PRUNING_FRAGILITY.)

IMPROVEMENT_VERDICT:          STOCHASTIC_FLIP
  (pytest-6197 is resolved 5/5 by the fresh identity baseline — a task the agent reliably SOLVES,
   not a pruning benefit. No task meets TRUE_PRUNING_IMPROVEMENT.)

HELDOUT_TRANSFER_VERDICT:     DOES_NOT_TRANSFER
  (the golden-50 "+41.5% saving" does not transfer; held-out task-level token saving is ~0 median /
   negative mean. What transfers is the null: solve rate preserved, no cost benefit.)

SAFETY_GATE_VERDICT:          NO_INCREMENTAL_VALUE
  (no gate — length, frozen, even oracle — beats always-C0 on the saving/regression frontier,
   because HYBRID1 has no positive task-level saving to protect. Admission control has nothing to admit.)

PAPER_VERDICT:                NEGATIVE_STUDY_RESULT
  ("Large per-call context compression does not translate into reliable task-level cost reduction
   for frontier coding agents." A valid, defensible negative result per the protocol.)
```

## What is publishable (the honest contribution)

This is a **rigorous negative result with a mechanistic explanation** — more valuable than the false positive it replaces:

1. **Per-call token reduction ≠ task-level cost reduction** on cached frontier-agent pipelines. Client-side pruning rewrites the prompt prefix and **invalidates the provider's prompt cache** (cache_read:cache_creation collapses 11.8:1 → 0.37:1), so cheap cached tokens are replaced by expensive re-created ones. The net task cost is flat-to-worse despite fewer raw prompt tokens per call.

2. **Frontier-agent success is run-to-run nondeterministic even at temperature=0** (5/10 boundary tasks flip). Any A/B that attributes single-sample per-task outcome changes to an intervention — without an A/A noise floor — will manufacture false "regressions" and "improvements." This is a methodological warning for the whole agent-evaluation field.

3. **Measurement integrity matters more than the method.** The original +41.5% came from a contaminated ledger + cache-naive per-call averaging. The correct metric (paired task-level total cost) reverses the conclusion.

## Methodological lessons (preserved for the project)
- Always task-tag the cost ledger; never pool per-call averages across runs.
- Always measure true prompt = input + cache_read + cache_creation, AND account for the cache-hit-rate shift the intervention causes.
- Always establish an A/A + SHAM noise floor before attributing per-task outcome changes.
- Always validate on a held-out set selected without inspecting the candidate's outcomes.
- Grade with the real test harness; submission ≠ resolution.

The scientific project (taxonomy + safe-pruning study) is NOT killed by this negative result — it is **strengthened**: the methodology now correctly detects that this particular intervention (client-side observation pruning on a cached frontier agent) does not deliver, and explains precisely why.
