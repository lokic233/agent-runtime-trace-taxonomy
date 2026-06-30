# STATIC_POLICY_TRANSPORT (Phase E) — SKELETON

**Design:** Sonnet4.6 + Haiku4.5 + gpt-5-5 × {C0, LINEDEDUP, GENTLE6K, CAP1K} × golden-30 (→50 after gate).
**Cost:** anthropic effective-cost weights (frozen) for Claude; provider-native vs own-C0 for gpt-5-5 (NO anthropic weights).
**Two populations:** full fixed set (deployment) + common-support (stable-C0 tasks, defined from C0 only).
**No threshold tuning** (zero-shot transport of frozen actions). Anchor static: LINEDEDUP +6.3%, GENTLE6K +10.1% (bill-weighted, NON-robust).
**Populated from:** static_policy_transport.json (analyze_static_policy.py) + robustness.py.

## Results _[pending Phase E paid run]_
| model | LINEDEDUP saving% | GENTLE6K saving% | CAP1K saving% | beats C0? | beats best-static? |
|-------|-------------------|-------------------|----------------|-----------|---------------------|
| sonnet46 | | | | | |
| haiku45 | | | | | |
| gpt55 (native) | | | | | |

## Robustness (leave-top-k, repo-cluster, common-support) _[per analyze]_
## Transport verdicts: mechanism vs effect-size vs policy (kept distinct).
