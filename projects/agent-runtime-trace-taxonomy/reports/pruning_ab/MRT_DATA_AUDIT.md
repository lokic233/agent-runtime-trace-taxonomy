# Phase 0 — MRT Data Audit (freeze)

**Commit:** `4986a2149fabe0e3c975eb73bec632e8bd545f55`

## Frozen
- action implementations: line_level_dedup, cap_all_obs (6k), retrieval_ref_large (from prune_methods.py sha256 cb06efb6...)
- eligibility: segment ≥200 chars for stratum assignment; ≥2000 chars for MRT randomization
- annotation prompts: 3 roles (systems/reasoning/hostile), structured JSON schema (from blind_annotate.py)
- randomization: 50% NO_OP / 50% ACTION per eligible event within stratum (single intervention per task)
- outcomes: incremental eff-cost (H=1,3), cache tokens, output, rereads, resolution
- stop: one intervention per task; abort on data-integrity uncertainty; balance gate checked before randomization

## Trace inventory
| data | count | content |
|------|------:|---------|
| C0 trajectories | 50 | full observation content per call ✅ |
| LINEDEDUP trajectories | 50 | full obs content + activation logs ✅ |
| LINEDEDUP ledger (per-call) | 1203 calls | changed/chars_removed/cache/output ✅ |
| C0 ledger (per-call) | 1159 calls | cache/output per call ✅ |
| Phase34 A/A repeated runs | 15 grades (5×C0/SHAM/HYBRID1 on 10 tasks) ✅ |
| Candidate events enumerated | 778 across 50 tasks ✅ |
