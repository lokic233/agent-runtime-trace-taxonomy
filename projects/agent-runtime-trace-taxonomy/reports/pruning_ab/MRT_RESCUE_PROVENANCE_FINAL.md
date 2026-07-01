# MRT Rescue — Provenance (FINAL, corrected)

Supersedes MRT_RESCUE_PROVENANCE.md, which recorded the *frozen* shim SHA rather than the SHA
that actually generated the committed live-run results.

## Chronological provenance

| Stage | Commit | Shim SHA-256[:16] | What happened |
|---|---|---|---|
| Freeze | `4261888` | `12f631e6fd3c25ac` | rescue shim written + 6 synthetic tests pass; provenance.json recorded this SHA |
| _is_obs fix | `5d2764a` | (intermediate) | fixed wire-format observation matcher; identified model-efficiency barrier |
| **Live run** | `36686f2` | **`ae352c2efdb0769e`** | 2 live-run bug fixes applied (see below); pilot RAN CLEAN end-to-end and was graded |

## The final successful live rescue run

- **Commit:** `36686f2`
- **Shim SHA-256:** `ae352c2efdb0769e291e96abc85689ec02e38093e7e5efe8197f8cc5a8b4214c`
- **Model:** anthropic/claude-opus-4-7 (PlugBoard mTLS)
- **SWE-agent:** 1.1.0
- **Temperature:** 0.0 · thinking OFF
- **Seed:** 20260701
- **Eligibility:** newest obs, segment ≥ 2000 chars, ≥ 5 dup lines, dup_fraction > 0.40 (rescue thresholds)
- **Tasks (5):** pylint-dev__pylint-8898, sympy__sympy-14248, sympy__sympy-14976, sympy__sympy-19040, sympy__sympy-24539
- **Event-log SHA-256:** `2b7c3b2989986b2fd64ad3beb18f15d2795c9ea2968484c7c7fb99b81e937f7b` (215 calls)
- **Grade-report SHA-256:** `3e4cd2836d27307cf8a9ea72f13891c9f014e8ba02f9893b5454643972994860` (3/5 resolved)
- **Preds SHA-256:** `2b6f546dd22dcff2366d0cefcf6b04bb08906236519257168d1cf18f4b771b1d`

## Source fixes made AFTER the initial freeze (`12f631e6` → `ae352c2e`)

1. **`_normalize_body()` hoist** — custom-tool `type` stripping + `top_p` drop moved to the top of
   `process_request` so ALL request paths (not just the experimental branch) are normalized.
   Without this, PlugBoard returned 400 → litellm `KeyError:'content'` → batch crash.
2. **Response guard** — on a malformed upstream response, retry once, then (in the rescue) synthesize
   a minimal empty-assistant message. **NOTE:** this synthetic fallback is REMOVED in the formal shim
   (`mrt_formal_shim.py`) because it changes the trajectory; the formal shim fails closed.

## Status

This provenance describes a **protocol-valid smoke test** (N=2 interventions, 0 controls), not a
powered causal result. The formal study (`mrt_formal_shim.py`) supersedes the rescue shim for all
causal claims.
