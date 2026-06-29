# Feature Calibration v1

Precision = fraction of detector-flagged instances that are TRUE waste under the feature definition
AND its counter-interpretation (e.g. empty searches that legitimately falsify are counted as FALSE
positives for SEARCH_NO_NEW_EVIDENCE; harness `_split_string` edit-fails are FALSE positives for churn;
intentional repro-script failures are FALSE positives for tool-error). Two auditors: R1 detector
evidence, R2 independent counter-interpretation re-check; R2 adjudicates. Target precision >= 0.80.

| feature | traces | instances flagged | true positives | precision | gate(>=0.80) |
|---|---|---|---|---|---|
| SEARCH_NO_NEW_EVIDENCE_RATE | 25 | 38 | 34 | 0.895 | PASS |
| OVERSIZED_THEN_NARROW_READ_RATE | 25 | 50 | 50 | 1.0 | PASS |
| NO_EVIDENCE_PATCH_CHURN_RATE | 25 | 244 | 244 | 1.0 | PASS |
| TOOL_ERROR_RATE | 25 | 702 | 586 | 0.835 | PASS |
| STAGNATION_FRACTION | 25 | 1296 | 1296 | 1.0 | PASS |
| POST_EDIT_TEST_GAP | 0 | 0 | 0 | None | n/a |

Notes: REDUNDANT_REREAD_RATE and ENVIRONMENT_SETUP_RATE are not headline-calibrated (secondary / harness-confounded). Calibration audited on LOCALLY-available traces (B/C/E/G/H on devvm; A/F skipped where files are on devgpu014) — sample is the high-signal tail per feature.

## POST_EDIT_TEST_GAP note
PETG is a DETERMINISTIC definitional measure (steps from last edit to next test; None if no post-edit test). It has no fuzzy detection step, so 'precision' is structurally 1.0 by construction — there is nothing to mis-detect. Its scientific risk is INTERPRETATION (a gap is not proven 'waste' without verified oracle availability), not detection error. Hence the deterministic name and the spec caveat. Local-file calibration sampling returned 0 because the no-post-edit-test tail traces were opus A/F (raw files on devgpu014, not on the analysis node); the feature itself is computed for all 3432 traces in the table.
