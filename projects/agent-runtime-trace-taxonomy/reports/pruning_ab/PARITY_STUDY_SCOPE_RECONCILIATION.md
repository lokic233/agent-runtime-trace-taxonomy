# Parity-Study Scope Reconciliation (P0.1)

Audit of the retrospective parity artifacts (commit `4121d70`) against their actual evidence.
**This document corrects scope; it supersedes the broader wording in the earlier parity reports
without erasing them.** No sealed raw artifact modified; no new runs.

## Discrepancy table

| Claimed object | Actual object | Scientific consequence | Required wording correction |
|---|---|---|---|
| "4-action ladder A0..A3" evaluated | A0=C0_identity, **A1=M4_obs_cap_5k**, A2=M6_env_log_collapse, A3=M7_old_obs_elide | M4 obs-cap is NOT prefix-preserving LINEDEDUP; the conceptual A1 was never evaluated on the 50-task matrix | State "A1 proxy = M4 obs-cap; actual LINEDEDUP not in this matrix". **Never call M4 LINEDEDUP.** |
| "task-total effective cost" | provider `instance_cost` ($) used as PROXY (corr 0.67–0.74 with the custom formula) | The custom cache-aware effective cost was NOT the metric for the 50-task oracle gap | Label the 50-task gap as "provider-$ proxy", not the custom effective cost |
| "oracle gap" (implying replicated) | **1 run per (task,action) cell** | A per-task min over single noisy draws is winner's-curse biased | Always attach "single-run; cannot beat SHAM noise floor" |
| SHAM noise floor (implying general) | SHAM measured on **10 tasks, 2.67× the 50-task mean cost, 5/10 repos** | Noise floor may not transfer to cheaper tasks | State SHAM subset is high-cost; report cheap/expensive split |
| "Decision C — No useful parity" | Decision C **for this single-run retrospective matrix** | Reads as "no parity exists in general" — unsupported | Scope to "not established from this matrix"; general parity "not established AND not falsified" |
| "bias-corrected oracle gap ~0%" | No positive lower bound establishable; null can manufacture ≥ observed | "exactly zero" is a stronger claim than the data support | "No positive lower bound establishable"; NOT "true gap is zero" |
| "0/50 tasks show a stable crossing" | 0/50 have **repeated evidence** to establish one (1 rep each) | Reads as "50/50 proven no crossing" — unsupported | "0/50 have sufficient repeated evidence"; NOT "proven no crossing" |
| A2/A3 "kill" (all moderate) | Aggressive **recency** (HYBRID1) kill is well-supported (cache-bust, 9/10 net-negative); M4/M6 moderate evidence is **non-diagnostic** | Conflates a strong recency-kill with weak moderate-transform evidence | Separate: recency=kill; M4/M6 moderate=non-diagnostic/redesign |

## Net effect
The retrospective study's **method is sound and its central methodological negative stands** (a
single-run per-task oracle cannot exceed the SHAM-calibrated min-selection noise floor). Only the
**scope of the conclusions** was too broad. The canonical verdicts (CANONICAL_DECISION_MEMO.md) and
evidence matrix (TRACECONTROLLER_CANONICAL_EVIDENCE_MATRIX.md) use the corrected wording.
