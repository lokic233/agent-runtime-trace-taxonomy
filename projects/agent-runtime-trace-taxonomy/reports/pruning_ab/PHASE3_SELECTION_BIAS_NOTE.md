# Phase 3 Methodological Note — Decision-Point Selection Bias (flag for analysis)

**Observation (during blind annotation):** The Phase 2 decision-point selector chose the **largest observation per task** as the candidate segment. Early annotations show these are predominantly classified `semantic_liveness=active`, `redundancy_type=none` → preferred action KEEP_FULL_CONTENT/NO_OP.

**Why:** the largest observation is frequently the source file the agent is actively editing (high dependency, not redundant). The genuinely *prunable* content (exact duplicates, superseded state, stale repeated reads) tends to live in **smaller, repeated** observations, not the single largest one.

**Implication for verdicts:**
- This selection may **under-sample the prunable opportunities** the ontology is designed to detect.
- A fairer decision-point sampling for the MRT (Phase 8) should include: repeated observations, observations with high dup-vs-prior, and superseded-state candidates — not just the largest.
- The blind discovery still serves its purpose (does a frontier model identify *active/keep* vs *prunable* correctly?), but the retrospective screening (Phase 7) and MRT (Phase 8) should stratify by candidate TYPE, not just size.

**Action taken:** flagged here; the MRT shim already randomizes at any eligible (≥2000 char) segment, and Phase 8 stratification includes duplicate-class + recoverability. This note prevents over-reading a "mostly KEEP" blind distribution as evidence that pruning is rarely useful — it may be an artifact of selecting the largest (=active) segment.
