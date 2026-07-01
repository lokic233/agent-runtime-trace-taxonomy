# MRT Rescue Pilot — Results (Emergency Rescue Run)

**Date:** 2026-07-01
**Node:** cli:devgpu014
**Shim:** `scripts/mrt_rescue_shim.py` sha256[:16] = `ae352c2efdb0769e`
**Event log:** `results/pruning_ab/mrt_rescue/events.jsonl` (215 model calls, 5 tasks)
**Grade report:** `results/pruning_ab/mrt_rescue/grade_report.json`
**Model:** anthropic/claude-opus-4-7, temp=0.0, SWE-agent 1.1.0, thinking OFF
**Seed:** 20260701

## What this run IS

A **protocol-conformant single-shot MRT smoke test** that ran end-to-end on 5 real
(paid) SWE-bench Verified tasks and was graded. It fixes the prior pilot's 5 protocol
mismatches and demonstrates the corrected mechanism works on live traffic.

## What this run is NOT

It is **NOT a powered causal pilot**. See "Honest limitations" below. N=2 interventions,
both drew into treatment by chance → **zero controls** → no causal effect is estimable.
Per the rescue mandate: *clean smoke test > incomplete pilot; do not overclaim.*

## Protocol conformance — ALL PASS

| Check | Requirement | Result |
|---|---|---|
| 1. One intervention per task | single-shot, `already_intervened` gate | **PASS** (0 tasks intervened >1×) |
| 2. Target newest observation | segment = last obs index only | **PASS** (all exp events have segment_index) |
| 3. Prefix preserved | transform must not mutate any prior message | **PASS** (prior_prefix_identical=True, both) |
| 4. 50/50 randomization | propensity=0.5, SHA-256 stable u | **PASS** (propensity=0.5 both; u=0.227, 0.301) |
| 5. Segment-local LINEDEDUP | dedup only within newest obs vs prior obs | **PASS** (changed_message_indices = single idx) |
| 6. H=1 proximal estimand | effective_cost_h1 logged per event | **PASS** (3882.6, 5282.1) |

Synthetic protocol tests: **6/6 PASS** (`scripts/test_mrt_rescue_protocol.py`) against this exact shim sha.

## The two interventions (H=1 proximal detail)

| Task | call | assign | u | dup_frac | dup_lines | chars_removed | prefix_ok | cache_read | cache_create | ratio |
|---|---|---|---|---|---|---|---|---|---|---|
| pylint-8898 | 30 | LINEDEDUP | 0.227 | 1.00 | 54/54 | 2445 | ✓ | 31316 | 256 | **122.3×** |
| sympy-14248 | 35 | LINEDEDUP | 0.301 | 0.57 | 31/54 | 1151 | ✓ | 25573 | 1783 | **14.3×** |

**Cache-preservation signal (the real scientific win):** both interventions kept a
high cache_read:cache_creation ratio (122×, 14×). The prior recency-based HYBRID1 method
destroyed the cache (ratio 0.37×). This empirically confirms the **content-stable pruning
principle** on live traffic: a segment-local transform of the newest observation preserves
the provider prompt-cache prefix, where whole-history/recency transforms bust it.

## Eligibility — why only 2/5 tasks intervened

| Task | calls | eligible obs | intervened | max dup_frac | note |
|---|---|---|---|---|---|
| pylint-8898 | 36 | 1 | 1 (LINEDEDUP) | 1.00 | fully-redundant re-read |
| sympy-14248 | 75 | 2 | 1 (LINEDEDUP) | 0.62 | 2nd eligible obs correctly skipped (single-shot gate) |
| sympy-14976 | 22 | 0 | 0 | 0.03 | never crossed dup_frac>0.40 |
| sympy-19040 | 75 | 0 | 0 | 0.11 | never crossed dup_frac>0.40 |
| sympy-24539 | 7 | 0 | 0 | 0.00 | solved fast, no redundancy |

Eligibility gate: `seg_chars>=2000 AND dup_lines>=5 AND dup_frac>0.40`.

## Task-level outcomes (SWE-bench Verified grade)

| Task | intervened | assign | resolved |
|---|---|---|---|
| pylint-8898 | yes | LINEDEDUP | **NO** |
| sympy-14248 | yes | LINEDEDUP | **NO** |
| sympy-14976 | no | — | YES |
| sympy-19040 | no | — | YES |
| sympy-24539 | no | — | YES |

Grade: 3/5 resolved, 0 errors.

## Honest limitations (do NOT overclaim)

1. **No control arm.** Both randomization draws (u=0.227, 0.301) fell below 0.5 → both
   LINEDEDUP. With 0 NO_OP controls, **no causal (treatment vs control) contrast exists**.
   The 2-vs-3 resolved split is confounded with task difficulty and cannot be attributed
   to the intervention.
2. **pylint-8898 is the known universal canary** — it fails baseline (0/5) across all prior
   arms independent of any pruning. Its non-resolution here is uninformative.
3. **N=2 interventions** is far below any power threshold. A real pilot needs enough tasks
   that (a) many cross the eligibility bar and (b) treatment/control balance emerges.
4. **Low eligibility rate** (2/5 tasks had any eligible obs) means the golden-50 (or larger)
   set is required to accumulate interventions. opus-4.7's improved 1-shot solving further
   reduces multi-turn redundancy, shrinking the eligible pool.

## Conclusion

The rescue **succeeded at its stated priority**: a protocol-conformant, single-shot,
segment-local, 50/50-randomized, H=1 MRT shim now runs cleanly end-to-end on live paid
tasks, passes 6/6 synthetic tests, and logs a complete proximal + task-level ledger with
zero protocol violations. The cache-preservation signal (122×/14× vs HYBRID1's 0.37×)
is real and consistent with the content-stable principle.

This is a **clean smoke test**, not a powered causal result. Scaling to a powered pilot
requires a larger task pool to obtain treatment/control balance.

## Reproduce

```
# shim (project-dir launcher, setsid, strips IPv6 no_proxy that crashes litellm)
setsid bash scripts/launch_rescue_shim.sh > logs/mrt/shim.log 2>&1 < /dev/null &
# run (5 cached-image tasks, podman --memory=4g, 3 workers)
setsid bash scripts/run_rescue_cached.sh > logs/mrt/run.log 2>&1 < /dev/null &
# grade
setsid bash scripts/grade_rescue.sh > logs/mrt/grade.log 2>&1 < /dev/null &
```
