# Pareto Frontier v3 — TASK-LEVEL accounting (the corrected cost metric)

**This supersedes v2's saving numbers.** v2 reported *mean prompt-token-per-call reduction*. That is NOT task-level cost saving. Recomputed on paired per-task totals from SWE-agent's own `model_stats` (tokens_sent / tokens_received / api_calls / instance_cost — authoritative, per-task, per-run).

## ⚠️ The headline reverses

| method | v2 claim (per-call) | **v3 mean Δsent** | **v3 median Δsent** | **v3 median Δcost** | mean call Δ |
|--------|------:|------:|------:|------:|---:|
| HYBRID1_m7_agg2 | **+41.5%** | **−16.7%** | **−2.5%** | **−2.2%** | varies |
| AGG3_recency_obs_4 | +50.6% | −14.9% | −1.2% | −48.8% | −0.6 |
| M7_old_obs_elide | +37.0% | −23.0% | −4.3% | −41.0% | −0.6 |
| M4_obs_cap_5k | +1.4% | −25.9% | −9.3% | +4.4% | +0.1 |
| M6_env_log_collapse | +0.5% | −25.2% | −18.7% | +6.7% | +0.9 |

(Δ = (C0 − method)/C0; positive = method saves. Negative = method costs MORE.)

**Every method has negative MEAN task-level token saving.** HYBRID1's median is −2.5% (sent) / −2.2% (cost) — i.e. it does **not** reduce task-level cost. The +41.5% was an artifact.

## Why the +41.5% was wrong (two compounding bugs)

### Bug 1: Ledger contamination (the denominator was inflated)
The `logs/ledger_C0_identity.jsonl` pooled **1910 calls across a 2.9-hour window spanning multiple runs** (screen phase + full-50 + re-runs), but the actual C0 golden-50 run made only **1190 calls**. The 720 contaminating calls (mostly large-prompt screen tasks) inflated C0's mean true-prompt/call to 20,570 — making HYBRID1's 12,028 look like a 41.5% cut. The ledger was never task-tagged (`tag=""`), so per-call pooling could not be paired.

### Bug 2: Cache-busting tax (per-call ≠ task cost)
opus-4.7 via PlugBoard uses Anthropic **prompt caching**. C0 sends a stable growing prefix → 11.8:1 cache_read:cache_creation (cheap reuse). HYBRID1 **rewrites the prefix every step** (clearing old observations changes the cached span) → 0.37:1 — the cache is constantly invalidated, so expensive `cache_creation` (1.25× price) replaces cheap `cache_read` (0.1× price). Fewer raw prompt tokens per call, but each token costs more AND the cache savings evaporate. Net task cost: flat-to-worse.

```diagram
C0 (no pruning):        HYBRID1 (pruning):
  step N prompt =          step N prompt =
  [cached prefix]──┐         [REWRITTEN prefix]──┐
   cache_read 0.1× │          cache_creation 1.25×│  ← every edit busts the cache
  [new turn]       │         [new turn]           │
                   ▼                               ▼
  cache_read:creation        cache_read:creation
     = 11.8 : 1                  = 0.37 : 1
```

## Corrected metric name
Until validated on held-out data, the per-call number must be called **"mean prompt-token-per-call reduction"**, NOT "total token saving". Task-level cost is the metric that matters, and it shows HYBRID1 is **NEUTRAL-to-NEGATIVE**.

## Provisional frontier verdict (pending A/A noise floor + held-out)
- No method demonstrates positive paired task-level token saving on golden-50.
- The methods that DO save task-level cost slightly (M4 +4.4%, M6 +6.7% median cost) are the *conservative* ones that barely prune — and they had 3 regressions each.
- **HYBRID1 is not a frontier point under task-level cost.** Hard-kill rules #1 (no token improvement) and #2 (output/call growth cancels reduction) are provisionally TRIGGERED.

## Caveat on this analysis
`instance_cost` aggregates are outlier-sensitive (a few thrashing tasks dominate sums), which is why **median paired** is the headline. Even the median is negative/flat. Phase 3 (A/A noise) will establish whether the −2.5% is within run-to-run noise (likely) or a real cost.

---

## Addendum: the three cost signals (read this before trusting any single number)

SWE-agent + the shim expose THREE distinct cost signals. They measure different things:

| signal | source | what it measures | cache-aware? |
|--------|--------|------------------|:---:|
| **tokens_sent** | `.traj` model_stats (litellm `token_counter` on messages, **line 690**) | client-side count of the FULL history **BEFORE the shim prunes** | no — it's a pre-prune trajectory-size proxy |
| **instance_cost** | `.traj` model_stats (`litellm.completion_cost(response)`) | priced from the model's RESPONSE usage (post-prune, cache-aware) | yes, but opus-4.7 may be unmapped → fallback price |
| **true-prompt** | shim ledger (`input + cache_read + cache_creation` from PlugBoard usage) | the POST-prune tokens the model actually billed | yes (ground truth) |

**Critical architectural fact:** SWE-agent counts `tokens_sent` on the messages it builds, which is **before** the HTTP request reaches the shim where pruning happens. So `tokens_sent` does NOT reflect what pruning removed — a lower HYBRID `tokens_sent` means HYBRID took a **different/shorter trajectory** (an indirect, confounded effect), not that pruning cut the billed prompt.

**The only ground-truth billing signal is the shim ledger true-prompt** — and the original one was contaminated/untagged. That is why Phase 2 rebuilt a **task-tagged** ledger (shim v2). The Phase 3/4/6 runs use it; their numbers supersede everything derived from the old ledger.

**Distribution finding (instance_cost, golden-50):** HYBRID1 is cheaper on 24 tasks, more expensive on 26, with catastrophic outliers (pylint-6528 −457%, pytest-7432 −408%) where cache-busting + extra calls dominated. Median ≈ flat. This is textbook **Hard Kill Rule #6** (result depends on a small number of unstable tasks) — pending confirmation from the A/A noise floor.
