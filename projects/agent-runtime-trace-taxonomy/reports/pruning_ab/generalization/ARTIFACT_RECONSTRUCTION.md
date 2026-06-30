# ARTIFACT_RECONSTRUCTION — Phase A

**Purpose:** Regenerate the canonical Opus-4.7 context-materialization facts from the machine-readable
artifacts (not copied prose) and assert agreement with the canonical audit, before any paid run.

**Source freeze commit:** `bb43b49612760b56a3f8d620fbffcae9dc347bf6`
**prune_methods.sha256 (manifest):** `cb06efb69c9a08e7a48a1fca747a9fe1e9f71fcf657158a3c5463b028e0d10cf`
**Reconstruction script:** generated `results/pruning_ab/generalization/artifact_reconstruction.json` (with per-source SHA-256).

## Reconstructed canonical facts (from JSON)

| Fact | Reconstructed value | Source |
|------|--------------------|--------|
| Canonical C0 (stable, cost-pairing baseline) | **46/50 resolved** (49 completed) | `causal_data_manifest.json` |
| v2 separate C0 (provenance only) | 48/50 — NOT the E3/E4 pairing baseline | CAUSAL_DATA_AUDIT |
| Cache tax (cc_fraction) | C0 **0.077** [.061,.098] · SHAM **0.066** [.051,.083] · HYBRID1 **0.784** [.733,.83] | `mechanism_effects.json` |
| Intelligence tax (dose-controlled OLS, n=206) | dose_coef **+0.0001/kchar (≈0)** · is_destructive_coef **+0.415** | `mechanism_effects.json` |
| LINEDEDUP_e4 | bill-weighted **+6.3%**, leave-top-{1:+0.9, 3:−4.0, 5:−8.8} | `robustness.json` |
| GENTLE6K_stable | bill-weighted **+10.1%** (best static), leave-top-{1:+2.5, 3:−7.1, 5:−8.4} | `robustness.json` |
| SHAM cost negative control | dup_line_ratio↔SHAM Spearman **−0.758** (FAILS as method-specific moderator) | `falsification.json` |
| LINEDEDUP repo-cluster CI | **[−9.9%, +18.0%]** (straddles zero) | `falsification.json` |
| Controller | oracle 4,019,692 · always_GENTLE6K 4,951,455 · best trace policy (dup>0.25→LD) 4,997,664 → **trace policy costs MORE than best static → NOT_SUPPORTED** | `controller_policies.json` |
| Success-CATE (repeated, 10 tasks) | HYB−C0 **+0.00**, SHAM−C0 **+0.02** (control valid), 5/10 C0-unstable | `success_cate_repeated.json` |
| Consistency assertions | **7/7 all_pass=true** | `consistency_assertions.json` |

## Agreement audit
**14/14 agreement checks PASS** (see `artifact_reconstruction.json → agreement_checks`). The reconstructed
numbers do NOT materially disagree with the canonical audit. **Cleared to proceed.**

## Preserved negative results (must not be weakened)
- TRACE_SIGNAL_PREDICTIVENESS = NOT_SUPPORTED
- DEPLOYABLE_CONTROLLER_VALUE = NOT_SUPPORTED
- Saving is NOT robust (concentrated in 1–3 expensive tasks; leave-top-3 flips both methods negative)
- Single-run regression flips have UNRESOLVED attribution (the "A/A = noise, deletable" framing is RETRACTED)
