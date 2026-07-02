# Paper Narrative — Canonical

Primary narrative reference. Aligned with TRACECONTROLLER_CANONICAL_EVIDENCE_MATRIX.md.

## Four scientific layers (keep distinct)
**Layer 1 — Measurement.** Trace features expose rereading, looping, no-new-evidence streaks, patch
churn, environment failures, and trajectory growth. *Established (associational).*

**Layer 2 — Mechanism.** Runtime optimization decomposes as: direct token saving − cache tax −
rework tax − recovery tax − quality loss. Recency prefix rewriting destroys prefix-cache reuse
(net-negative); content-stable transforms preserve it. *Established (mechanistic + directional).*

**Layer 3 — Static primitives.** Some low-risk transformations — notably prefix-preserving line
deduplication — are useful as static, compiler-like passes within their eligible region. *Supported
as a static primitive; quality non-inferior at the frozen marginal margin.*

**Layer 4 — Adaptive control.** Requires (a) real action crossing, (b) pre-treatment predictability,
(c) policy improvement over the best static policy, (d) independent validation. **Current evidence
does not establish Layer 4.** It is neither established nor globally falsified: the NO_OP-vs-LINEDEDUP
controller is a credible negative at N=70, and the retrospective action matrix is non-diagnostic
(single-run, below the SHAM noise floor).

## Strongest safe claim (canonical wording)
> Visible token reduction is not equivalent to runtime cost reduction. Cache reconstruction,
> trajectory rework, and stochastic action-ranking noise can reverse or fabricate apparent
> optimization gains. Across the evaluated transformations, prefix-preserving line deduplication
> remains a useful low-risk static primitive, while neither syntactic gating nor the existing
> retrospective action matrix provides sufficient evidence for trace-conditioned adaptive control.

Optional forward-looking sentence:
> We therefore identify repeated, noise-calibrated action-parity testing as a necessary prerequisite
> for future tolerance-conditioned controllers.

## Do NOT claim
Deployable/production TraceController · validated individual treatment-effect prediction · per-event
causal labels · cross-model generalization · production safety · that general action parity has been
disproven · that the retrospective oracle gap is exactly zero · that M4 is actual LINEDEDUP · any
merge of H1 / H3 / task-total cost.

## Standalone methodological contribution — "Why single-run per-task oracles are invalid for stochastic agents"
This may be the strongest reusable contribution of the work.
- **Min-over-actions selection bias.** Taking the per-task minimum cost over k actions, each measured
  once, is a biased-downward estimator: it capitalizes on run-to-run noise. E[min of k noisy draws]
  is systematically below the true best.
- **Byte-identical SHAM controls.** A byte-identical no-op re-run moves task-total effective cost by
  a median ~31% (max ~106%) here — a large noise floor that a single run cannot see.
- **Run-to-run trajectory variance.** Stochastic agents diverge even at temperature 0 (tool outputs,
  ordering, retries), so identical inputs yield different trajectories and costs.
- **Repository stability is not validation.** A noise-manufactured oracle gap is repo-stable because
  the *noise* is repo-stable; repo-stability does not distinguish signal from noise.
- **Repeated task-action cells are necessary.** Only repetition (with an embedded SHAM and a
  repetition-aware/bias-corrected oracle) can separate a true action crossing from noise.
