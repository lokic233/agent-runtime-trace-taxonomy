# MRT Rescue — Provenance (Phase 0)

- **Git commit:** `4261888` (at mission start; shim + tests committed this session)
- **Shim SHA-256:** `12f631e6fd3c25ac...` (mrt_rescue_shim.py)
- **Model:** anthropic/claude-opus-4-7 via PlugBoard mTLS
- **Temperature:** 0.0
- **Seed:** 20260701
- **Randomization:** SHA-256 based, 50/50 LINEDEDUP vs NO_OP
- **Eligibility:** newest observation only, segment ≥ 2000 chars, ≥ 5 duplicate lines, dup_fraction > 0.40
- **Intervention:** segment-local line dedup (only target obs changed; prior prefix byte-identical)
- **One intervention per task** (explicit task state guard, verified by protocol test 4)
- **Protocol tests:** ALL 6 PASS (ineligible, LINEDEDUP, NO_OP, single-intervention, stable-assignment, activation-accounting)
