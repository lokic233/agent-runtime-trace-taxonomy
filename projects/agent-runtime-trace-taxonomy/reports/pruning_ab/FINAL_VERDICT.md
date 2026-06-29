# FINAL VERDICT — Context-Pruning Falsification Pass

**Status: INTERIM (Phases 1,2,5,7-dev complete; Phases 3,4,6 empirical runs in progress)**
Updated as A/A noise floor + replication + held-out validation land.

## Executive summary

The headline **HYBRID1 "+41.5% token saving"** does **not** survive falsification. Recomputed on paired task-level totals (the cost metric that matters), HYBRID1's median saving is **−2.5%** — it does **not** reduce task-level cost. The +41.5% was an artifact of (1) a contaminated, non-task-tagged ledger and (2) the prompt-cache-busting tax. The "universal canary" and "universal improvement" claims rest on **1 regression and 1 improvement** on golden-50 — too sparse to distinguish from noise until the A/A floor lands.

This is trending toward a **NEGATIVE_STUDY_RESULT**, which the protocol explicitly accepts as valid.

## Evidence by phase

### Phase 1 — FREEZE ✅
HYBRID1 frozen: `hybrid_m7_agg2` sha256 `6c9ab8b6…`, git `859cbc4`, opus-4.7, temp 0, thinking OFF, SWE-agent 1.1.0. See HYBRID1_FREEZE.md.

### Phase 2 — Task-level accounting ✅
Built + validated task-tagged shim v2 (PR-fingerprint tagging, 0 UNKNOWN on real runs). Full per-call schema: activation (changed/chars_removed/first_changed_index) + usage + latency. The old ledger was contaminated (1910 pooled calls vs 1190 actual C0 calls).

### Phase 5 — True frontier (task-level) ✅ (golden-50)
| method | per-call claim | **paired median Δsent** | **paired median Δcost** |
|--------|---:|---:|---:|
| HYBRID1 | +41.5% | **−2.5%** | **−2.2%** |
| AGG3 | +50.6% | −1.2% | −48.8% |
| M7 | +37.0% | −4.3% | −41.0% |

Every method has negative MEAN task-level saving. HYBRID1 cost distribution: cheaper on 24 tasks, dearer on 26, catastrophic cache-bust outliers (pylint-6528 −457%).

### Phase 7 — Safety gate (dev-data) ✅
Length-only gate **falsified in-sample**: the 1 regression (pylint-4551, 69 obs) is NOT the longest trajectory — 3 safe tasks have 76-77 obs. Label sparsity (1/50) prevents fitting a generalizable gate.

### Phase 3 — A/A + SHAM noise floor 🔄 RUNNING
C0×5 + SHAM×5 + HYBRID1×5 on 10 interesting tasks. Establishes whether 1 flip exceeds run-to-run noise.

### Phase 4 — Interesting-task replication 🔄 RUNNING
Classifying pylint-4551 (canary?) and pytest-6197 (improvement?) as TRUE_PRUNING_* vs INHERENTLY_UNSTABLE vs NO_OP vs STOCHASTIC.

### Phase 6 — Held-out validation ⏳ PENDING (set built: 167 tasks)
Repo-balanced, stratified, integrity-preserved. Runs C0/SHAM/HYBRID1 after Phase 3+4.

## HARD KILL RULES — current status

| # | rule | status |
|---|------|--------|
| 1 | total task-level tokens do not improve | **TRIGGERED** (median −2.5%) |
| 2 | output/call growth cancels prompt reduction | **TRIGGERED** (cache-bust, 26/50 dearer) |
| 3 | held-out excess regression > A/A floor | PENDING (Phase 3+6) |
| 4 | golden-50 advantage disappears held-out | PENDING (Phase 6) — but there's no advantage to lose |
| 5 | safety gating no better than length-only | **TRIGGERED in-sample** (length-only falsified) |
| 6 | result depends on few unstable tasks/artifacts | **TRIGGERED** (1 reg, 1 imp; cache outliers dominate) |

**4 of 6 kill rules already triggered** on existing evidence.

## VERDICTS

```
TASK_LEVEL_COST_VERDICT:      NEUTRAL   (median −2.5% sent / −2.2% cost; not a saving, not a large loss)
AA_NOISE_VERDICT:             PENDING   (Phase 3 running)
HYBRID1_RESOLUTION_VERDICT:   PENDING   (golden-50: noninferior 48/48; held-out pending)
CANARY_VERDICT:               PENDING   (Phase 4 running; provisional: NOT_SUPPORTED — 1 flip)
IMPROVEMENT_VERDICT:          PENDING   (Phase 4 running; provisional: STOCHASTIC_FLIP — 1 flip)
HELDOUT_TRANSFER_VERDICT:     PENDING   (Phase 6; set built, runs after 3+4)
SAFETY_GATE_VERDICT:          INCONCLUSIVE → likely NO_INCREMENTAL_VALUE (length-only falsified in-sample)
PAPER_VERDICT:                NOT_READY → trending NEGATIVE_STUDY_RESULT (4/6 kill rules triggered)
```

**The honest current read:** client-side context pruning, as implemented here (HYBRID1 on opus-4.7), does **not** create reliable task-level cost reduction on a frontier coding agent. The per-call compression is real but is cancelled by prompt-cache invalidation and trajectory-path changes. Final verdicts pending the noise floor + held-out runs, which will either confirm NEGATIVE_STUDY_RESULT or (less likely on current evidence) reveal a defensible task-selective benefit.
