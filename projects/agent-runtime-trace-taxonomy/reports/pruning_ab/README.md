# Safe Context-Pruning Study — Index

A full empirical study + adversarial falsification of client-side context pruning for SWE-agent on a frontier coding model (Claude opus-4.7). **Final verdict: NEGATIVE_STUDY_RESULT** — large per-call context compression does not translate into reliable task-level cost reduction.

## TL;DR

The candidate method **HYBRID1** (graduated observation pruning) reduces the **per-call prompt by ~40%** — and that win is **REAL** (verified +42.8% mean on clean ledgers). But a 7-phase falsification pass showed the per-call win **does not propagate to task-level cost**:
- Per-call prompt reduction is genuine (~40%, the one win). But paired **task-level cost is ~0% (median) and negative** — the provider prompt cache arbitrages the reduction away (cache-busting).
- The per-task "canary" and "improvement" were **single-sample flukes** — the agent is run-to-run nondeterministic even at temperature=0 (a no-op SHAM control flips 8/10 boundary tasks).
- On **167 held-out tasks**, solve rate is preserved (160=160) but there is **no token saving** and the advantage **does not transfer**.

## Read in this order

| # | document | what it establishes |
|---|----------|--------------------|
| 1 | [EXPERIMENT_PLAN.md](EXPERIMENT_PLAN.md) | original A/B design |
| 2 | [PARETO_FRONTIER_v1.md](PARETO_FRONTIER_v1.md) | ⚠️ SUPERSEDED — submission-proxy "0 regression" claims |
| 3 | [PARETO_FRONTIER_v2_VERIFIED.md](PARETO_FRONTIER_v2_VERIFIED.md) | SWE-bench-graded; "+41.5%, 1 regression" (still per-call) |
| 4 | [PER_TASK_MATRIX.md](PER_TASK_MATRIX.md) | per-task pass/regress map (50 tasks) |
| 5 | **[FINAL_VERDICT.md](FINAL_VERDICT.md)** | **START HERE for the conclusion** — all 8 verdicts |
| 6 | [HYBRID1_FREEZE.md](HYBRID1_FREEZE.md) | Phase 1: frozen method + config hashes |
| 7 | [PARETO_FRONTIER_v3_TASK_LEVEL.md](PARETO_FRONTIER_v3_TASK_LEVEL.md) | Phase 2+5: the +41.5% reverses to neutral/negative |
| 8 | [AA_NOISE_FLOOR.md](AA_NOISE_FLOOR.md) | Phase 3: A/A + SHAM noise floor (the core result) |
| 9 | [FRAGILITY_REPLICATION.md](FRAGILITY_REPLICATION.md) | Phase 4: 0 true fragility, 0 true improvement |
| 10 | [HELDOUT_VALIDATION.md](HELDOUT_VALIDATION.md) | Phase 6: 167 held-out tasks, no transfer |
| 11 | [SAFETY_GATE_EVALUATION.md](SAFETY_GATE_EVALUATION.md) | Phase 7: no gate beats always-C0 |
| 12 | **[CACHE_STABLE_FRONTIER.md](CACHE_STABLE_FRONTIER.md)** | **Follow-up: cache-stable pruning — catastrophe→break-even (+0.6%)** |

## The 8 verdicts (FINAL_VERDICT.md)

```
TASK_LEVEL_COST:      NEUTRAL              AA_NOISE:          DOMINANT
HYBRID1_RESOLUTION:   NONINFERIOR          CANARY:            NOT_SUPPORTED
IMPROVEMENT:          STOCHASTIC_FLIP      HELDOUT_TRANSFER:  DOES_NOT_TRANSFER
SAFETY_GATE:          NO_INCREMENTAL_VALUE PAPER:             NEGATIVE_STUDY_RESULT
```

## Three findings worth keeping

1. **Per-call token reduction ≠ task-level cost reduction** on cached pipelines. Pruning rewrites the prompt prefix → invalidates the provider prompt cache (cache_read:creation collapses 11.8:1 → 0.37:1) → cheap cached tokens replaced by expensive re-created ones. Net cost flat-to-worse.
2. **Frontier coding agents are run-to-run nondeterministic at temperature=0.** 5/10 (C0) to 8/10 (SHAM no-op) boundary tasks flip outcome across identical reps. Any per-task A/B without an A/A noise floor manufactures false effects.
3. **Measurement integrity dominates method choice.** The headline reversed entirely once the ledger contamination + cache-naive averaging were corrected.

## Reproduce

Full apparatus in [`../../harness/pruning_ab/`](../../harness/pruning_ab/) — task-tagged shim, all method implementations, orchestrators, graders, analysis scripts, and a per-method `RUNTIME_CONFIG.json`. See its README for the 3-step replay.

## Raw evidence

- `../../results/pruning_ab/` — graded outcomes (golden-50 + 15 A/A cells + 3 held-out arms), task-level ledger, A/A noise results, held-out outcomes, frontier, safety-gate results, sample task-tagged cost ledgers.
- Apparatus: opus-4.7 via PlugBoard mTLS, SWE-agent 1.1.0, SWE-bench Verified, podman grading, thinking OFF, temp 0.

## Scope & honest caveats

- **Scope:** standard-mode opus-4.7 (a strong, efficient, *cached* frontier model). The one regime where pruning might still win — a **weaker or uncached model** with genuinely redundant context and no cache tax — was not tested and is the natural follow-up.
- **Power:** A/A on 10 boundary tasks × 5 reps; held-out 167 tasks (loss_UB 0.055). Sufficient to reject the saving claim and establish the noise floor; not powered for δ=1% certification.
- A valid negative result. The taxonomy/methodology project is strengthened, not killed: it now correctly detects and explains why this intervention fails.
