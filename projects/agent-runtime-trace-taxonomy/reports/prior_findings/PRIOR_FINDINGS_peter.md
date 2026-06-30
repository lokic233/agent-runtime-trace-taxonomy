# Prior Findings from tokensaver — supplementary evidence (Peter)

> These are earlier observations from a separate measurement campaign
> ([Peterren/tokensaver](https://github.com/Peterren/tokensaver)) that corroborate or scope
> the main pruning A/B results. They are **not independent claims** — they are supporting evidence
> and generalization guards.

## Shared baseline / harness / method
- **Harness:** mini-swe-agent (bash tool loop), SWE-bench Verified, container-based grading
  (podman, network-isolated, FAIL_TO_PASS + PASS_TO_PASS).
- **Models:** multiple tiers on the SAME harness + instances: Opus-4.6 (frontier-big),
  Sonnet-4.5 (frontier-mid), Qwen2.5-Coder-7B (open-small).
- **Cost metric:** billed cost computed from REALIZED per-call `cache_read` / `cache_creation` /
  output token fields (not estimated). Provider pricing weights: cache_read 0.1×, cache_write 1.25×,
  output 5×, uncached input 1×.
- **Determinism:** seed 0, temperature 0 where applicable. Resolve verified by real test-suite execution.

---

## Finding 1: Capability-conditioned waste signatures — DON'T generalize from weak to frontier
**Source:** [research/03-capability-signatures](https://github.com/Peterren/tokensaver/tree/main/research/03-capability-signatures)

**Question:** Are token-waste patterns universal across models, or capability-dependent?

**Method:** Same 18 SWE-bench Verified instances, same harness, seed 0, three capability tiers.

**Result:**
| Model (tier) | mean steps | **redundant-obs %** | step-cap hits |
|---|---:|---:|---:|
| Opus 4.6 (frontier-big) | 14.3 | **0.0%** | 3/18 |
| Sonnet 4.5 (frontier-mid) | 22.6 | **1.3%** | 11/18 |
| Qwen2.5-Coder-7B (open-small) | 17.7 | **35.4%** | 9/18 |

The 35.4% on the weak model is a **looping symptom** (62.7% in step-capped episodes vs 8.1% in non-capped),
not a clean optimization lever.

**Relevance to the main study:** This explains WHY lossless context compression is a non-lever on the frontier
model (0% byte-exact redundancy → nothing to compress losslessly). The pruning A/B methods that DO save
per-call prompt (HYBRID1/AGG3) are not lossless — they destructively REMOVE old context, which is why they
trigger the Cache Tax. A lossless approach would have nothing to remove on opus-4.7.

**Scope guard:** any optimization trained/validated on a weak model's waste signatures MUST be re-validated on
frontier before claiming generality. The 0→35% gap is not noise (same instances, same harness, controlled).

---

## Finding 2: Cache Tax — first billed-cost measurement (corroborating evidence for the main result)
**Source:** [research/05-cache-economics](https://github.com/Peterren/tokensaver/tree/main/research/05-cache-economics)

**Question:** Does raw-token context compaction reduce billed cost under production prompt caching?

**Method:** 3×2 factorial on n=12 SWE-bench Verified instances:
- Arm A = no compaction (append-only baseline, preserves prefix)
- Arm B = prefix-editing compaction (rewrites earlier observations → mutates cached prefix)
- Arm C = cache-safe truncation (trims only the newest obs tail, never rewrites history)
- × {5-minute, 1-hour} cache TTL

**Result:**
- Arm B (prefix-editing): cache hit-rate **52% → 7%** (collapses on 69% of turn-pairs), net billed-cost
  **neutral-to-negative** despite cutting raw tokens.
- Arm C (cache-safe): **+11–15% median billed-cost saving**, resolve-neutral. The only reliable lever.
- The mechanism: prefix-editing churns the content-hash identity of the cached span → forces expensive
  cache re-creation (1.25×) instead of cheap cache reads (0.1×).

**Relevance to the main study:** This is the **earlier, controlled observation** of the same Cache Tax that
the golden-50 pruning A/B reproduces at scale:
- Study 05 Arm B ≈ the main study's HYBRID1/AGG3 (prefix-destructive)
- Study 05 Arm C ≈ a hypothetical prefix-stable policy (the design target for the controller)

The main study (v2/v3 + independent reproduction) confirms Study 05's directional finding at n=50 with
full SWE-bench grading. Study 05 adds the TTL ablation and the cache-safe arm (showing the design path).

**Honest caveat:** n=12, one model, single seed. The SIGN is robust (3 independent confirmations); the
MAGNITUDE (+11-15% for cache-safe) is directional and needs the golden-50-scale validation.

---

## What is NOT contributed here (honest)
- **Study 09 (compositional losslessness)** is Loki's work (committed by dengcchi); cited, not claimed.
- **Study 01 (cache certification)** is a correctness/engineering bug finding, not a research contribution
  in this context.
- **Study 02 (shadow methodology)** is a measurement framework; its headline result is a null.
- No new intervention claims. These findings are MEASUREMENT + SCOPE — they support and bound the main study.
