# Signal-Discovery + Causal-Validation — Final Report & 8 Verdicts

## The scientific question
> Which identifiable semantic/runtime patterns in an agent trajectory **causally modify** the benefit & quality-risk of specific optimization actions?

## Pipeline executed
frontier-model pattern discovery (P3) → structured ontology (P5) → blind annotation frozen before outcome reveal → action-specific outcome-aware adjudication (P4) → candidate moderators (P6) → retrospective screening with negative controls (P7) → micro-randomized trial DESIGNED but PENDING (P8).

## VALID PRIOR NEGATIVE (preserved from the prior study)
**STATIC_TASK_LEVEL_SUMMARY_ROUTING: NOT_SUPPORTED.** Task-level aggregate features (dup_line_ratio etc.) failed all tests: SHAM negative control (Spearman −0.76), interaction CI∋0, LORO +4.9% < static +10.1%, fragile leave-top-3. NOT WEAKENED.

---

## THE 8 VERDICTS

```
FRONTIER_MODEL_SIGNAL_DISCOVERY:              SUPPORTED
  (132 valid annotations, 0 errors, 6.1 evidence spans/ann, 3.5 counterexamples/ann,
   107 distinct grounded patterns, high cross-role agreement on latent state 91-100%.
   Frontier models CAN produce structured, evidence-grounded trace annotations.)

ANNOTATION_AGREEMENT:                         SUPPORTED
  (semantic_role 96%, liveness 100%, redundancy 91%, recoverability 96%, task_phase 98%.
   Only dependency_risk 67% has genuine uncertainty. Action agreement 59% but
   disagreements are within the "don't-prune" family.)

ACTION_SPECIFIC_ONTOLOGY:                     PARTIALLY_SUPPORTED
  (Ontology defined with 10 actions + 6 latent-state axes. Agreement strong. BUT the
   tested decision points are biased toward "active/keep" → the ontology lacks enough
   "prune-recommended" examples to validate action-specificity. The distinction between
   LINE_DEDUP-applicable vs GENTLE_CAP-applicable latent states is THEORETICAL until MRT.)

BLIND_SEMANTIC_SIGNAL_VALUE:                  UNDERPOWERED
  (Blind annotations correctly identify "active/keep-worthy" content (precision). But the
   decision-point selection biased toward the largest (= active) observations, so failure
   to predict pruning opportunities is a SELECTION ARTIFACT, not a falsification of
   semantic signals. The right test = MRT sampling ALL eligible segments.)

RETROSPECTIVE_ACTION_EFFECT_PREDICTION:       NOT_SUPPORTED
  (candidate_dup_lines_vs_prior Spearman +0.03 with LINEDEDUP saving; permuted +0.16 > real;
   bin analysis opposite to hypothesis. On the tested segments, retrospective prediction fails.)

RANDOMIZED_CAUSAL_MODERATION:                 PENDING_TRIAL
  (MRT shim built + smoke-tested; protocol preregistered; 50% NO_OP / 25% LINE_DEDUP / 25%
   GENTLE_CAP with propensity + prefix-state logging. NOT YET EXECUTED. This is the only
   test that can validate whether ontology patterns causally modify action effects.)

LOCAL_PATTERN_RECOGNIZER:                     PENDING_DATA
  (Requires MRT outcomes + broader ontology examples to supervise. Cannot train on the
   current 132 annotations which are 100% "active/keep" — no prune-class supervision signal.)

SEQUENTIAL_CONTROLLER_VIABILITY:              PENDING_TRIAL
  (Roadmap in LEARNED_CONTROLLER_ROADMAP.md. No data to evaluate until MRT runs + local
   recognizer trains. The speculative-feedback-rollback architecture is DESIGNED but untested.)
```

---

## What this study established
1. **Frontier models produce high-quality structured trace annotations** (SUPPORTED): 6+ evidence spans, 3+ counterexamples, 91-100% latent-state agreement across roles, grounded in concrete trace content.
2. **The prior negative (static task-level routing) is preserved and correctly scoped** (NOT WEAKENED): the new mission tested a different representation and architecture.
3. **The selection bias in this batch (largest obs → active content → keep)** is an honest limitation that prevents adjudicating whether semantic patterns predict pruning opportunities — it does NOT falsify that claim, it leaves it UNTESTED.
4. **The ontology infrastructure (10 actions × 6 latent-state axes) is built and frozen** — ready for the MRT to populate with diverse prune/keep examples.

## What remains PENDING (honestly)
- **Causal validation (Phase 8 MRT):** the only test of whether ontology patterns *causally modify* action effects. Without it, all moderator hypotheses remain theoretical.
- **Local recognizer (Phase 9):** cannot train without MRT supervision data.
- **Sequential controller (Phase 10):** roadmap only until MRT + recognizer validate.

## Honest bottom line
Frontier-model blind annotation works well (structured, grounded, agreeing) — but the current dataset lacks the diversity to validate action-specific causal moderation. The pilot's decision-point selection was biased toward "keep" cases, making it uninformative about *when to prune*. The MRT (designed, preregistered, shim built, not yet run) tests the correct hypothesis on the correct segments. Until it runs, the question "can semantic patterns identify safe pruning opportunities?" is **open, not negative.**
