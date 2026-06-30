# Phase 3+4 — Blind Signal Discovery + Outcome-Aware Adjudication

## Phase 3: blind frontier-model annotation (COMPLETE, auto-generated)
- **132 valid annotations** (0 errors) across **44 decision events** × **3 annotator roles**
- All roles balanced: A_systems=44, B_reasoning=44, C_hostile=44
- **6.1 evidence trace spans / annotation** (concrete, not storytelling)
- **3.5 counterexamples / annotation** (hostile reviewer validates)
- **107 distinct pattern names** (rich ontology for Phase 5 consolidation)

### Action distribution
| preferred_action | count | % |
|------------------|------:|---:|
| KEEP_FULL_CONTENT | 93 | 70% |
| NO_OP | 33 | 25% |
| GENTLE_CAP | 5 | 4% |
| LINE_DEDUP | 1 | 1% |

### Latent-state classification
- semantic_liveness: **active 100%** (132/132) — all selected segments classified as live content
- redundancy_type: none 93%, near_duplicate 3%, others <2%
- This reflects the **selection bias** (Phase 2 chose the LARGEST observation = typically the active target file). *(See PHASE3_SELECTION_BIAS_NOTE.md)*

## Phase 4: outcome-aware adjudication (auto-generated, deterministic)
Compared blind predictions to sealed outcomes (did preferred_action's cost direction match?).

| adjudication | count | % | interpretation |
|-------------|------:|---:|----------------|
| VALIDATED_CANDIDATE | 63 | 48% | annotator said "keep" and no method saved >5% → correct |
| REJECTED | 67 | 50% | annotator said "keep" but a method DID save >5% → missed opportunity |
| UNIDENTIFIED | 3 | 2% | outcome data missing |

### Interpretation (honest)
- The frontier model **correctly identifies active/keep-worthy content** (high precision for "don't prune" on the selected segments).
- The **50% REJECTED** rate reflects that the annotator was ONLY shown the largest (= active) segment, not the genuinely-prunable content elsewhere in the trajectory. The "missed opportunity" was a **segment-selection limitation**, not a reasoning failure.
- This directly validates the selection-bias flag: to test whether frontier models can identify prunable vs non-prunable, the discovery must sample **repeated/redundant observations**, not only the largest one.

## What this establishes
- Frontier-model blind annotation produces structured, evidence-grounded, ontology-rich labels (107 patterns, 6+ evidence spans each).
- On the selected (largest-obs, active-content) segments, all 3 annotators converge on "keep" with appropriate confidence gradients (systems 0.8 > reasoning 0.68 > hostile 0.58).
- The adjudication against outcomes is honest: no overclaim of "pattern predicts which action helps" — the tested segments are biased toward "keep" cases.

## What remains untested (Phase 8 MRT)
- Whether frontier-model annotation identifies prunable opportunities when shown **smaller, repeated, genuinely-redundant segments** (the MRT shim randomizes at ALL eligible segments, not just the largest).
- Whether blind pattern labels **causally modify** a specific action's local effect (randomized intervention required).

## IMPORTANT: frontier-model consensus is NOT causal evidence
These annotations are *proposal generation for ontology building*. The adjudication is *observational* (single paired run). Only the randomized MRT (Phase 8) can validate causal moderation. (Per mission rule: "Do not call a pattern causally validated based only on forensic plausibility.")
