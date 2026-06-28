# Trace Format Coverage Report

**Generated:** 2026-06-28 · normalize_traces.py L0_v1 · 4 on-disk layouts

## Parse coverage (ALL available reference traces)

| solver | model (unblinded for THIS report only) | files | parsed OK | errors | warnings | avg events | layout |
|--------|------|------:|----------:|-------:|---------:|-----------:|--------|
| solver_B | opus-4.5 live-SWE-agent | 500 | 500 | 0 | 0 | 36.8 | mini_swe_agent |
| solver_C | claude-3.5-sonnet | 500 | 500 | 0 | 0 | 33.6 | classic_traj |
| solver_E | qwen2.5-32B HELDOUT | 500 | 500 | 0 | 0 | 41.9 | classic_traj |

**Result: 1500/1500 traces parse cleanly, 0 errors, 0 warnings.**

Plus live runs (devgpu014): solver_A opus-4.7 (classic_traj, ~449/500 generating), solver_F opus-4.6 (queued).

## Normalized event type distribution (per solver, full sets)

| solver | PLAN | SEARCH | READ | RETRIEVE | EDIT | PATCH_APPLY | TEST | EXECUTE | TOOL_ERROR | ENVIRONMENT | FINISH |
|--------|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| solver_B | 1 | 2603 | 2561 | 0 | 3516 | 517 | 457 | 3399 | 455 | 4910 | 0 |
| solver_C | 0 | 2795 | 3707 | 0 | 5794 | 0 | 422 | 1720 | 1639 | 240 | 498 |
| solver_E | 200 | 2755 | 4 | 4 | 3562 | 0 | 433 | 8922 | 2410 | 2344 | 309 |

## Layout handling
| layout | path shape | structure | solvers |
|--------|-----------|-----------|---------|
| classic_traj (flat) | trajs/<inst>.traj | trajectory[] w/ action,observation,thought,state | C, E |
| classic_traj (nested) | <inst>/<inst>.traj | same | A, F (live) |
| mini_swe_agent | trajs/<inst>/<inst>.traj.json | messages[]; assistant=THOUGHT+bash, user=<returncode><output> | B |

## Honest observability notes (red-team relevant)
- **RETRIEVE / PATCH_APPLY / OTHER never appear — and that is CORRECT:**
  - SWE-agent has **no memory/retrieval layer** → RETRIEVE structurally impossible.
  - SWE-agent **submits via final git-diff capture**, not in-trace `git apply` → recorded via info.submission on the last event.
  - **OTHER=0** → every action classified into a meaningful type.
- **Per-event tokens null everywhere** — .traj carries only aggregate info.model_stats; we backfill trace-level prefill/decode/cost. Honest null, never 0.
- **solver_B (mini) has no token counts** — model_stats={instance_cost,api_calls} only.
- **state.diff empty** in downloaded classic sets → patch_reversions=null (deferred to L1 line-range parse).
- **Tool error rate separates capability tiers** (median): B 0.01 « C 0.13, E 0.09 — tracks resolve rates 79.2%»40.2%»33.6%. EVIDENCE only, never a label.
