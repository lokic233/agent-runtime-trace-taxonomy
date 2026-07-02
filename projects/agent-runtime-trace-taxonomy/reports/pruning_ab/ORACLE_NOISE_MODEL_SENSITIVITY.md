# Oracle-Gap Noise-Model Sensitivity (P0.3)

Auto-derived from `results/pruning_ab/parity_study/oracle_noise_sensitivity.json`. Existing data only.
**Objective: determine whether ANY reasonable noise model permits a defensible positive lower bound
on real oracle headroom.** Not to recover a positive gap.

## Setup
- Observed naive oracle gap (ladder, provider-$ proxy, equal-weight): **21.7%**.
- SHAM noise floor: 10 tasks, median|rel Δcost|=0.31, mean|rel|=0.34,
  sd(rel)=0.43, MAD(rel)=0.44. **SHAM subset is 2.67× the 50-task mean cost** (high-cost subset).
- NULL = all 4 actions truly identical; observed cost = true cost + noise. If the null-manufactured
  gap ≥ observed, no positive lower bound is defensible under that model.

## Documented simulation assumptions
- multiplicative (lognormal) vs additive (gaussian) noise — both tested.
- homoskedastic across actions (primary) vs correlated-within-task (tested ρ∈{0.3,0.5,0.8}).
- independence across cells assumed (no repeated runs to estimate within-task action correlation).
- SHAM representativeness: 10 high-cost tasks only — a documented limitation; cheap/expensive split tested.
- sigma estimator varied: median|rel|/0.674, mean|rel|/0.798, sd(rel), MAD.

## Results — null-manufactured gap by model
| noise model | null gap % | ≥ observed? |
|---|---:|:--:|
| mult_lognormal_sigma[median_rel/0.674=0.46] | 40.9 | YES |
| mult_lognormal_sigma[mean_rel/0.798=0.42] | 38.0 | YES |
| mult_lognormal_sigma[sd_rel=0.43] | 38.7 | YES |
| mult_lognormal_sigma[mad_rel=0.44] | 38.6 | YES |
| additive_gaussian_homosked | 34.0 | YES |
| correlated_within_task_rho0.3 | 35.2 | YES |
| correlated_within_task_rho0.5 | 30.3 | YES |
| correlated_within_task_rho0.8 | 19.9 | no |

- **6 of 7 models** manufacture a gap (34–41%) **larger than** the observed 21.7% → no positive lower bound.
- Only **strong within-task correlation (ρ=0.8)** drops the null gap below observed (19.9%). But we have
  **no repeated-run data to estimate the true action-noise correlation**, so this is not a defensible basis.
- Cheap-half vs expensive-half observed gaps: 17.5% vs 22.9% — similar; the gap is not a
  pure high-cost-task artifact that a subset rescues (but both remain single-run).

## Verdict
- Any noise model where null < observed: **True** (only ρ=0.8).
- **Defensible positive lower bound: False.**
- Canonical wording: *No positive lower bound on real oracle headroom can be established from the current single-run retrospective matrix under any tested noise model. This is NOT the same as a true gap of zero.*

This corrects the earlier "bias-corrected oracle gap ~0%" to the accurate: **no positive lower bound
on real oracle headroom is establishable from this single-run matrix — which is NOT the same as a true
gap of zero.**
