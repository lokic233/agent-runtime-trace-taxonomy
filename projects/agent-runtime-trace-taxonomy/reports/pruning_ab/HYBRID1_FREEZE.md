# HYBRID1 FREEZE — Phase 1

Frozen 2026-06-29T20:22:03Z. HYBRID1 implementation is locked; no modifications after viewing validation outcomes.

## Identity & hashes

| field | value |
|-------|-------|
| git commit SHA | `7791c5ec15f0e45c846bf5aa1a83b46717b5afbb` |
| prune_methods.py sha256 | `5b2c8b2156e78d0e5a4f908456430ad4817e8f8e4530f38f49dc7a46e895c07b` |
| HYBRID1 fn name | `hybrid_m7_agg2` |
| HYBRID1 source sha256 | `6c9ab8b642bda9a3032ff2ef1f4d2492eb89e3dbd8a57e3c5694d53578b457b1` |
| prune_shim.py sha256 | `5b64206382843e88...` |
| SWE-agent run config sha256 | `9841a85269ec1f93...` |
| model identifier | `anthropic/claude-opus-4-7` (served: claude-opus-4.7) |
| serving endpoint | PlugBoard (plugboard.x2p.facebook.net/v1/messages), mTLS via curl --noproxy |
| temperature | 0.0 |
| thinking mode | **OFF** (verified: 0/22 steps have non-empty thinking_blocks; no `thinking` key in wire body) |
| max_tokens | 128000 (wire body) |
| per_instance_call_limit | 75 |
| harness | SWE-agent 1.1.0 (swe_agent_version=1.1.0) |
| grading | swebench.harness.run_evaluation, SWE-bench_Verified, podman, max_workers=4, cache_level=instance |

## Frozen HYBRID1 source

```python
def hybrid_m7_agg2(messages):
    """HYBRID1: M7 for VERY old observations (>12 steps) + AGG2-style obs-clear for medium-old (8-12).
    Graduated: recent=full, medium=summarized, old=cleared."""
    import copy
    out=copy.deepcopy(messages); n=len(out)
    obs_idx=[i for i,m in enumerate(out) if _is_obs(i,m,n)]
    if len(obs_idx)<=12: return out
    recent_cut=obs_idx[-8]; medium_cut=obs_idx[-12]
    for i in obs_idx:
        if i>=recent_cut: continue  # keep recent
        t=_txt(out[i].get("content"))
        if len(t)<=200: continue
        if i<medium_cut:  # very old -> full clear
            _set_obs_text(out[i], f"[old observation cleared; {len(t)} chars]")
        else:  # medium -> summarize (first 100 + last 50)
            _set_obs_text(out[i], t[:100]+"..."+t[-50:]+f" [{len(t)}c]")
    return out
```

## Candidate result under scrutiny (pre-validation)
- reported **mean prompt-token-per-call reduction**: 41.5% (NOT "total token saving" — see Phase 2)
- C0 resolved 48/50, HYBRID1 resolved 48/50; paired: 1 regression + 1 improvement

## Known weaknesses being tested (per reviewer)
1. saving was per-call aggregate, not paired task-level total cost
2. no A/A baseline → no outcome noise floor
3. per-task pruning activation / chars removed not logged
4. canary + improvement claims may be stochastic flips
5. golden-50 used for BOTH selection and evaluation → need held-out set
