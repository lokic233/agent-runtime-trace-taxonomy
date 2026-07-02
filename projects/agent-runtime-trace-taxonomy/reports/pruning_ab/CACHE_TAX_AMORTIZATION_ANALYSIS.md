# Cache-Tax Amortization Analysis

Exact cache-aware decomposition available for **C0 (A0) vs HYBRID1 (aggressive recency), 10 tasks**
(the only arms with per-call cache ledgers). net_saving = baseline_task_total - transformed_task_total.

## Finding: aggressive recency compaction is dominated by cache tax
- net saving **negative on 9/10 tasks** (mean -744799, median -738357 effective-cost units).
- Cache ratio (cache_read:cache_creation) collapses from A0 ~11.8 to aggressive ~0.37 — the transform
  BUSTS the prefix cache, and cache recreation cost swamps the direct prompt saving.
- Break-even: because the recency transform mutates the prefix on essentially every call, there is
  no byte-stable compacted prefix to amortize over; H_break_even is effectively never reached within
  realized horizons.

## Implication for the action ladder
A3-recency (cache-busting) is a **net cost INCREASE**, not a saving. Only content-stable transforms
(A1/A2, prior evidence cache ratio 13-14x) preserve the cache. This is consistent with the overall
negative: the aggressive end of the ladder loses after the cache tax, so there is no cost regime in
which an aggressive action is worth selecting — removing the main mechanistic route to action parity.
