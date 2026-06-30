# Phase 2 — MRT Blind Annotation (COMPLETE, frozen)

## Results (auto-generated from mrt_blind_annotations.jsonl at freeze)
- **262 valid annotations** (6 errors) across **~88 decision events** × **3 annotator roles**
- Balance gate: **PASS** (LINE_DEDUP=58 ≥ 30, total prune=79 ≥ 30)

### Action distribution (the key fix validation)
| preferred_action | count | % |
|------------------|------:|---:|
| LINE_DEDUP | **58** | 22% |
| KEEP_FULL_CONTENT | 158 | 60% |
| RETRIEVABLE_REFERENCE | 13 | 5% |
| NO_OP | 25 | 10% |
| GENTLE_CAP | 8 | 3% |

**Prior batch (selection-biased): 0 LINE_DEDUP in 132 annotations. This batch: 58 LINE_DEDUP.**
The action-opportunity sampler (Phase 1) corrected the selection bias entirely.

### What this enables (Phase 4-6)
With 58 LINE_DEDUP + 158 KEEP recommendations across stratified events, the preregistered interaction test has power: does LINE_DEDUP's effect differ on events where all 3 annotators said "LINE_DEDUP" vs events where they said "KEEP"? That is the causal moderation question.

## Phase 4 status: READY TO LAUNCH
The MRT shim (scripts/mrt_shim.py) is built and smoke-tested. The single-intervention-per-task randomized pilot requires a full SWE-agent run through the shim on 50 golden tasks (~30-60 min). Annotations are frozen; hypotheses preregistered; the next step is execution.
