# Held-Out Validation — Phase 6 (FINAL)

**167 held-out SWE-bench Verified tasks** (not in golden-50, all C0-baseline-resolved, repo-balanced, trajectory-stratified, integrity-preserved — HYBRID1 outcomes never inspected during selection). Frozen minimal suite: C0 / SHAM / HYBRID1.

## Outcome (the transfer question)

| metric | C0 | HYBRID1 |
|--------|---:|--------:|
| resolved | 160/167 (95.8%) | 160/167 (95.8%) |
| **net resolution change** | — | **0** |
| paired regressions | — | 4 |
| paired improvements | — | 4 |
| regression rate | — | 2.5% |
| regression loss_UB (95%) | — | **0.055** |

**HYBRID1 preserves aggregate solve rate exactly (160 = 160).** 4 regressions are balanced by 4 improvements — precisely the signature of run-to-run noise (the Phase 3 A/A floor was 5/10 flips on boundary tasks; here 8/167 flip in a balanced way). The regression rate 2.5% sits inside the A/A noise band.

## Token cost (the value question)

Computed from SWE-agent per-task model_stats (163 paired tasks):

| metric | mean | median |
|--------|---:|---:|
| tokens_sent saving | **−30.4%** | **−0.8%** |
| instance_cost saving | **−106.0%** | **−52.0%** |
| call delta | +0.1 | — |

**HYBRID1 does NOT reduce task-level tokens on held-out data** (median −0.8% = essentially zero), and **costs MORE** (median cost −52%) due to the prompt-cache-busting tax confirmed on golden-50. The mean is dragged sharply negative (−30% tokens, −106% cost) by the cache-bust outlier tasks.

## The five held-out questions, answered

1. **Does HYBRID1 reduce total task-level tokens?** NO. Median −0.8% (sent), median cost −52%. The per-call reduction does not survive to task-level cost.
2. **Does it preserve aggregate solve rate?** YES. 160/167 vs 160/167, net 0.
3. **Does it introduce excess success→failure flips beyond A/A/SHAM noise?** NO. 4 regressions = 4 improvements; regression rate 2.5% is within the A/A noise floor (which flips ~50% of *boundary* tasks; the held-out set is mostly stable tasks). loss_UB 0.055.
4. **Is risk concentrated in a predictable subset?** NO. The 4 regressions (django-13344, django-16100, sphinx-7440, sphinx-8551) do not match the golden-50 "fragile" set — they are different tasks, consistent with random noise, not a learnable fragility signature.
5. **Does a safety gate help?** See SAFETY_GATE_EVALUATION.md — NO.

## Verdicts established
- **HYBRID1_RESOLUTION_VERDICT: NONINFERIOR** — held-out solve rate preserved (160=160), excess regression within noise (loss_UB 0.055).
- **HELDOUT_TRANSFER_VERDICT: DOES_NOT_TRANSFER** — the golden-50 "+41.5% saving" does not transfer; held-out task-level token saving is ~0 (median) / negative (mean+cost). What transfers is the *null result*: no task-level cost benefit, solve rate merely preserved.

## Hard kill rules confirmed on held-out
- **#1 (no token improvement): CONFIRMED** — median −0.8% sent.
- **#2 (output/call growth cancels reduction): CONFIRMED** — median cost −52% from cache-busting.
- **#4 (golden-50 advantage disappears held-out): CONFIRMED** — there was no real advantage; the artifact disappears as expected.
- **#6 (depends on unstable tasks): CONFIRMED** — the entire per-task signal is run-to-run noise.
