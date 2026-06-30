# Phase 0 — Causal Data Audit & Freeze

**Commit:** `bb43b49612760b56a3f8d620fbffcae9dc347bf6` · **prune_methods.py sha256:** `cb06efb6…` · Generated from `causal_data_manifest.json` + `report_reconciliation.json` (no hand-typed numbers).

## Frozen treatment set (no new methods this mission)
| method | role | task-tagged ledger | grade (completed/resolved /50) |
|--------|------|:--:|:--:|
| C0_identity | baseline | ✅ 50 tasks | 49 / 46 |
| SHAM | no-op control | only A/A reps (10 tasks) | — |
| LINEDEDUP_e4 | treatment | ✅ 50 tasks | 49 / 44 |
| GENTLE6K_stable | treatment | ✅ 49 tasks | 48 / 45 |
| HYBRID1_m7_agg2 | cache-bust control | ❌ pooled/contaminated | 50 / 48 |
| RETRIEVREF_e4 | near-neutral control | ✅ 50 tasks | 49 / 45 |

## A/A repeated-measures data (the causal repeated-runs)
**5 reps each of C0_identity, SHAM, HYBRID1_m7_agg2 on the 10 interesting tasks** — all graded + task-tagged. This is the ONLY repeated-run data and is essential for estimating P(success|treat)−P(success|C0) per the causal rules (instead of single-run flip deletion).

## Canonical baseline decision
- **For E3/E4 cost & resolution pairing:** stable tagged C0 (`logs/stable/ledger_C0_identity.jsonl` + `grade_C0_identity.json`), **46/50 resolved**.
- **For A/A repeated analysis:** phase34 C0 reps 1–5.
- The original `results/pruning_ab/grade_C0_identity.json` (48/50) is a **different run** — retained for v2 provenance only, NOT used for causal pairing.

## Reconciled contradictions (across the 5 prior reports)

### 1. C0 baseline: 48 vs 46 resolved
**Two different C0 runs.** Original full_C0 = 48/50 (v2). Stable tagged C0 = 46/50 (E3/E4 canonical). ~2-task run-to-run variance. **Canonical = 46/50.**

### 2. LINEDEDUP regressions: 5 vs 2
The "5" was scored at **46/50 completed** — 3 were incomplete tasks misread as regressions. **Full-49 reconstruction vs stable C0 = 2 regressions** (pylint-6386, sympy-19040). Authoritative = 2. *Per causal rules, these 2 are flips with UNRESOLVED single-run attribution — NOT dismissed as noise.*

### 3. LINEDEDUP saving: +24% vs +6.3%
The +24% was **optimistic early-completion sampling** (big-saver tasks finished first). **Full-50 = +6.3% effective-cost.** Authoritative = +6.3%.

### 4. ⚠️ RETRACTION: the "real regression = 0 (A/A noise)" framing
Earlier reports computed "real regressions" by **excluding tasks that flip under C0 A/A**. **This is scientifically invalid and is hereby RETRACTED.** A task flipping under C0 does not prove a treatment has zero added effect on it. Going forward:
- Single paired-run flips → **"unresolved causal attribution"**, not "noise."
- Where A/A repeated runs exist → estimate P(success|treat)−P(success|C0) directly.
- Raw regression counts (LINEDEDUP 2, GENTLE6K 1) **stand as-is**; all "real reg = 0" claims withdrawn.

## Superseded reports
The following retain provenance but their disputed numbers are superseded by this audit + the canonical index (to be maintained in CANONICAL_INDEX.md):
- REGRESSION_BUDGET_PARETO.md (used +24% partial, "noise" framing)
- parts of REGRESSION_BUDGET_FINAL.md and EXPERIMENT4_FRONTIER.md (the "0 real regression" language)

## Data sufficiency flags
- **Cost CATE:** 50 paired tasks per treatment (single run each) — adequate for exploratory heterogeneity, **UNDERPOWERED** for high-dimensional causal forests.
- **Success CATE:** only 10 tasks have repeated runs (5×) — repeated-measures success estimation limited to these 10.
- **SHAM:** only on the 10 interesting tasks — usable as negative control there, not genome-wide.
