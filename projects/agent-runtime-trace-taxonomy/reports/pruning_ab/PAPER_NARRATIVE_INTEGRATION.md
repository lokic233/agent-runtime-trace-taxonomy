# Paper-Facing Narrative Integration — Formal MRT

**Purpose (mission §24):** integrate the formal MRT result into the workshop paper without
letting it overwrite the earlier negative task-level controller result. All claim language is
drawn from the preregistered claim ladder; abstract language is frozen only after final verdicts.

## The paper's evidence hierarchy (unchanged, extended)

1. **Cache tax** — SUPPORTED (SHAM-controlled), `CACHE_TAX_CAUSALITY.md`.
2. **Intelligence tax** — SUPPORTED (dose-controlled), `INTELLIGENCE_TAX_CAUSALITY.md`.
3. **Task-level observational signal failure** — the earlier task-level controller was
   **NOT_SUPPORTED** (`ORACLE_GAP.md`, `BUDGET_CONTROLLER_DEV.md`): a +27% oracle gap exists
   (real heterogeneity) but no observational signal converts it to value over the best static
   policy. **This negative result stands and is not overwritten.**
4. **Decision-level causal formulation** — motivated precisely because the task-level signal
   failed: reframe the question as a per-decision action×signal interaction (`CAUSAL_ESTIMANDS.md`).
5. **Formal MRT moderator result** — this study. A protocol-conformant, stratified-block,
   restart-safe, fail-closed decision-level randomized experiment. **Outcome #4 (underpowered,
   N=13):** protocol path validated; exact redundancy **not** established as a causal moderator;
   redundancy-gated policy does **not** beat the best static policy; cache-preservation mechanism
   directionally confirmed.
6. **TraceController policy value** — NOT_SUPPORTED at achievable N; a powered evaluation needs
   a much larger buildable task pool and remains future work.

## Why the MRT does not contradict the task-level result
Both point the same direction: **at the samples achievable in this workshop-scale study, neither
a task-level observational signal nor a decision-level randomized signal converts the real
underlying heterogeneity into deployable controller value.** The MRT tests a *different, more
local* signal (per-decision exact redundancy) with a *cleaner* identification (randomized NO_OP
control), and still finds no established moderator — strengthening, not reversing, the negative
controller narrative.

## Frozen abstract language (selected branch: signal fails / underpowered)

Per the ladder, because the moderator is not supported and the study is underpowered:

> Even decision-local syntactic redundancy fails to reliably identify profitable transformations
> at the sample achievable here; the protocol-conformant MRT path is validated and the
> cache-preservation mechanism is directionally confirmed, but a powered evaluation of a
> redundancy-gated TraceController — and richer semantic liveness/recoverability signals —
> remains future work.

## Honest framing of the ONE positive thread
The cache-preservation mechanism (segment-local transform preserves the materialized prefix)
is the durable, reusable finding: it is directionally confirmed here (lower cache_creation for
LINEDEDUP) and consistent with the rescue evidence (content-stable methods preserve cache
122×/14× vs recency methods 0.37×). This is a **mechanism**, not an identified causal saving,
and is described as such.

## What must NOT appear in the paper
- "the controller is validated" (b3 sign is wrong AND underpowered)
- "exact redundancy is ground truth"
- "LINEDEDUP is lossless"
- "MRT produces per-event causal labels"
- "the signal generalizes across models"
- "deployment ready"
