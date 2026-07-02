# Repeated-Oracle Estimation Plan (DESIGN ONLY)

The retrospective study proved a raw min-over-noisy-cells oracle is invalid for stochastic agents.
Any future oracle-gap estimate MUST use a repetition-aware, bias-corrected estimator. Options
(specify ≥1 as primary before outcomes):

1. **Hierarchical partial pooling.** Model task-total cost C[task,action,rep] ~ task effect +
   action effect + task×action interaction + rep noise (log scale). Shrink task×action estimates
   toward the action mean. Oracle = per-task argmin of the **posterior mean** action cost, not the
   raw sample min. Reports posterior uncertainty on the oracle gap.
2. **Posterior expected action value + P(optimal).** For each task, compute the posterior probability
   each action is the cheapest feasible action. A task is a **stable crossing** only if
   P(action a is optimal) exceeds a threshold (e.g. 0.8) for an a ≠ global best static, with a
   meaningful cost margin.
3. **Split task-action repetitions.** Use half the reps per cell to SELECT the per-task action,
   the other half to EVALUATE it. This removes the winner's-curse the retrospective split-sample
   missed (it split tasks, not reps).
4. **Bias-corrected minimum.** Subtract the expected min-of-k-noisy-draws downward bias (estimated
   from the embedded SHAM variance) from the naive oracle.
5. **Conservative lower confidence bound.** Report the lower end of a repo-clustered bootstrap CI on
   (best_static − oracle); require this LCB > 0 (and > practical threshold) before claiming headroom.

## Definition of a stable crossing (frozen)
A task counts as a stable crossing ONLY if repeated evidence supports a different optimal (feasible)
action than the global best static, with (a) P(optimal) > 0.8 under partial pooling, AND (b) a cost
margin exceeding the practical threshold, AND (c) sign-consistency across repetition splits.

## Reporting requirements
- naive oracle gap (for comparison only, flagged as biased);
- bias-corrected / posterior oracle gap with CI;
- number of stable-crossing tasks (by the frozen definition);
- fraction of apparent crossings attributable to noise (via embedded SHAM null);
- aggregate cost-weighted AND equal-weight task-level; repo-clustered; leave-one-repo-out.

## Non-negotiables
- Never report a raw min-over-single-run-means oracle as evidence of headroom.
- Never treat repo-stability of a gap as validation (repo-stable noise is still noise).
- Keep H1, H3, and task-total oracle gaps as separate estimands.
