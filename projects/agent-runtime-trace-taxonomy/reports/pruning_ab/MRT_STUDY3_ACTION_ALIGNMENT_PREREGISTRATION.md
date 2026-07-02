# MRT Study-3 — Action-Alignment Validation Preregistration (DRAFT; NOT RUN)

**Status: DRAFT preregistration. Study 3 is NOT executed and MUST NOT be run without explicit
instruction.** This document freezes the design so that IF a candidate exception policy is ever
validated, it is done confirmatorily and independently of the Study-2 discovery data.

## Motivation
Study-2 discovery (SIGNAL_ACTION_ALIGNMENT_DISCOVERY.md) found **no** pre-treatment feature family
or candidate exception policy that credibly beats always-LINEDEDUP (all repo-bootstrap CIs span
zero; advantage calibration inverted). Therefore Study 3 is a **high-risk confirmatory attempt**,
and the most likely honest outcome is a confirmed null. It is preregistered only so that a future
run is disciplined, not because the discovery evidence warrants optimism.

## Independence & anti-leakage
- **New task pool** — tasks NOT in Study 1 or Study 2 (verified by task_id set difference).
- **New run ID** `study3_action_alignment`, **new immutable ledgers**, **new randomization seed 20260703**.
- **No pooling** with Study 2 before Study 3 is frozen AND analyzed.
- Study-2 outcomes may inform ONLY: variance/eligibility estimates and the frozen feature extractor
  + frozen candidate policies. They may NOT change the 0.40 threshold, outcome weights, or model spec.

## Frozen inputs (to be hashed at freeze time)
- **Feature extractor:** `extract_pretreatment_features.py` (frozen sha).
- **Candidate policies:** the ≤3 in `candidate_exception_policies.json` (frozen sha). Since none is
  currently supported, Study 3 should evaluate them **off-policy first** and treat any as exploratory.
- **Outcome:** effective_cost_h1 with frozen weights {input:1, cache_read:0.1, cache_creation:1.25, output:5}.
- **Quality margin:** risk-difference NI margin −0.15 (frozen).
- **Propensity:** 0.5, stratified permuted 2:2 blocks.

## Primary estimand
**V(pi_exception) − V(pi_static)** on effective_cost_h1 (lower better), via Hájek IPW (primary) +
LORO cross-fit DR (secondary), repo-cluster bootstrap CI. NOT an interaction coefficient.

### Success criteria (ALL required)
1. pi_exception lower cost than always-LINEDEDUP with repo-cluster 95% CI excluding 0;
2. no quality degradation beyond frozen −0.15 margin (Newcombe);
3. sign-stable across repository folds (worst-fold gain ≤ 0);
4. nontrivial but controlled override coverage (prespecify e.g. 5–40%);
5. robustness to leave-top-{1,3,5} and winsorization.

## Design
- **Arms:** Arm 1 LINEDEDUP, Arm 2 byte-identical NO_OP (continue randomized action assignment to
  keep treatment effects estimable). The candidate controller is evaluated **off-policy** first.
- Only after a frozen off-policy evaluation succeeds should an online policy-vs-static experiment
  be considered.

## Power / precision
Use Study-2 variance to size N for a target CI half-width on V(pi_exc)−V(pi_static). Given Study-2's
policy-contrast CI half-width (~±1000 eff-cost at N=70), detecting a plausible small exception gain
likely requires several hundred eligible interventions; precision-based stopping preferred over an
infeasible power target. Full simulation to be run at freeze time.

## Enrichment (optional, bias-controlled)
If the candidate targets a rare region, Study 3 MAY oversample using ONLY frozen pre-treatment
features; log sampling probabilities; keep known propensities; retain a representative sample; and
account for the sampling design in policy-value estimation.

## Stopping rule
Prespecified eligible-event target OR buildable-pool exhaustion. NEVER stop on observed effect/p-value.

## Prespecified acceptable outcomes
(1) exception policy validated (beats always-LINEDEDUP, quality ok, stable); (2) not supported;
(3) underpowered/blocked. All acceptable. A fragile positive is NOT acceptable.
