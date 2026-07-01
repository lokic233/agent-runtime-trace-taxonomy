# MRT Confirmatory (Study 2) — Preregistration (FROZEN)

Auto-mirrors `results/pruning_ab/mrt_confirmatory/preregistration.json`. Committed **before** any
Study-2 treatment-control outcome is examined. **Independent** of Study 1.

## Relation to Study 1
INDEPENDENT. New tasks (not in Study-1), NEW seed 20260702, new randomization ledger. Study-1 outcomes used ONLY for variance/eligibility/power planning — NOT to tune threshold, select tasks, choose outcome, or pick model spec. NO pooling until Study-2 frozen+analyzed.

## Scientific question
Does pre-treatment exact line-level redundancy causally modify the effect of segment-local LINEDEDUP, and can that signal produce a policy that beats the best static policy?

Prespecified acceptable outcomes: moderates+policy-value, moderates-only, does-not-moderate, underpowered/blocked (documented). **Unacceptable:** protocol violation or estimator error presented as causal evidence; overstated claims.

## Decision unit
one task-level decision opportunity; <=1 randomized event/task (single-shot, newest observation, first available main-agent call).

## Treatment / control / signal
- **LINEDEDUP:** segment-local LINEDEDUP (remove newest-obs lines whose stripped form >=12 chars appears in a prior observation; prefix byte-identical; actual_changed from real serialized diff).
- **NO_OP:** byte-identical NO_OP (only the transport normalization applied identically to BOTH arms).
- **Signal:** continuous exact duplicate_line_fraction (pre-treatment).
- **Frozen policy:** pi_signal = LINEDEDUP iff dup_frac > 0.40 (threshold FROZEN, identical to Study-1; NOT tuned on Study-1 outcomes).

## Base availability (dup_frac is a CONTINUOUS moderator)
newest observation AND segment_chars>=2000 AND duplicate_line_count>=5 AND LINEDEDUP would remove >=1 complete line. dup_frac is a CONTINUOUS moderator (NO dup_frac gate on availability).
Strata: HIGH = `dup_frac>0.40`, MIXED = `0<dup_frac<=0.40 & dup_count>=5`.

## Randomization
stratified permuted-block, block size 4 (2 LINEDEDUP/2 NO_OP), SHA-256 Fisher-Yates from seed 20260702|stratum|block_id (no python hash()). Propensity 0.5. Append-only ledger, atomic-before-mutation, restart-reconstructed, conflict=>abort.

## Outcomes
- **Primary:** `effective_cost_h1 = input + 0.1*cache_read + 1.25*cache_creation + 5*output (lower=better; weights frozen; raw components stored).`
- **Secondary:** effective_cost_h3 (intervention + next 2 MAIN-AGENT responses; internal calls excluded; truncation recorded), H=3 rework proxies, SWE-bench resolved (quality guardrail)

## Primary model (estimable at expected N)
```
Y_i = alpha_block(i) + beta1*A_i + beta2*S_i + beta3*A_i*S_i + error_i
```
- A = LINEDEDUP assignment (ITT); S = centered dup_frac (center = Study-1 available-event median, frozen)
- **beta3** = PRIMARY moderator parameter (negative => redundancy makes LINEDEDUP more favorable)
- Inference: block-respecting randomization inference for beta3 (primary); repo-clustered / repo-bootstrap uncertainty (secondary).
- block FE + beta3 only (no repo FE + many covariates at expected N). ITT primary.
- Secondary ANCOVA covariates (prespecified): prespecified variance-reduction covariates {log(segment_chars), calls_so_far, prior-call effective cost, prior cache state} — SECONDARY only.
- **Forbidden:** NEVER control for post-treatment variables (characters_removed, future calls, rereads, task resolution).

## Controller policies (frozen)
`pi_keep`=always NO_OP · `pi_static`=always LINEDEDUP when available · `pi_signal`=LINEDEDUP iff dup_frac>0.40
- Estimators: Hajek self-normalized IPW (primary) + cross-fitted doubly-robust (LORO folds) + block-aware CI + leave-one-repo-out cross-fitting.
- **Supported iff:** pi_signal beats BOTH pi_keep and pi_static on the primary estimator with credible uncertainty AND no quality collapse.
- Report separately: moderator evidence, policy-value evidence, deployability evidence

## Quality non-inferiority (margin FROZEN before outcomes)
- Margin: risk-difference margin = -0.15 (LINEDEDUP resolution may be at most 15pp below NO_OP to claim non-inferiority), justified from baseline resolution ~0.5-0.7 and workshop deployment tolerance. FROZEN before outcomes.
- Report: arm resolution rates, risk difference, Newcombe/Wilson CI, non-inferiority result
- If insufficient: QUALITY_NONINFERIORITY: UNDERPOWERED (no-catastrophic-collapse is descriptive, not a safety guarantee).

## Negative controls
- SHAM: separate SHAM calibration cohort (byte-identical transform-path traversal, randomized vs NO_OP); test whether dup_frac modifies SHAM-vs-NO_OP cost. NOT mixed into primary two-arm estimand.
- Placebo: >=5000 deterministic placebo moderators + event-id-hash placebo + block-respecting interaction permutation.
- Sensitivity (secondary only): threshold {0.30,0.40,0.50}, leave-top-k {1,3,5}, leave-one-repo-out, H1/H3/task-total, pricing weights

## Power & precision (frozen)
- 80% moderator power INFEASIBLE at N<=400 given Study-1 variance (power_b3=0.27 at N=400).
- **Mode:** PRECISION · **Primary target:** ATE(H1) 95% CI half-width <= 1000 eff-cost (~16% of mean), expected ~N=160
- **Hard floor:** >=60 eligible events, >=25/arm, both strata, >=5 repos
- **Stopping rule:** stop when ATE CI half-width<=1000 AND >=60 events; OR all buildable pool tasks attempted. NEVER on p-value/sign/trend.

## Missing data
infrastructure_failure (fail-closed 502) in the H1/H3 window => task EXCLUDED, classified BEFORE outcome analysis, logged. NEVER rerun a completed task for an unfavorable outcome.

## Model & pool
- anthropic/claude-opus-4-7, temp 0.0, thinking OFF, PlugBoard mTLS, SWE-agent 1.1.0.
- Task pool: NEW tasks from SWE-bench Verified (500) minus golden-50. 450 candidates. Pool size finalized from the eligibility dry-run online availability rate (Part-VII).

## Frozen code hashes (sha256[:16])
- `mrt_confirmatory_shim.py` = `87b0043ab8c2194c`
- `test_mrt_confirmatory_protocol.py` = `d0d30055134ae882`
- `join_h3_confirmatory.py` = `3bc25c2c56a9b3ad`
- `analyze_mrt_formal.py` = `0a2437b9ea5d40e2`
- `power_precision_confirmatory.py` = `e441336de0d7e852`

Protocol tests: **26/26 PASS**. Main-agent-call audit: **24/24 trajectories consistent (>=20 required)**.
Seed: **20260702**. Study id: **study2**.
