# MRT Confirmatory (Study 2) — Protocol & Harness Audit (Part III)

**Isolated Study-2 harness** (does NOT touch Study-1 code or artifacts).
- shim: `harness/pruning_ab/scripts/mrt_confirmatory_shim.py` sha256[:16] = `87b0043ab8c2194c`
- tests: `harness/pruning_ab/tests/test_mrt_confirmatory_protocol.py` sha256[:16] = `d0d30055134ae882`
- H=3 joiner: `harness/pruning_ab/scripts/join_h3_confirmatory.py` sha256[:16] = `3bc25c2c56a9b3ad`
- results dir: `results/pruning_ab/mrt_confirmatory/`  ·  **NEW seed 20260702** (Study 1 was 20260701)

## Protocol tests: 26/26 PASS
Auto-derived `results/pruning_ab/mrt_confirmatory/protocol_test_results.json`. The 22 formal
checks plus 4 hardening/robustness checks (unknown-task, restart-ordinal, main-agent-class,
ledger-conflict).

## The three hardening fixes (all tested)

### FIX 1 — Unknown task IDs fail closed (test 20 PASS)
`_task_of` now returns `(task_id, known_bool)`. An unrecognized fingerprint ⟹
`task_known=False`, `infrastructure_failure=True`, **never randomized** (0 assignments written),
error logged. Study 1 could emit `UNK_<fp>` and still randomize; Study 2 cannot.

### FIX 2 — Restart-safe monotonic event ordinal + stable event_id (test 21 PASS)
Persistent per-task ordinal in an append-only ledger (`event_ordinal.jsonl`), reconstructed on
startup. `event_id = study_id : task_id : o<ordinal> : request_hash : segment_hash`.
Verified: two calls → ordinals [1,2]; after a process restart the next call → ordinal **3** (no
reset to 1); all three event_ids unique. No collision after restart.

### FIX 3 — Main-agent-call classification (test 22 PASS + offline audit)
Every provider call is classified `internal_setup | main_agent_call`. H=3 joins the intervention
response + the next two **main_agent** responses only (internal calls never counted). All provider
calls preserved in `provider_events.jsonl` for total-cost accounting.
**Validated on 24 real trajectories** (Study-1 formal 18 + pilot 6): 24/24 consistent
(`main_agent_call_audit.json`), meeting the ≥20 requirement.

## Retained protocol guarantees (tests 1–19, 23–24)
Single intervention/task, newest-obs target, base availability (seg≥2000 & dup≥5 & removes ≥1
line; dup_frac continuous moderator), stratified permuted-block 2:2, deterministic seeded blocks,
NO_OP byte-identity, segment-local LINEDEDUP, prior-prefix identity, **no synthetic assistant
content** (fail-closed 502 on invalid upstream), H=1 cost formula, ledger-conflict abort,
provenance hashes on every event.

## SHAM mode (Part IX) implemented
`MRT_CONF_MODE=sham`: traverses the transform path (computes the dedup) but sends **byte-identical**
context (result discarded). Randomizes SHAM vs NO_OP so dup_frac can be tested as a moderator of a
NULL transform — a separate calibration cohort, not mixed into the primary two-arm estimand.

## Review gate (mission requirement)
Corrected estimators (Stage 1), event-ordering fix, and main-agent-call classification have all
passed offline review. **Cleared to proceed** to task-pool construction, eligibility audit, power/
precision simulation, and preregistration — before any paid Study-2 run.
