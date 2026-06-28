# LANE 1 — TokenSaver Context Contract

**Source:** github.com/Peterren/tokensaver @ 78ab263 (clone: cli:devvm14382:/data/users/dengcchi/agent_runtime_proj/tokensaver)
**Purpose:** Identify the fields TokenSaver already defines so our normalized schema PRESERVES them
(the downstream controller reads TokenSaver telemetry), and separate **deterministic metrics** from
**semantic labels**. We do not reinvent metric names that TokenSaver already standardizes.

## 1. The single most important inherited principle: HONEST NULLS
TokenSaver's design rule (docs/metrics.md "Limitations"; model.py; scorecard.py):
> Missing data reads `n/a`/`null` with `content_available=false` — **never a fabricated 0 or 1**.
- Per-span CPU with no sample in window → `cpu_ms=null`, `cpu_samples=0` (NOT interpolated).
- Utilization metrics with no captured content → `null` + `content_available=false` (NOT 0).
- Unknown-model cost → listed in `unpriced_models`, excluded (NOT treated as free).
- Scorecard: a calling with no relevant spans scores `None` and is **excluded** from the mean.

→ **Binding on our L0 schema (Section 5):** "Never force absent fields to zero. Use null plus an
availability flag." This is the SAME rule. We adopt `content_available` verbatim.

## 2. Deterministic metrics (TokenSaver computes these — EVIDENCE, not semantic truth)
### Roofline (per trace) — `RooflineVector` (model.py)
`prefill_tokens, decode_tokens, reasoning_tokens, llm_calls, tool_calls, cpu_ms, cpu_samples,
rss_peak_bytes, rss_delta_bytes, wall_ms, cost_usd, energy_wh, parallelism_depth, context_length`
- Additive dims roll up by summation across a subtree; cpu/rss only when present on both sides.
- Reserved (null until an emitter provides): `quality, uncertainty, artifact_maturity,
  verification_confidence, failure_prob`. We do NOT fabricate these.

### Tool-calling effectiveness (per trace) — `ToolMetrics` (effectiveness/tools.py)
`tool_calls, error_rate, duplicate_rate (identical name+args), retry_rate, tool_churn (type switches),
result_utilization (null if no content), content_available`
- "Used" = lexical word-shingle containment ≥ 0.35 (effectiveness/text.py). **Lexical, not semantic** —
  pure paraphrase is a known miss. This is exactly the prompt's "AUTOMATIC-METRIC OVERREACH" warning.

### Memory effectiveness (per trace/session) — `MemoryMetrics` (effectiveness/memory.py)
`retrieval_utilization, recall_miss_rate (rework), redundant_retrieval, redundant_write, write_yield
(dead writes), memory_token_overhead`. Each null when uncomputable.

### Scorecard (effectiveness/scorecard.py)
`tools, memory, planning (=1-loop_rate), overall, weakest, content_available, findings[]`.
`planning` waste = TRULY repeated identical op signatures (tool:name:normalized-args / mem:query).
Tool *churn* (diverse tools used once) is explicitly NOT waste → informational only.

### Waste findings (analyze/waste.py) — `Finding{severity, dimension, title, detail, recommendation, location, value}`
Severity ∈ {high, medium, low}. These are roofline/heuristic findings, NOT our semantic taxonomy.

## 3. Mapping: TokenSaver field → our Section-5 deterministic feature
| Section 5 metric                       | TokenSaver source                          | Notes |
|-----------------------------------------|--------------------------------------------|-------|
| prefill/decode/total tokens, wall, cpu  | RooflineVector                             | direct |
| peak RSS, energy, cost, parallelism     | RooflineVector                             | direct (estimates flagged) |
| tool-call count, tool error rate        | ToolMetrics.tool_calls/error_rate          | direct |
| exact duplicate call rate               | ToolMetrics.duplicate_rate                 | name+args identical |
| retry rate, tool churn                  | ToolMetrics.retry_rate/tool_churn          | direct |
| result utilization, unused-result count | ToolMetrics.result_utilization             | **lexical** → evidence only |
| retrieval util, recall-miss, redundant  | MemoryMetrics.*                            | direct |
| memory write yield, token overhead      | MemoryMetrics.write_yield/token_overhead   | direct |
| semantic/near-duplicate call rate       | NOT in TokenSaver (lexical only)           | **we add candidate flag, mark LOW observability** |

## 4. What TokenSaver does NOT provide (we build in Lane 2, SWE-agent-specific)
TokenSaver is workload-agnostic (OTel spans). It has NO concept of: unique files searched/read,
duplicate file reads, repeated file-region reads, candidate-file set growth, files modified, patch
attempts/reversions/churn, targeted vs full-suite tests, env/setup failures, first-candidate-location
step, first-plausible-patch step, first-improving-test step, longest no-new-evidence streak,
termination reason. These are the SWE-AGENT-SPECIFIC block of Section 5 — our `extract_deterministic_features.py`
computes them from the normalized event stream.

## 5. Contract obligations on our pipeline
1. Reuse TokenSaver metric NAMES where they exist (interop with the controller's telemetry).
2. Preserve `content_available` and honest nulls everywhere.
3. Treat ALL deterministic metrics as **evidence that must be cited by event ID**, never as the
   semantic label itself (REDUNDANT_SEARCH ≠ "search_count>1"; UNUSED_TOOL_RESULT ≠ "low lexical reuse").
4. Keep TokenSaver's lexical-similarity caveat front-of-mind in the red-team audit (check #8).
5. The downstream controller emits/consumes TokenSaver telemetry → our exports must be joinable on
   trace_id and use compatible roofline field names.

## 6. Deterministic vs semantic — the hard line
- **Deterministic (this layer, reproducible, no model):** everything in §2 + §4 above.
- **Semantic (Stage A/B annotation, model judgment, must cite evidence):** workload L1/L2, execution
  phase/progress, waste L1/L2, primary bottleneck, candidate interventions, abstain.
- Frontier models may produce semantic labels + intervention HINTS. They may NOT mint gold config/Pareto
  labels (Section 1/15). TokenSaver's own `optimize`/auto-tuner uses **offline counterfactual replay** for
  its config claims — the same empirical bar we require before any `recommended_config` is non-null.
