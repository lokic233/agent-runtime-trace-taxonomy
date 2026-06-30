# Part 4 — What Existing Data Can Recover

## Reconstructed (decision_event_manifest.jsonl)
3,476 per-call decision events from the v2 task-tagged ledgers, with: task/repo/method/call_index, action_fired, chars_removed, tokens_removed, first_changed_msg_index, per-call cache_read/cache_creation/output/latency, timestamp.

## NOT recoverable from current logs
- **Segment content** (which exact lines were removed) — ledger stores counts, not the removed text. Cannot compute reuse-distance, recoverability, or reread-of-removed-content retrospectively.
- **Reread detection** — would need to match removed content against future observations (content not stored).
- **Prefix-aligned feature values** — would need to replay each prefix; not stored.

## Counterfactual classification (honest)
| class | count | meaning |
|-------|------:|---------|
| PAIRED_TASK_ONLY | 1863 | task-level C0 baseline exists; no event-level match |
| COUNTERFACTUAL_UNIDENTIFIED | 1613 | post-divergence fired calls; no matched C0 state |
| RANDOMIZED_COUNTERFACTUAL_AVAILABLE | 0 | **none — no randomization was done** |

## Verdict
**Observational method runs do NOT provide randomized event-level counterfactuals.** Event-level CATE is **COUNTERFACTUAL_UNIDENTIFIED** from current data. Proceeding to experimental design (micro-randomized trial, Part 6) is the only valid path to the decision-level causal estimands.
