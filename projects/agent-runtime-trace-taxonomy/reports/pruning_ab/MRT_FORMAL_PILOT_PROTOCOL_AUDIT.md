# MRT Formal — Phase B Protocol Pilot Audit (Step 14)

**Auto-derived:** `results/pruning_ab/mrt_formal/pilot_protocol_report.json`
**Pilot ledger:** `results/pruning_ab/mrt_formal_pilot/events.jsonl` (332 events, immutable)
**Code:** frozen shim `df08cebcfd2b37c6`, git `35f8e28`, model claude-opus-4-7 temp=0, thinking OFF.

## Purpose (per mission §15 Phase B)
Exercise the full randomization machinery on live paid traffic: both strata, both arms, one
full block, restart persistence, H=3 joining, grading. **Phase B outcomes are NOT used in the
final formal analysis** — they are burned for infrastructure validation only.

## Result: protocol machinery works end-to-end

| Check | Result |
|---|---|
| total events logged | 332 |
| available events (base eligibility, no dup_frac gate) | 21 |
| randomized interventions | 6 |
| tasks | 6 |
| **one intervention per task** | **PASS** (max 1) |
| **strata coverage** | MIXED=4, HIGH=2 (both present) |
| **arm balance** | LINEDEDUP=3, NO_OP=3 (2:2 within block 0) |
| **LINEDEDUP prefix byte-identical** | **PASS** (3/3, prior_prefix_identical=True) |
| **LINEDEDUP changed only target seg** | **PASS** (changed_indices == [segment_index]) |
| **NO_OP full body byte-identical** | **PASS** (3/3, full_noop_identical=True, changed_indices==[]) |
| **infrastructure failures** | 0 |
| **provider errors / synthetic fallback** | 0 |
| shim sha / git consistency | single value on all events |

## Block randomization (stratified permuted-block, block size 4, 2:2)

| task | stratum | assign | block | pos | dup_frac | chars_rm | cache_read | cache_create |
|---|---|---|---:|---:|---:|---:|---:|---:|
| pylint-4551 | MIXED | LINEDEDUP | 0 | 0 | 0.043 | 364 | 4576 | 7268 |
| pylint-8898 | MIXED | NO_OP | 0 | 1 | 0.385 | 0 | 11650 | 1451 |
| sphinx-9658 | MIXED | LINEDEDUP | 0 | 2 | 0.136 | 336 | 26729 | 2000 |
| sympy-14248 | MIXED | NO_OP | 0 | 3 | 0.190 | 0 | 26597 | 1700 |
| pylint-6386 | HIGH | NO_OP | 0 | 0 | 0.902 | 0 | 19452 | 1921 |
| sphinx-8638 | HIGH | LINEDEDUP | 0 | 1 | 1.000 | 2442 | 30003 | 467 |

MIXED block 0 = [LINEDEDUP, NO_OP, LINEDEDUP, NO_OP] → exact 2:2. HIGH block 0 (partial) = [NO_OP, LINEDEDUP].

## Note on eligibility yield (consistent with power analysis)
21 available events but only 6 randomized — because **single-shot × newest-only** means each
task contributes at most one intervention (first available call). 6 tasks → 6 interventions.
This is exactly the pool-ceiling mechanism quantified in MRT_FORMAL_POWER_ANALYSIS.md.

## Conclusion
The frozen formal shim runs live, randomizes correctly with stratified 2:2 blocks, preserves
NO_OP byte-identity and LINEDEDUP prefix-identity, fails closed, and persists state. Phase B is
**PASS**. Proceeding to Phase C (formal locked run) on the frozen 18-task pool. Phase B data is
retained immutably but excluded from the primary formal estimand.
