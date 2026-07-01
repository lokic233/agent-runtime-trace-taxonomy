# MRT Formal — Protocol Audit (Step 4)

**Shim:** `harness/pruning_ab/scripts/mrt_formal_shim.py` sha256[:16] = `df08cebcfd2b37c6`
**Tests:** `harness/pruning_ab/tests/test_mrt_formal_protocol.py` sha256[:16] = `8d0b7f91dd4d48b0`
**Result:** **24/24 PASS** (auto: `results/pruning_ab/mrt_formal/protocol_test_results.json`)

All 22 mission-required protocol properties are covered (24 assertions incl. 2 sub-tests).
**No paid formal run may proceed unless this file shows 24/24.**

| # | Test | Property |
|---|---|---|
| 1 | internal_call_filtering | setup calls (<=2 msgs) pass through, not logged |
| 2 | newest_obs_selection | segment = last observation index |
| 3 | availability | seg>=2000c AND dup>=5 AND removes>=1 line |
| 4 | continuous_moderator | dup_fraction in [0,1] recorded continuously |
| 5, 5b | stratum_high / stratum_mixed | dup_frac>0.40 → HIGH; 0<frac<=0.40 & dup>=5 → MIXED |
| 6, 6b | block 2:2 balance | every completed block = 2 LINEDEDUP / 2 NO_OP |
| 7 | deterministic_block_order | frozen SHA-256 seed → identical permutation |
| 8 | restart_persistence | assignment survives fresh module reload |
| 9 | duplicate_request_idempotent | repeated HTTP req → already_intervened, no new assignment |
| 10 | one_intervention_per_task | second eligible obs not randomized |
| 11 | noop_byte_identity | NO_OP body byte-identical to input (post identical normalization) |
| 12 | segment_local_linededup | only target msg changed; actual_changed from REAL serialized diff |
| 13 | prior_prefix_identical | all messages before target byte-identical |
| 14 | assignment_vs_activation | assignment, actual_changed, lines_removed all separate fields |
| 15 | invalid_upstream_detected | missing 'content' key → not-ok (fail closed) |
| 16 | no_synthetic_assistant | source contains NO fabricated empty-assistant content path |
| 17 | h1_cost_formula | input + 0.1·cr + 1.25·cc + 5·out |
| 18 | h3_joining | 3 sequential events summed by call_index |
| 19 | h3_truncation | <3 responses → available-only sum + terminal flag |
| 20 | unknown_task_id | unmapped fingerprint → UNK_ prefix (flagged) |
| 21 | provenance_hashes | shim_sha256 + transform_sha256 + experiment_version recorded |
| 22 | ledger_conflict_aborts | conflicting assignments in ledger → RuntimeError on startup |

## Key correctness fix over the rescue shim

The rescue shim computed `actual_changed` from a parallel line-count and only wrote the
`tool_result` content branch. For SWE-agent 1.1.0's `content=[{type:text}]` format this could
record `actual_changed=True` while **not mutating the wire**. The formal shim:
- writes all three content formats (str, [{type:text}], [{type:tool_result}]);
- computes `actual_changed` from the **real serialized diff** of the target message;
- logs `segment_hash_before`/`segment_hash_after` for independent verification.

## Fail-closed guarantee

The formal shim has **no synthetic-content path**. On an invalid upstream response it retries
per the frozen policy, then returns HTTP 502 and logs `infrastructure_failure=true` with the
failed-response hash. The task is excluded per the preregistered missing-data rule — never by
fabricating a model turn.
