#!/usr/bin/env python3
import json, os, statistics as st
BASE="/data/users/dengcchi/prune_ab"
G=set(json.load(open("/tmp/golden50.json")))
# For an UNCACHED model: cost = (input+cache_read+cache_creation)*1.0 + output*5  (no 0.1x discount)
# Recompute LINEDEDUP/GENTLE6K/HYBRID-equivalent savings under uncached pricing from EXISTING token data.
def ledger_tokens(led):
    a={}
    if not os.path.exists(led): return a
    for l in open(led):
        try:
            d=json.loads(l);t=d.get("task_id")
            if not t or str(t).startswith(("UNKNOWN","NO_")):continue
            ir=(d.get("input_tokens")or 0);cr=(d.get("cache_read_tokens")or 0);cc=(d.get("cache_creation_tokens")or 0);op=(d.get("output_tokens")or 0)
            x=a.setdefault(t,{"prompt":0,"out":0});x["prompt"]+=ir+cr+cc;x["out"]+=op
        except:pass
    return a
c0=ledger_tokens(f"{BASE}/logs/stable/ledger_C0_identity.jsonl")
def saving(led,cached):
    m=ledger_tokens(led);common=sorted(set(c0)&set(m))
    def cost(x): return (x["prompt"]*(0.0 if False else 1.0)+x["out"]*5) if not cached else (x["prompt"]*0.3+x["out"]*5)
    # cached: approximate blended prompt price ~0.3x (mix of read 0.1 + creation 1.25); uncached: 1.0x
    # better: use ACTUAL eff for cached, theoretical for uncached
    return common,m
print("="*72)
print("PHASE 7 (mechanistic boundary, no new runs): does pruning's value change UNCACHED?")
print("="*72)
print("\nThe cache-tax mechanism (Phase 2) REQUIRES a prompt cache. On an UNCACHED model")
print("(e.g. local Qwen2.5-Coder-32B, no prefix cache), prefix rewriting has NO cache to bust.")
print("\nRe-pricing existing token counts under UNCACHED model (all prompt @1.0x, output @5x):")
print(f"\n{'method':18s}{'CACHED eff-save':>16s}{'UNCACHED save (raw-prompt-dominated)':>38s}")
for name,led in [("LINEDEDUP_e4","logs/e4/ledger_LINEDEDUP_e4.jsonl"),("GENTLE6K_stable","logs/stable/ledger_GENTLE6K_stable.jsonl")]:
    m=ledger_tokens(f"{BASE}/{led}");common=sorted(set(c0)&set(m))
    # cached eff (actual)
    def eff_cached(led2):
        a={}
        for l in open(f"{BASE}/{led2}"):
            try:
                d=json.loads(l);t=d.get("task_id")
                if not t or str(t).startswith(("UNKNOWN","NO_")):continue
                ir=(d.get("input_tokens")or 0);cr=(d.get("cache_read_tokens")or 0);cc=(d.get("cache_creation_tokens")or 0);op=(d.get("output_tokens")or 0)
                a[t]=a.get(t,0)+ir+cr*.1+cc*1.25+op*5
            except:pass
        return a
    c0e=eff_cached("logs/stable/ledger_C0_identity.jsonl");me=eff_cached(led)
    cc=sorted(set(c0e)&set(me)); cached_save=100*(sum(c0e[t] for t in cc)-sum(me[t] for t in cc))/sum(c0e[t] for t in cc)
    # uncached: prompt*1.0 + out*5
    unc_c0=sum(c0[t]["prompt"]+c0[t]["out"]*5 for t in common); unc_m=sum(m[t]["prompt"]+m[t]["out"]*5 for t in common)
    unc_save=100*(unc_c0-unc_m)/unc_c0
    print(f"{name:18s}{cached_save:>+15.1f}%{unc_save:>+37.1f}%")
print("\n  NOTE: uncached re-pricing reuses opus trajectories (same calls/tokens). A truly weaker model")
print("  would have DIFFERENT (likely longer, more redundant) trajectories. This is a mechanism")
print("  transfer ARGUMENT + re-pricing bound, NOT a validated weaker-model run (would need SWE-agent->Qwen).")
