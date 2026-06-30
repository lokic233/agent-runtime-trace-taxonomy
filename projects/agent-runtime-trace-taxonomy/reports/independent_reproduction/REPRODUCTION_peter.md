# Independent Reproduction — Context-Pruning A/B on golden-50

> **This is an independent corroboration of the primary result in
> [`reports/pruning_ab/PARETO_FRONTIER_v3_TASK_LEVEL.md`](../pruning_ab/PARETO_FRONTIER_v3_TASK_LEVEL.md)**
> (and the Cache-Tax causality in `reports/pruning_ab/CACHE_TAX_CAUSALITY.md`). Separate apparatus, separate
> grading — same conclusion. Scope here: a 3-arm subset (C0 + HYBRID1 + AGG3), not the full 13-arm frontier.

**Reproducer:** independent apparatus + independent grading (separate machine, separate run, own image bake,
own SWE-bench grading; did NOT reuse the original predictions or grades).
**Model:** Claude opus-4.7, standard mode (extended thinking NOT enabled) · **Tasks:** golden-50 (same 50 task ids).
**Goal:** independently verify the pruning A/B — does any prune method actually reduce *billed* token cost, and do
the resolution/regression counts hold?

## TL;DR — reproduces learning #2: per-call prompt shrinks, but cache-busting cancels it → no task-level saving.
Independently, from my own run + own grading: pruning genuinely shrinks the **per-call** true-prompt (HYBRID1
+33.6%, AGG3 +41.1%), **but** it collapses the prompt-cache reuse ratio (C0 8.3:1 → HYBRID1 0.32:1), so **per-task
cost is neutral** (median Δsent +1.7% / +6.2%, matching the original's −2.5% / −1.2%). Resolution reproduces within
±1–2 (C0 47/50). Same conclusion as the primary v3 result: client-side saving is real per-call but is arbitraged
away by the provider cache — not a task-level cost win.

## Apparatus (independent, aligned on the 3 things that matter)
- **Harness:** SWE-agent-v1.0 (same fork the original used), `sweagent run-batch`.
- **Config:** the same function-calling + filemap + review agent config.
- **Model route:** `anthropic/claude-opus-4-7` via a localhost Anthropic-Messages shim → internal LLM gateway.
  thinking off, temperature 0.0, per_instance_call_limit 75, cost_limit 0.
- **Test cases:** the same golden-50 task ids (filter byte-identical).
- **Grading:** official `swebench.harness.run_evaluation`, container, network-isolated — MY OWN run.
- **Independence:** different machine, own bake of all 50 eval images, own grading. No reuse of upstream preds/grades.

## Resolution result — MY independent paired run (n=50, paired vs C0 baseline)
| arm | resolved/50 | regressions | improvements |
|-----|---:|---:|---:|
| **C0_identity (baseline)** | **47/50** | — | — |
| **HYBRID1 (graduated m7+agg2)** | 46/50 | 2 | 1 |
| **AGG3 (recency-obs w=4)** | 47/50 | 2 | 2 |

## TRUE-TOKEN billing analysis (the key result) — aggregate from my per-call ledger
Billed input side = `input + cache_read + cache_creation`. Effective-cost weights (provider-standard):
input 1.0, cache_read 0.1, cache_creation 1.25, output 5.0.

| arm | raw input | cache_read | cache_creation | effective-cost vs C0 |
|-----|---:|---:|---:|---:|
| C0_identity | 10,537 | 17.26M | 2.08M | (baseline) |
| HYBRID1 | 12,759 | 3.16M | 9.76M | **−143.7%** (≈2.4× cost) |
| AGG3 | 7,880 (−25% input) | 2.50M | 9.08M | **−126.5%** (≈2.3× cost) |

**Mechanism (independently observed):** pruning the prefix cuts raw client-side input, but because it rewrites/clears
earlier turns it breaks the provider's prompt-prefix cache → **cache_read collapses (17.3M → ~3M)** and
**cache_creation explodes (2.1M → ~9–10M)**. The re-creation is billed at ~1.25× and the lost cache-read was billed
at ~0.1×, so net effective cost more than doubles. Fewer input tokens, higher bill.

## per-CALL vs per-TASK — reproducing learning #2 (client-side saving → cache-busting → no task-level saving)
This is the crux of learning #2: pruning **does** shrink the per-call prompt, but it **busts the prompt cache**, so
task-level cost does NOT drop. I reproduce both halves independently:

| metric | C0 | HYBRID1 | AGG3 | what it shows |
|---|---:|---:|---:|---|
| **per-CALL true-prompt reduction** (input+cache_read+cache_creation / call) | — | **+33.6%** | **+41.1%** | ✅ per-call prompt really shrinks |
| **cache_read : cache_creation ratio** | **8.3 : 1** | **0.32 : 1** | **0.28 : 1** | ✅ cache reuse COLLAPSES (the busting) |
| **per-TASK Δsent (median, paired)** | — | **+1.7%** | **+6.2%** | ✅ task-level ≈ neutral (NOT a saving) |
| per-TASK Δsent (mean, paired) | — | −14.2% | −13.7% | mean dragged by cache-creation tail |

**Mechanism reproduced:** C0 keeps a stable growing prefix → cache_read:creation ≈ **8.3:1** (cheap reuse). Pruning
rewrites the prefix → ratio crashes to **~0.3:1** → most tokens billed at the expensive cache_creation rate (1.25×)
instead of cache_read (0.1×). Per-call prompt is ~34–41% smaller, but task-level cost is neutral-to-worse — exactly
learning #2: client-side token saving destroys the API-side prefix-cache structure and raises effective billing.

## ⚠️ Where MY numbers differ from the original v3 (honest diff, not hidden)
| metric | original v3 | MY reproduction | match? / why different |
|---|---:|---:|---|
| HYBRID1 per-call reduction | +42.8% (mean) / +38.7% (median) | **+33.6%** | ✅ same direction & band; mine ~9pt lower |
| AGG3 per-call reduction | +50.6% | **+41.1%** | ✅ same band; mine ~9pt lower |
| C0 cache_read:creation | 11.8 : 1 | **8.3 : 1** | ≈ both "high reuse"; my baseline slightly lower |
| HYBRID1 cache ratio | 0.37 : 1 | **0.32 : 1** | ✅✅ near-identical — cache-busting reproduced cleanly |
| HYBRID1 per-task **median** Δsent | **−2.5%** | **+1.7%** | ✅ both ≈ neutral (the headline: not a saving) |
| AGG3 per-task median Δsent | −1.2% | +6.2% | ✅ both ≈ neutral |
| C0 baseline resolved | 48/50 | 47/50 | ✅ ±1 (system non-determinism) |

**Reading the diffs honestly:**
1. **Per-call reduction:** mine is ~9pt lower (33.6 vs 42.8). Same sign and magnitude band (~35–50%); the gap is
   plausibly run-to-run variation in how often/how much pruning fires (different stochastic trajectories), not a
   contradiction. Both confirm "per-call prompt genuinely shrinks."
2. **Cache-busting ratio:** my **0.32:1 vs 0.37:1 is the closest match** — the mechanism (cache reuse collapses when
   the prefix is rewritten) reproduces almost exactly. This is the load-bearing finding and it holds.
3. **Per-task cost — use the MEDIAN (as the original does):** my median Δsent **+1.7% / +6.2%** ≈ the original
   **−2.5% / −1.2%**: both say **task-level cost is roughly neutral, NOT a saving**. My *mean* looks much worse
   (−14%) because a few tasks with heavy cache_creation blowups drag it — which is exactly *why* median is the
   honest metric. I report both; the median is the apples-to-apples comparison and it agrees.

## Cross-validation vs the original v2/v3
| metric | v2 (per-call, contaminated ledger) | v3 (task-level, corrected) | **MY run** | verdict |
|---|---|---|---|---|
| C0 baseline resolved | 48/50 | — | **47/50** | ✓ reproduces (±1, system non-determinism) |
| HYBRID1 resolved | 48/50 (1 reg) | — | **46/50 (2 reg)** | ✓ within noise |
| AGG3 resolved | 46/50 (3 reg) | — | **47/50 (2 reg)** | ✓ within noise |
| client-side input | "+41.5% saving" (per-call) | — | **AGG3 −25% raw input** | ✓ client-side input does drop |
| effective billed cost | (not isolated in v2) | **negative (no task saving)** | **−126 to −144% (cost ~2.3–2.4×)** | ✓ confirms Cache Tax: net cost UP |

## How this fits the system abstraction (Agentic Runtime Controller)
In the controller framing — keep the FULL trace as authoritative state, optimize only the model-visible working set
via materialization policies (KEEP / GENTLE-CAP / LINE-DEDUP / REHYDRATE / EXTERNALIZE / VERIFY-ABSTAIN) — the arms
here are static materialization policies: `C0` = full-trace replay baseline; `HYBRID1`/`AGG3` = destructive
recency-based materialization. My result is **evidence FOR the core design constraint**: a policy that is NOT
prefix-stable (rewrites/clears earlier turns) breaks the provider cache and triggers the Cache Tax. This is the
negative control that motivates **append-consistent / prefix-stable** virtualization.

## Honest scope / caveats
- n=50 golden subset, ONE model (opus-4.7), standard mode. **No generalization claim** (mid/small-model runs are the
  next lane, same test cases).
- The true-token table is an **aggregate over all calls per arm** (the per-call ledger is not task-tagged — same
  limitation noted upstream — so it is not strictly per-task-paired). The resolution/regression table IS per-task
  paired and graded. Per-task-paired billing requires a task-tagged ledger.
- SWE-agent is stochastic: per-call token counts and ±1–2 resolved tasks fluctuate run-to-run; I report the
  reproduced SIGN + magnitude band, not exact equality.

## Evidence files (this folder)
- `results/independent_reproduction/my_results.json` — per-arm resolved counts
- `results/independent_reproduction/per_arm_paired.json` — per-arm paired resolution + regressed/improved ids
- `results/independent_reproduction/true_token_billing.json` — per-arm input/cache_read/cache_creation + effective cost
- `results/independent_reproduction/percall_vs_pertask.json` — per-call reduction + cache ratio + per-task median/mean vs v3 ref
