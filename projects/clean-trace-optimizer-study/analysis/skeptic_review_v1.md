# Skeptic Review v1 — feature falsification

Lane C attempts to falsify each candidate feature BEFORE the correlation study.
Tests: (1) collapse-into-trace-length |Spearman vs n_actions|; (2) solver-identity eta^2;
(3) harness-identity eta^2; (4) future-info (structural); (5) outcome-independence (structural).

| feature | n | r vs n_actions | eta2 solver | eta2 harness | verdict |
|---|---|---|---|---|---|
| search_no_new_evidence_rate | 3114 | 0.227 | 0.069 | 0.064 | KEEP |
| redundant_reread_rate | 3334 | 0.542 | 0.169 | 0.164 | KEEP |
| oversized_then_narrow_read_rate | 3334 | 0.163 | 0.116 | 0.11 | KEEP |
| no_evidence_patch_churn_rate | 3360 | 0.322 | 0.08 | 0.078 | KEEP |
| post_edit_test_gap | 1073 | 0.123 | 0.017 | 0.016 | KEEP |
| fraction_actions_in_no_new_evidence_streaks | 3431 | 0.389 | 0.178 | 0.178 | KEEP |
| tool_error_rate | 3431 | 0.141 | 0.116 | 0.115 | KEEP |
| environment_setup_rate | 3431 | 0.048 | 0.028 | 0.028 | KEEP |

## Structural checks (all features)

- (4) FUTURE-INFO: FULL features use the whole trace BY DESIGN (diagnosis features, not online). PREFIX variants (T5/T10/T20) are computed strictly on events <= cutoff in src code (slice on action index); no final-outcome, final-patch, or total-token field is read by any feature. PASS.
- (5) OUTCOME-INDEPENDENCE: no feature reads `resolved` or grade fields; all derive from action/obs text. PASS.
- (6) HEALTHY-VS-WASTE: NO_EVIDENCE_PATCH_CHURN gates on intervening evidence (test/search/read/error) so edit->test->edit iteration is NOT counted as churn (validated in 45 healthy-sequence memos).
- (7) HARNESS BUG QUARANTINE: solver_C `_split_string future-annotations` edit-failures are excluded from 'evidence' so they neither reward nor are rewarded; solver_C churn flagged harness-contaminated.

## Interpretation

Features with eta2_harness >= 0.5 are HARNESS-DOMINATED and must be read per-harness, never as solver behavior — the correlation models include source_harness + repo + task FE to absorb this.