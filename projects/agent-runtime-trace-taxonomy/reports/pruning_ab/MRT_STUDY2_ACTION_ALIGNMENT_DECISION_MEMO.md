# Final Decision Memo — Hostile Committee (Study-2 reconciliation + action-alignment discovery)

**Prepared for adversarial statistical review. Analysis-only; sealed N=70; 17 raw files verified
unchanged; no new trajectories or interventions run. Reconciliation tests 22/22; invariant checks 13/13.**

## 1. Does Study 2 remain confirmatory after reconciliation?
**Partially.** Study 2 is a valid, protocol-clean randomized replication, but for the MODERATOR and
CONTROLLER questions it is **underpowered / not established**, not confirmatory. It IS confirmatory
for: protocol integrity, prefix byte-preservation (software invariant), and marginal quality NI at
the frozen margin. The sealed analysis's positive-leaning framing does not survive the corrected
estimators.

## 2. Every preregistration deviation
1. **Block fixed effects omitted** in the sealed moderator model → repaired (block FE, 18 blocks).
2. **Moderator center recomputed from Study-2 median (0.35067)** instead of the frozen Study-1
   available-event median (0.3429275) → repaired. **Materiality: none for b3** (b3 is algebraically
   center-invariant = +931.6 for all centers); the deviation matters in principle but did not change
   the primary parameter.
3. **Incomplete-block randomization inference** conditioned on the realized 2-treated prefix of the
   one incomplete block (HIGH:7=[LI,LI]) → repaired (draw from full 2:2 design space; marginal
   propensity verified 0.5; observed assignment in reconstructed space).
4. **Placebo "percentile" mislabel** → corrected (upper-tail probability vs empirical rank).
5. **DR own-outcome fallback** possible in sealed code → repaired (leakage-free, 0 own-outcome
   fallbacks, hard assertion passes).
6. Classical OLS SE was the only moderator SE → now classical + HC3 + repo-cluster reported.

## 3. Corrected primary estimates
- **ATE H1** (unadjusted DESCRIPTIVE): -995 eff-cost (LINEDEDUP cheaper);
  block-FE A coef with repo-cluster CI crossing zero; **tail-sensitive** (leave-top-3 attenuates markedly).
- **Moderator b3** = 932 (hypothesized <0 → WRONG sign), repo-cluster 95% CI
  [-5600, 7463]; sharp-null p=0.73;
  real |b3| exceeds only ~26% of distribution-preserving placebos.
- **Quality**: risk diff +0.13, Newcombe [−0.083, +0.334], marginal NI met at −0.15 (binary resolution only).

## 4. Does always-LINEDEDUP remain the best static policy?
**Yes, on BOTH estimators.** Hájek pi_static=5460 < pi_keep=6455 < pi_signal=6186;
DR agrees. pi_signal − pi_static = +726 (worse). The Study-1
unnormalized-HT ranking that favored pi_keep is an artifact and is NOT revived.

## 5. Does any feature family show stable signal–action alignment?
**No.** 5 families + 2 interactions tested. Removal/liveness/recoverability/interactions FAIL
(positive V_exc−V_static). F4 cache-geometry (−80) and F5 trajectory-state (−156) have nominally
negative point gains but repo-bootstrap CIs [−1024,+1037] and [−849,+591] span zero, and F4
attenuates sharply under leave-top-k. Advantage calibration is **non-monotonic and inverted** in
the extreme bin → the learned advantage ordering is not trustworthy at N=70.

## 6. Does any candidate exception policy beat always-LINEDEDUP?
**No.** All 3 frozen candidates: C1_cache_geometry gain=-80 CI[-1024,1037], C2_trajectory_state gain=-156 CI[-849,591], C3_interpretable_rule gain=+59 CI[-50,195]. All CIs span zero. any_supported = False.

## 7. Evidence classification
- Protocol integrity, prefix preservation: **CONFIRMATORY** (software invariants).
- Marginal quality NI: **CONFIRMATORY at the frozen margin** (precision limited).
- ATE H1 direction: **EXPLORATORY / UNDERPOWERED** (favorable but imprecise, tail-sensitive).
- Redundancy moderator: **NOT SUPPORTED / UNDERPOWERED**.
- Any action-alignment signal / exception policy: **NOT SUPPORTED** (exploratory discovery, credible null).

## 8. Should Study 3 proceed?
**Not now.** Discovery produced no candidate meeting the preregistration bar (no CI excludes zero,
calibration inverted). A Study-3 preregistration is DRAFTED and FROZEN
(`MRT_STUDY3_ACTION_ALIGNMENT_PREREGISTRATION.md`) but should run only if (a) a larger discovery
dataset first yields a stable candidate, or (b) the committee explicitly wants to confirm the null.

## 9. Candidate policy eligible for preregistration
**None.** No exception policy is eligible; all are exploratory with CIs spanning zero.

## 10. Strongest claim the workshop paper may safely make
> "Across an independent randomized replication (N=70, 11 repos), exact line-level redundancy did
> not identify decision points at which LINEDEDUP was more valuable, and a redundancy-gated policy
> failed to beat blanket LINEDEDUP. A pre-treatment feature-based exception detector (liveness,
> recoverability, cache geometry, trajectory state) also failed to yield stable incremental policy
> value. LINEDEDUP showed a favorable but imprecise, tail-sensitive H1 cost direction while meeting
> the preregistered marginal quality non-inferiority criterion. These results validate the
> experimental substrate but not a deployable TraceController; exact syntactic redundancy is an
> opportunity signal, not an action-value signal."

**The committee's preference for a credible negative over a fragile positive is satisfied: we report
no supported controller.**
