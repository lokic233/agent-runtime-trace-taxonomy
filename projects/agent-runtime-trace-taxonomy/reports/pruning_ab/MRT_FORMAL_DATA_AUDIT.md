# MRT Formal — Data Audit (Step 18, formal locked run)

**Run:** `formal_locked` · frozen shim `df08cebcfd2b37c6` · git `dd017e7` · opus-4.7 temp=0 · thinking OFF.
**Immutable ledgers (sha256[:16]):** events.jsonl `e01d167205f6eb37` (699) ·
randomization_state.jsonl `a1c85da51dfeae83` (13) · task_state.jsonl `e7755f1d3ae3940c` (13).

## Realized sample (STOPPING RULE MET: all 18 buildable pool tasks attempted)

| quantity | value |
|---|---|
| pool tasks attempted | 18 / 18 |
| total model calls logged | 699 |
| available events (base eligibility) | 13 |
| **randomized interventions** | **13** (one per available task) |
| infrastructure failures | 0 |
| provider errors / synthetic fallbacks | 0 |
| arms | LINEDEDUP=7, NO_OP=6 |
| strata | MIXED=10, HIGH=3 |
| repos represented | 6 (pylint-dev, pydata, pytest-dev, scikit-learn, sphinx-doc, sympy) |

## Block randomization (stratified permuted-block, size 4, 2:2)

| stratum | block | composition | complete? |
|---|---|---|---|
| MIXED | 0 | 2 LINEDEDUP / 2 NO_OP | ✅ complete 2:2 |
| MIXED | 1 | 2 LINEDEDUP / 2 NO_OP | ✅ complete 2:2 |
| MIXED | 2 | 1 / 1 | partial (run ended) |
| HIGH | 0 | 2 LINEDEDUP / 1 NO_OP | partial (run ended) |

Completed blocks are exactly balanced. Partial blocks are the natural tail of the stopping rule.

## Protocol invariants (all events)
- one intervention per task: **PASS** (13 interventions / 13 distinct tasks)
- LINEDEDUP prior_prefix_identical: **PASS** (7/7)
- NO_OP full_noop_identical: **PASS** (6/6)
- assignment vs activation separated: logged (`actual_changed` recorded, ITT primary)

## Why only 13 interventions (not 60): confirmed structural, NOT a bug
5 pool tasks produced **zero** available events. Verified: none had a **single** newest
observation meeting BOTH `segment_chars≥2000` AND `duplicate_line_count≥5` simultaneously
(the earlier "max_seg / max_dup" were maxes across *different* calls). E.g. django-14771's one
large obs (seg=4054) had dup_lines=1. The shim's `available` flag matched the criteria exactly
on every event → no false negatives. This is the **single-shot × newest-only × model-efficiency**
ceiling quantified in MRT_FORMAL_POWER_ANALYSIS.md: opus-4.7 solves with little redundant
re-reading, so the online availability rate is far below the historical C0 inventory.

## Missing-data classification (before outcome analysis)
0 infrastructure failures ⟹ 0 tasks excluded by the fail-closed rule. All 13 interventions are
valid. No task was rerun for any reason.

## Verdict entering analysis
**N=13 randomized interventions < 60-event floor.** The stopping rule condition (b) — *all
buildable pool tasks attempted* — is satisfied. This is the preregistered **outcome tier #4
(underpowered/blocked, documented)**. The analysis reports effect sizes + CIs explicitly as
**descriptive**, not significance tests.
