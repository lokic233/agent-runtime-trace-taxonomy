# Oracle-Gap Analysis (existence probe on existing paid data)

Auto-derived from `oracle_gap.json`, `oracle_gap_bias_correction.json`. **Cost metric: provider
instance_cost ($, cache-aware) as a PROXY** for task-total effective cost (exact custom-weight cost
reconstructable only for 2 arms x 10 tasks; provider-$ corr with custom formula 0.67-0.74). Ladder
A0=C0, A1=M4, A2=M6, A3=M7. 50 tasks, 10 repos.

## Naive oracle gap (per-tolerance)
| eps | best static | naive gap % | distinct oracle actions | oracle choice |
|---|---|---:|---:|---|
| 0.0 | C0_identity | 15.0 | 4 | {'M6_env_log_collapse': 19, 'M4_obs_cap_5k': 13, 'M7_old_obs_elide': 4, 'C0_identity': 14} |
| 0.02 | C0_identity | 15.0 | 4 | {'M6_env_log_collapse': 19, 'M4_obs_cap_5k': 13, 'M7_old_obs_elide': 4, 'C0_identity': 14} |
| 0.05 | C0_identity | 15.0 | 4 | {'M6_env_log_collapse': 19, 'M4_obs_cap_5k': 13, 'M7_old_obs_elide': 4, 'C0_identity': 14} |
| 0.1 | C0_identity | 15.0 | 4 | {'M6_env_log_collapse': 19, 'M4_obs_cap_5k': 13, 'M7_old_obs_elide': 4, 'C0_identity': 14} |

**Tolerance is NOT binding** — the gap is identical across eps because quality barely differs across
actions and KEEP is the best static at every tolerance.

## The decisive noise control (why the ~15-22% gap is NOT real)
A **byte-identical NO_OP (SHAM)** moves task-total effective cost by a **median 31% (max 106%)** per
task, purely from run-to-run stochasticity. Simulating the NULL where all 4 actions are truly
identical with this noise:

| noise sigma | source | null-manufactured oracle gap |
|---|---|---:|
| 0.46 | SHAM median (31%) | **40.6%** |
| 0.30 | conservative | 28.1% |
| 0.20 | small | 19.5% |

**The observed naive gap (~15-22%) is BELOW the noise-null gap (40.6% at the SHAM-calibrated sigma).**
A min-over-4-single-draws manufactures a larger gap from pure noise than we observe. **Conservative
bias-corrected oracle gap: 0% (indistinguishable from the noise floor).**

## Robustness (all confirm the gap is noise, not signal)
- Split-sample bias correction (naive selection artifact only): still ~15% — because it corrects
  static-winner selection, NOT the per-task oracle min over noisy draws.
- Leave-one-repo-out naive gap: 18.1-23.5% — repo-stable, but this is
  the NOISE being repo-stable, not signal.
- Leave-top-k cost tasks (eps=0.05): {'drop_top1_eps0.05': {'oracle_gap_abs': 0.07882442857142846, 'oracle_gap_pct': 13.949570461407648}, 'drop_top3_eps0.05': {'oracle_gap_abs': 0.06835656382978716, 'oracle_gap_pct': 13.584744272120457}, 'drop_top5_eps0.05': {'oracle_gap_abs': 0.07139463333333329, 'oracle_gap_pct': 16.03592226754802}}.
- **0/50 tasks show a STABLE action crossing** (action_crossing.json); 10 are noise-dominated,
  40 are uncertain-single-rep.
