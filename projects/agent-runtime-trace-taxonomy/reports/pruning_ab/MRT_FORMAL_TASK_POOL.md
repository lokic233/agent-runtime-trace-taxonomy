# MRT Formal — Task Pool (Step 8)

**Frozen manifest:** `results/pruning_ab/mrt_formal/task_manifest.json` · auto-derived from
`results/pruning_ab/candidate_events.jsonl` (778 events across 50 C0 trajectories).

## Selection rule (pre-treatment only)

A task enters the pool iff its **C0 trajectory** contains ≥1 event meeting formal **base
availability**: newest-style observation with `segment_chars ≥ 2000` AND `dup_lines ≥ 5`.
**No selection on any LINEDEDUP outcome.** Difficult/failing tasks are NOT excluded; known
canaries are flagged, not dropped.

## Pool (18 tasks, 60 prior available events, 7 repos)

| task | repo | prior avail evts | HIGH | MIXED | max dup_frac | image cached | baseline note |
|---|---|---:|---:|---:|---:|:--:|---|
| pylint-4551 | pylint-dev | 11 | 5 | 6 | 0.98 | ✅ | **universal canary (baseline fails)** |
| pytest-6197 | pytest-dev | 9 | 6 | 3 | 1.00 | ✅ | stochastic-flip baseline |
| pylint-8898 | pylint-dev | 7 | 3 | 4 | 1.00 | ✅ | (rescue: unresolved) |
| sphinx-8638 | sphinx-doc | 6 | 6 | 0 | 1.00 | ✅ | |
| pylint-6528 | pylint-dev | 5 | 3 | 2 | 1.00 | ❌ | |
| pylint-6386 | pylint-dev | 4 | 2 | 2 | 0.93 | ✅ | |
| scikit-learn-259xx | scikit-learn | 3 | 2 | 1 | 1.00 | ❌ | |
| sympy-14248 | sympy | 3 | 2 | 1 | 1.00 | ✅ | (rescue: intervened LINEDEDUP) |
| xarray-3305 | pydata | 2 | 1 | 1 | 1.00 | ❌ | |
| sphinx-9658 | sphinx-doc | 2 | 2 | 0 | 1.00 | ✅ | |
| django-14771 | django | 1 | 1 | 0 | 0.42 | ❌ | |
| django-16136 | django | 1 | 1 | 0 | 0.41 | ❌ | |
| pytest-7324 | pytest-dev | 1 | 1 | 0 | 0.65 | ❌ | |
| pytest-7432 | pytest-dev | 1 | 0 | 1 | 0.34 | ❌ | |
| pytest-7490 | pytest-dev | 1 | 1 | 0 | 1.00 | ❌ | |
| scikit-learn-140xx | scikit-learn | 1 | 0 | 1 | 0.16* | ❌ | *below dup≥5? verify |
| scikit-learn-928x | scikit-learn | 1 | 1 | 0 | 0.46 | ❌ | |
| sympy-19040 | sympy | 1 | 1 | 0 | 0.52 | ✅ | (rescue: no eligible obs online) |

## Critical caveat: C0 inventory is an UPPER BOUND on online availability

The 60 events are enumerated across **all** observations in C0 trajectories. The formal shim
randomizes only the **newest** observation at the **first available call** (single-shot). Two
forces reduce the online rate below this inventory:

1. **Single-shot × newest-only:** a task with 11 prior available events yields **at most 1**
   online intervention.  ⟹ the pool's ceiling is **≤18 interventions**, not 60.
2. **Model efficiency drift:** opus-4.7 now solves many tasks in far fewer turns than when
   the C0 traces were collected (rescue evidence: only 2/5 cached tasks reached availability).

⟹ **The 18-task pool cannot reach the 60-event floor.** Reaching it requires either (a) a much
larger task pool (many more images built) or (b) relaxing single-shot (which the protocol
forbids). This is quantified in the eligibility dry run (Step 9) and power analysis (Step 10),
and is the leading candidate for **outcome #4 (underpowered/blocked, documented)**.

## Image-cache constraint

8/18 pool tasks have cached eval/run images. Node currently healthy (384 cores, ~2TB RAM free,
load ~20) so additional images CAN be built, but each SWE-agent run is single-shot per task
⟹ building more images buys more tasks (each ≤1 intervention), the only way to grow N.
