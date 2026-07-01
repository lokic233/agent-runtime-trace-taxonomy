# MRT Pilot Reconciliation

The prior MRT pilot (MRT_SIGNAL_CAUSALITY_FINAL.md, reporting −81k causal effect) is **exploratory** because:
1. **Per-call rather than single-shot randomization** — multiple eligible events per task were randomized, creating carryover.
2. **Whole-history rather than segment-local action** — LINEDEDUP_seg called the whole-history `line_level_dedup()` instead of a segment-local transform.
3. **Offline/online event misalignment** — blind annotations and online intervention events were not reliably joined.
4. **Task-total rather than preregistered H=1 estimand** — reported task-level effects, not the proximal H=1 outcome.
5. **Assignment/activation conflation** — some assigned actions made no actual change.

**Status change:** MRT_SIGNAL_CAUSALITY_FINAL.md is reclassified from "definitive causal result" to **exploratory pilot provenance**. The −81k excess effect and the A-E interaction are DIRECTIONALLY INFORMATIVE but not protocol-conformant.

## The rescue pilot (this mission)
Implements a protocol-conformant replacement:
- **Single-shot** (one intervention per task, first eligible event only)
- **Segment-local** (only newest observation's lines deduplicated vs prior; prefix byte-identical)
- **50/50 randomization** (SHA-256 deterministic, propensity=0.5)
- **H=1 proximal estimand** (effective cost of the immediate response)
- **All 6 synthetic protocol tests pass** before any paid run

## Status
- rescue shim: BUILT + PROTOCOL-VERIFIED (all 6 tests pass)
- task manifest: FROZEN (17 tasks selected by prior eligibility)
- smoke test: RUNNING (awaiting image builds under heavy node load)
- full pilot: PENDING smoke validation
