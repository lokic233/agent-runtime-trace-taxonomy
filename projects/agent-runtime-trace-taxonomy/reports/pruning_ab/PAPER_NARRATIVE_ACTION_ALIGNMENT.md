# Paper Narrative — Action Alignment (Study 2 reconciliation + discovery)

Evidence hierarchy (each layer distinct; earlier negatives NOT overwritten):
1. **Cache tax** — supported (earlier work).
2. **Intelligence tax** — supported (earlier work).
3. **Task-level observational policy** — failed (no observational signal converts oracle gap to value).
4. **Study 1** — protocol-valid, underpowered pilot (N=13).
5. **Study 2** — independent randomized replication (N=70, 11 repos), reconciled with the
   preregistered block-FE moderator model, frozen center, corrected incomplete-block randomization
   inference, leakage-free DR.
6. **Directionally favorable but imprecise blanket LINEDEDUP.** H1 ATE ≈ −995 eff-cost (LINEDEDUP
   cheaper) but repo-cluster CI crosses zero and the mean is tail-sensitive (leave-top-5 attenuates).
7. **Exact redundancy fails as an action signal.** Moderator b3 = +931 (wrong sign), sharp-null
   p≈0.73, real |b3| exceeds only ~26% of distribution-preserving placebos. pi_signal (dup_frac>0.40)
   is *worse* than always-LINEDEDUP (+726, Hájek).
8. **Action-alignment discovery fails too.** No pre-treatment feature family (removal opportunity,
   semantic liveness, recoverability, cache geometry, trajectory state) yields an exception policy
   that credibly beats always-LINEDEDUP (all repo-bootstrap CIs span zero; advantage calibration
   inverted at N=70).
9. **Marginal quality non-inferiority** under the frozen −0.15 margin is met (risk diff +0.13,
   Newcombe lower bound −0.083), but this is binary resolution only, not broad safety.
10. **No deployable TraceController.**

## Strongest permissible claims
- "Exact syntactic redundancy is an **opportunity** signal, not an **action-value** signal."
- "Across an independent randomized replication, exact line-level redundancy did not identify
  decision points at which LINEDEDUP was more valuable, and a redundancy-gated policy failed to
  beat blanket LINEDEDUP. LINEDEDUP showed a favorable but imprecise, tail-sensitive H1 cost
  direction while meeting the preregistered marginal quality non-inferiority criterion. These
  results validate the experimental substrate but not a deployable controller."
- If no stable exception rule (current state): "Neither task-level observational features nor
  decision-level syntactic/semantic features reliably improve over the best static transformation
  policy, motivating larger randomized datasets and direct learning of action-specific
  counterfactual value."

## Forbidden claims
Not: deployable TraceController · validated individual treatment-effect prediction · per-event
causal labels · cross-model generalization · production safety · semantic-liveness discovery ·
policy improvement without held-out uncertainty · "LINEDEDUP causally saves 15%" · "LINEDEDUP lossless".
