# Verdict Scope Correction

The prior `TRACE_CAUSALITY_FINAL.md` reported **TRACE_SIGNAL_PREDICTIVENESS: NOT_SUPPORTED**. This is **too broad**. It conflates a specific tested claim with a general untested one.

## The exact claim that WAS tested
> Using **one row per task** with features computed mostly from the **complete C0 trajectory**, can a **static per-task method assignment** (pick one method for the whole task) outperform the best static policy?

## The exact claim that WAS falsified (preserved — still valid)
1. **Task-level aggregate features fail static routing.** dup_line_ratio CATE bins all have CIs spanning zero; interaction term (dup×LINEDEDUP) = −2.7%, CI [−18.6,+13.4] ∋ 0.
2. **dup_line_ratio failed the SHAM/no-op negative control** (Spearman −0.76 with a no-op method's cost-delta → tracks run-to-run noise, not treatment benefit).
3. **Leave-one-repository-out static routing did not beat best static** (+4.9% LORO vs +10.1% static).
4. **Aggregate savings are fragile**: leave-top-3-expensive-out flips LINEDEDUP to −4.0%, GENTLE6K to −7.1%; repo-cluster CI [−9.9%, +18.0%].

These remain **NOT_SUPPORTED** and are not weakened.

## The claims that were NEVER tested (wrongly implied as falsified)
1. **Decision-time prefix-aligned features** (computed from the trajectory prefix at a specific call, not the whole task).
2. **Segment-level treatment heterogeneity** (effect of pruning a *specific observation at a specific call*, not whole-task method).
3. **Post-intervention feedback value** (can early harm signals detect a bad pruning?).
4. **Speculative + rollback control** (try, verify on a short horizon, undo if harmful).
5. **Quality-budgeted online control.**

None of these were experimentally evaluated. Claiming them falsified would be **scientifically invalid** — the experimental object (whole-task retrospective summary) is not the same as prefix-aligned runtime state, and static prediction is not the same architecture as speculative execution with feedback/rollback.

## Old → corrected verdict map

| old verdict | old value | corrected verdict(s) | corrected value |
|-------------|-----------|----------------------|-----------------|
| TRACE_SIGNAL_PREDICTIVENESS | NOT_SUPPORTED | STATIC_TASK_LEVEL_TRACE_PREDICTIVENESS | NOT_SUPPORTED (preserved) |
| | | CURRENT_FULL_TRAJECTORY_SUMMARY_CONTROLLER | NOT_SUPPORTED (preserved) |
| | | DECISION_TIME_TRACE_PREDICTIVENESS | UNTESTED → (this mission) |
| | | SEGMENT_LEVEL_TREATMENT_HETEROGENEITY | UNTESTED → (this mission) |
| | | POST_INTERVENTION_FEEDBACK_VALUE | UNTESTED → (this mission) |
| | | SPECULATIVE_ROLLBACK_CONTROLLER | UNTESTED → (this mission) |
| | | QUALITY_BUDGETED_ONLINE_CONTROL | UNTESTED → (this mission) |
| DEPLOYABLE_CONTROLLER_VALUE | NOT_SUPPORTED | (scoped to) STATIC per-task routing | NOT_SUPPORTED (preserved); speculative-feedback architecture UNTESTED |

## Revised wording for TRACE_CAUSALITY_FINAL.md
Replace "TRACE_SIGNAL_PREDICTIVENESS: NOT_SUPPORTED" with:
> "STATIC, full-trajectory-summary, per-task trace routing: NOT_SUPPORTED. Decision-time/segment-level/feedback-based control: UNTESTED (requires event-level randomized evaluation — this follow-up mission)."

## Superseded language (explicitly marked, not deleted)
- TRACE_CAUSALITY_FINAL.md line "TRACE_SIGNAL_PREDICTIVENESS: NOT_SUPPORTED" → **narrowed** to STATIC_TASK_LEVEL (see TRACE_CAUSALITY_FINAL_V2.md).
- Any phrasing implying "trace signals cannot support any controller" → **superseded**: only the static task-level architecture was tested.
