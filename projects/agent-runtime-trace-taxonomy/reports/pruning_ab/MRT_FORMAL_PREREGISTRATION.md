# MRT Formal — Preregistration (Step 11, FROZEN)

**Frozen 2026-07-01** · auto-mirrors `results/pruning_ab/mrt_formal/preregistration.json`.
Committed **before** any treatment-control outcome is examined. Code hashes frozen below.

## Scientific question
Can a pre-treatment, decision-level trace signal (**exact line-level redundancy in the newest
tool observation**) identify when **segment-local LINEDEDUP** causally improves execution utility?

Target = the **action × signal interaction** τ(s) = E[Y(LINEDEDUP) − Y(NO_OP) | dup_frac = s],
NOT ordinary outcome prediction and NOT merely the average LINEDEDUP effect.

## Four distinct claims (not conflated)
1. **Mechanism** — segment-local transform preserves the materialized prefix.
2. **ATE** — LINEDEDUP helps/hurts on average among available events.
3. **Causal moderator** — the LINEDEDUP effect changes as redundancy changes (`b3`).
4. **Controller value** — a signal-conditioned policy beats the best static policy.

## Decision unit
One task-level decision opportunity. **≤1 randomized event per task** (single-shot, newest
observation, first available call). Task marked permanently intervened; never re-randomized.

## Treatment / control
- **LINEDEDUP:** remove newest-obs lines whose stripped form (≥12 chars) appears in a prior obs;
  append `[N duplicate lines elided]`; **prefix byte-identical**; `actual_changed` from real
  serialized diff.
- **NO_OP:** body byte-identical after the identical transport normalization applied to BOTH arms.

## Eligibility (base availability — NO dup_frac gate)
newest obs · `segment_chars ≥ 2000` · `dup_lines ≥ 5` · LINEDEDUP removes ≥1 line.
`duplicate_line_fraction` is a **continuous pre-treatment moderator**, centered at the median
dup_frac of pre-experiment C0 available events (frozen before outcome analysis).

Strata: **HIGH_REDUNDANCY** dup_frac>0.40 · **MIXED_REDUNDANCY** 0<dup_frac≤0.40 & dup_lines≥5.

## Randomization
Stratified **permuted-block**, block size 4 (2 LINEDEDUP / 2 NO_OP). Block sequence from
`SHA-256(seed|stratum|block_id)` Fisher-Yates (**no python `hash()`**), seed 20260701,
propensity 0.5. Persisted append-only; reconstructed on startup; ledger conflict → abort.

## Outcomes
- **Primary:** `effective_cost_h1 = input + 0.1·cache_read + 1.25·cache_creation + 5·output`
  (lower better; weights frozen; raw components stored for pricing sensitivity).
- **Secondary:** `effective_cost_h3` (intervention + next ≤2 responses), H=3 rework proxies,
  SWE-bench resolved (task-level guardrail, expected underpowered).

## Estimands & analysis
- **Primary estimand:** ITT ATE(LINEDEDUP − NO_OP) on `effective_cost_h1` among available events.
- **Interaction model:** `Y = b0 + b1·A + b2·S + b3·A·S + block FE + [log(seg_chars), calls_so_far, repo FE]`;
  `b3` is the **primary moderator parameter** (negative ⟹ redundancy makes LINEDEDUP more favorable).
- **Contrasts:** CATE_HIGH, CATE_MIXED, CATE_HIGH − CATE_MIXED (secondary).
- **ITT primary** — NOT conditioned on `actual_changed`. Report assignment/activation/dose separately.
- **Inference:** randomization-consistent diff + bootstrap CI + repo-clustered bootstrap +
  block-permutation. Report point est + 95% CI + N + missingness + balance + effect size —
  **not only p-values**. Few repos ⟹ cluster inference labeled low-resolution.

## Controller policies (frozen)
`pi_keep` = always NO_OP · `pi_static` = always LINEDEDUP when available ·
`pi_signal` = LINEDEDUP iff dup_frac>0.40 (**threshold frozen**). Value via IPW + doubly-robust +
block-aware CI + leave-one-repo-out cross-fit. Value SUPPORTED only if `V(pi_signal)` beats
`min[V(pi_keep), V(pi_static)]` with credible CI and acceptable quality.

## Falsification / robustness (all run)
SHAM negative control · placebo moderators (task-id / event-id hash) · block-respecting
permutation · leave-top-1/3/5 · leave-one-repo-out · threshold {0.30,0.40,0.50} · horizon
{H1,H3,task-total} · pricing sensitivity (frozen weight set).

## Missing-data rule
A task with an `infrastructure_failure` (fail-closed 502) in its H=1/H=3 window is **excluded**
and classified **before** outcome analysis; logged, never silent. **Never** rerun a completed
task for an unfavorable outcome.

## Power & stopping (frozen)
H=1 SD≈2136. MDE ATE −570 / interaction −2000, target power 0.80. **Finding: UNDERPOWERED at
feasible N** (pool ceiling ≤18 interventions ≪ 60-event floor). **Stopping rule:** stop at 60
eligible events OR all buildable tasks attempted; **never on observed p-value/trend**.

## Model
anthropic/claude-opus-4-7 · temp 0.0 · thinking OFF · PlugBoard mTLS · SWE-agent 1.1.0.

## Frozen code hashes
See `preregistration.json.code_hashes`. Protocol tests: **24/24 PASS** (MRT_FORMAL_PROTOCOL_AUDIT.md).

## Prespecified acceptable outcomes (no positive-result optimization)
1 moderates+policy-value · 2 moderates-only · 3 does-not-moderate · **4 underpowered/blocked (documented)**.
All four are scientifically acceptable. Protocol violations and overstated claims are not.
