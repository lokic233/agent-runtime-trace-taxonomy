# MRT Formal — Controller Policy Value (Step 20)

Auto-generated from `results/pruning_ab/mrt_formal/controller_policy_values.json`. N=13.
Frozen policies, IPW + doubly-robust, propensity 0.5, **lower cost = better**.

| policy | IPW cost | DR cost |
|---|---:|---:|
| `pi_keep` (always NO_OP) | 5852 | 6187 |
| `pi_static` (always LINEDEDUP) | 6620 | 6060 |
| `pi_signal` (LINEDEDUP iff dup_frac>0.40) | 7424 | 6863 |

**Best static = pi_keep** (IPW 5852). The signal policy `pi_signal`
(IPW 7424) is **worse** than the best static policy on both IPW and DR.
⟹ **Controller value NOT supported.** (No CI needed to reject: the point estimate itself does
not beat the baseline, and at N=13 any CI is enormous.)

Distinguish, per preregistration:
- moderator supported: **NO**
- policy value supported: **NO**
- deployable controller supported: **NO** (would additionally require held-out online comparison)
