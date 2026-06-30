# GENERALIZATION_FINAL — Cross-Model Context-Materialization Transport

**Status:** SKELETON (Phase A complete; Phase B smoke running; Phases C/D/E pending user GO for paid runs).
This file is populated by the analyzers (analyze_cache_tax / intelligence_tax / static_policy) + smoke_gates
once paid data exists. It does NOT modify any canonical Opus artifact.

## Scope (unchanged from prereg)
Mechanism-generalization + frozen-static-policy transport. NOT controller generalization.
`CONTROLLER_GENERALIZATION = NOT_TESTED — REQUIRES COMPLETED MRT` (hard, non-negotiable).

## Anchor (frozen Opus 4.7, reused — not rerun)
- Cache tax: C0 0.077 ≈ SHAM 0.066 ≪ HYBRID1 0.784 (SUPPORTED)
- Intelligence tax: dose_coef≈0, destructive_coef 0.415 (SUPPORTED, quasi-experimental)
- Trace-signal predictiveness: NOT_SUPPORTED · Deployable controller: NOT_SUPPORTED
- Saving NOT robust: leave-top-3 flips LINEDEDUP→−4.0%, GENTLE6K→−7.1%; repo-cluster CI [−9.9,+18.0]

## Q1 Cache tax across Claude tiers
_[populated from cache_tax_transport.json]_  Preview (smoke, EXPLORATORY): Sonnet C0 0.035 ≈ SHAM 0.039 ≪ HYBRID1 0.788.

## Q2 Intelligence tax vs capability
_[populated from intelligence_tax_scaling.json]_

## Q3 Frozen static-policy zero-shot transport
_[populated from static_policy_transport.json]_

## Q4 Effect attribution (capability / caching / pricing / tokenization / trajectory)
_[synthesis]_

## Three transport concepts (kept distinct)
- mechanism transport · effect-size transport · policy transport (a mechanism may transport while the policy does not)

## FINAL VERDICT TABLE (mission §11 — each: status · point est · CI · n · robustness · main limitation)
```
ARTIFACT_REPRODUCTION:               SUPPORTED (14/14 agreement vs canonical audit; Phase A)
RUNTIME_PROVENANCE:                  SUPPORTED (6/6 frozen treatment fn hashes == live; harness-copy quarantined)
CACHE_TAX_SONNET:                    [pending Phase C]   preview EXPLORATORY: replicates (cc_frac 0.79 vs C0 0.035)
CACHE_TAX_HAIKU:                     [pending Phase C]
CACHE_TAX_CROSS_PROVIDER:            NOT_IDENTIFIABLE (gpt-5-5 exposes no cache-recreation estimand)
INTELLIGENCE_TAX_CAPABILITY_SCALING: [pending Phase D]
LINEDEDUP_ZERO_SHOT_TRANSPORT:       [pending Phase E]
GENTLE6K_ZERO_SHOT_TRANSPORT:        [pending Phase E]
DESTRUCTIVE_CAP_TRANSPORT:           [pending Phase D/E]
STATIC_POLICY_CROSS_PROVIDER:        [pending Phase E]
QUALITY_GENERALIZATION:              [pending — resolution rates per model]
CONTROLLER_GENERALIZATION:           NOT_TESTED — REQUIRES COMPLETED MRT  (hard)
```

## Limitations
- Smoke = 5 tasks (validity only). Phase C/D powered at 10 tasks × reps; Phase E at 30→50.
- gpt-5-5: provider-native cost only (no Anthropic cache weights); obs via tool-role adapter (frozen logic).
- All saving claims inherit the frozen study's non-robustness caveat until re-checked per model.

## Exact next action
Await Phase B smoke gate PASS → user GO → `GO=1 bash run_paid_phases.sh` → populate this file from analyzers.
