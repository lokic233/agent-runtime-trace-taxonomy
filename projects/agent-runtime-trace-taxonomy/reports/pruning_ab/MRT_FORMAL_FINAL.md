# MRT Formal — FINAL (Step 22)

> ## 🔬 STATISTICAL RECONCILIATION APPLIED (2026-07-01) — read this first
> This report is **Study 1**, relabeled *Protocol-valid, underpowered formal pilot / Study 1*.
> Several verdicts below were **corrected** in `MRT_STUDY1_STATISTICAL_RECONCILIATION.md` (raw
> data unchanged; hashes frozen):
> - **Policy value:** the "best static = pi_keep" claim was an **unnormalized-IPW artifact**.
>   Under **Hájek self-normalized IPW** and **DR**, best static = **pi_static**; pi_signal is
>   worse than both but CIs span zero ⟹ *NOT SUPPORTED BY POINT ESTIMATES; UNDERPOWERED.*
> - **Moderator:** ⟹ *UNDERPOWERED / NOT_ESTABLISHED* (b3 sign is descriptive only, not evidence).
> - **Placebo:** real |b3| is at the 91st pct of a 5,000-placebo distribution, block-perm p=0.92
>   ⟹ *NOT distinguishable from finite-sample placebo variation* (the "decisive falsification"
>   framing is retracted).
> - **Quality:** ⟹ *UNDERPOWERED* (risk diff −0.26, Newcombe CI [−0.61, +0.22]).
> - **Cache:** split into *PREFIX_BYTE_PRESERVATION (SUPPORTED, software invariant)* and
>   *CACHE_COST_EFFECT (DIRECTIONAL/UNDERPOWERED)*.
> The verdict prose below is retained for provenance; the reconciliation is authoritative.

**TraceController formal MRT study.** Frozen shim `df08cebcfd2b37c6`, git-frozen preregistration,
opus-4.7 temp=0, thinking OFF, SWE-agent 1.1.0, PlugBoard mTLS. All numbers auto-generated from
immutable artifacts. Consistency assertions: **14/14 pass** (+ reconciliation checks **17/17 pass**,
`consistency_assertions_v2.json`).

## Headline
A **protocol-conformant decision-level randomized experiment** ran cleanly end-to-end
(13 interventions, 0 infra failures, all byte-identity invariants held, stratified 2:2 blocks).
The realized sample is **N=13 ≪ 60-event floor** — the preregistered **outcome tier #4
(underpowered)**, exactly as the pre-launch power analysis predicted. No causal moderator or
controller value can be established at this N; the protocol path itself is validated.

## The eight verdicts (exact evidence)

**FORMAL_PROTOCOL_INTEGRITY: SUPPORTED.**
24/24 protocol tests pass on the frozen shim. Live: one intervention/task (13/13 distinct),
LINEDEDUP prefix byte-identical (7/7), NO_OP full-body byte-identical (6/6), completed blocks
exactly 2:2, 0 infrastructure failures, 0 synthetic fallbacks (fail-closed). 14/14 consistency
assertions pass.

**LINEDEDUP_ATE_H1: UNDERPOWERED.**
ATE = -192 eff-cost (≈3% of control mean),
95% CI [-3540, 3358], block-perm p=0.94. Estimate ≪ CI width. No detectable effect.

**REDUNDANCY_CAUSAL_MODERATOR: NOT_SUPPORTED (at this N, effectively UNDERPOWERED).**
Primary interaction b3 = 924 (SE 4670) — **wrong sign** (hypothesis was b3<0)
and CI overwhelmingly spans zero. A **task-id-hash placebo** produces a *larger* b3
(11078) than the real signal ⟹ indistinguishable from noise.

**H3_REWORK_SAFETY: UNDERPOWERED.**
ATE(H=3) = 468, CI [-8649, 9064]. No horizon-consistent signal; cannot certify rework safety either way.

**CACHE_PRESERVATION: SUPPORTED (mechanism, directional).**
Mechanism decomposition: LINEDEDUP mean cache_creation = 2471 vs NO_OP
2966 (diff -495); input_tokens ≈ 1 both arms; cache_read nearly
identical (diff -58). Consistent with the preregistered mechanism: **segment-local
transform preserves the materialized prefix** (no cache-busting, unlike recency methods). This
is a mechanism observation, not an identified mediated effect.

**QUALITY_GUARDRAIL: SUPPORTED (no collapse) but UNDERPOWERED (no fine claim).**
SWE-bench resolved by arm: LINEDEDUP 4/7, NO_OP 5/6. LINEDEDUP did not cause a
resolution collapse; the difference is well within noise at N=13.

**SIGNAL_POLICY_VALUE: NOT_SUPPORTED.**
pi_signal IPW=7424/DR=6863 is **worse** than best static
pi_keep IPW=5852/DR=6187. The point estimate itself fails to beat baseline.

**DEPLOYABLE_TRACECONTROLLER: NOT_SUPPORTED (PENDING larger study).**
Requires moderator + policy value + held-out online comparison — none achieved.

## Which of the four prespecified outcomes
**Outcome #4: the experiment is underpowered/blocked, with the exact reason documented.**
Reason: **single-shot × newest-only × opus-4.7 efficiency** caps online availability far below
the 60-event floor (18-task pool → 13 interventions; 5 tasks never produced a newest observation
with seg≥2000 & dup≥5). Growing N requires a much larger buildable task pool, not a code change.

## Permitted claim (from the preregistered ladder)
> We validate a protocol-conformant, decision-level randomized experimentation path for
> runtime trace interventions (byte-exact NO_OP control, single-shot per-task randomization,
> fail-closed provider handling, restart-safe stratified blocks). At the achievable sample
> (N=13), exact line-level redundancy is **not** established as a causal moderator of
> segment-local LINEDEDUP, and a redundancy-gated policy does **not** beat the best static
> policy. The cache-preservation mechanism is directionally confirmed. A powered evaluation
> requires a substantially larger buildable task pool and remains future work.

## What is explicitly NOT claimed
Not "controller validated"; not "redundancy is ground truth"; not "LINEDEDUP lossless"; not
"MRT produces per-event causal labels"; not "generalizes across models"; not "deployment ready".
