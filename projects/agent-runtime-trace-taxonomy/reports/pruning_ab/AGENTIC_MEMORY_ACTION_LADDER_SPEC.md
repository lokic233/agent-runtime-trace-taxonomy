# Agentic-Memory Action Ladder — Specification (DESIGN ONLY, NOT RUN)

Design for the next parity-bearing action family. Motivation: unlike prefix-rewriting compression,
agentic memory can create a **real cost–quality tradeoff without continually rewriting the cached
prefix** — the mechanism that killed recency compression. Nothing here is executed tonight.

## Core cache-safe architecture (shared by all memory actions)
```
immutable cached system+task prefix
  + stable VERSIONED memory snapshot (byte-stable between consolidation epochs)
  + append-only HOT suffix (recent turns, uncompressed)
  + occasional CONSOLIDATION EPOCH (one-time cache-creation cost, then reuse)
```
**Forbidden:** regenerating the full summary/memory on every call (destroys cache reuse — the
recency failure mode). **Required:** memory snapshot is content-addressed + versioned; between
epochs the snapshot bytes are identical so the prefix cache is reused.

## The ladder
| Action | dose | what moves out of resident context | what is retained | recovery |
|---|---|---|---|---|
| **A0 = LINEDEDUP static baseline** | 0 | exact duplicate lines in newest obs | everything else verbatim | n/a (baseline) |
| **A1 = indexed raw-evidence memory** | 1 | cold raw content -> external store | EXACT raw content externally; inject stable compact handles | exact dereference by handle |
| **A2 = structured state memory** | 2 | cold history -> structured state | active objective, constraints, files, symbols, failed attempts, tests, errors, unresolved deps + pointers to raw evidence | dereference pointers |
| **A3 = aggressive semantic memory** | 3 | cold history -> short semantic representation | raw evidence retained for recovery; inject only SELECTED retrieved content | retrieval + raw dereference |

A0 is the frozen baseline (the current best static primitive). A1→A3 increase how much resident
context is externalized and how lossy the resident representation becomes.

## Failure-mode decomposition (each measured separately — do NOT collapse into "accuracy drop")
| failure mode | definition | observable measurement |
|---|---|---|
| write loss | evidence never written to memory | (written_ids) vs (evidence seen) diff |
| retrieval miss | needed evidence not retrieved when required | retrieval_hit=0 on a query whose target was in store |
| retrieval ranking error | needed evidence retrieved but ranked below cutoff | retrieval_rank > k for a used item |
| utilization failure | retrieved but model ignored/misused it | retrieved_hit=1 AND subsequent action ignores it |
| stale-memory error | memory snapshot outdated vs current state | snapshot_version < live state version at use |
| recovery cost | extra calls/tokens to recover externalized content | recovery_triggered, recovery_cost |
| cache tax | cache-creation tokens at consolidation epochs | cache_creation at epoch boundaries |
| memory-write overhead | tokens/calls to write the snapshot | write_cost |

## Objective (frozen)
**Primary = task-total effective cost** = input + 0.1·cache_read + 1.25·cache_creation + 5·output,
summed over ALL model calls + tool calls + **memory writes + memory retrievals + recovery calls +
repeated file reads + repeated tests + repeated searches**. (H1/H3/task-total kept distinct; primary
is task-total.)

**Quality (richer than binary where available):** resolution; patch correctness; regression;
active-constraint preservation; exact error recall; failed-hypothesis preservation; catastrophic
memory failure indicator.

## Tolerance-conditioned parity (frozen tolerances ε ∈ {0, 0.02, 0.05, 0.10})
a*(X, ε) = argmin task-total-cost action s.t. predicted quality loss ≤ ε AND catastrophic risk ≤ budget.
The question is NOT "is memory good?" but "**under what pre-treatment runtime states and quality
tolerances is each memory dose preferable?**"

## Determinism / fallback / failure
- Memory serialization deterministic + byte-stable; snapshot_id = content hash.
- A1 retains EXACT raw content (deterministic); A2 structured extraction should prefer frozen rules;
  A3 semantic compaction may use a model — if so, freeze model+prompt+temperature and version the
  snapshot (regenerate ONLY at consolidation epochs, never per call).
- Fail-closed: any memory write/read/validate error → fall back to A0 for that call + log.
