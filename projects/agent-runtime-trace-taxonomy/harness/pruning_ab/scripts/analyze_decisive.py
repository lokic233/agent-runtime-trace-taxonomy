#!/usr/bin/env python3
"""DECISIVE: paired per-task cache-aware effective cost + regressions for cache-stable methods.
EFFECTIVE COST = input*1.0 + cache_read*0.1 + cache_creation*1.25 + output*5.0
Pairs each method vs tagged C0 baseline on golden-50. Grades for regressions vs A/A noise floor."""
import json, glob, os, statistics as st, math
BASE="/data/users/dengcchi/prune_ab"
AA_NOISE_RATE=0.025  # from prior phases (held-out regression rate within noise)
AA_LOSS_UB=0.055

def per_task_eff(method):
    """per-task effective cost from task-tagged ledger."""
    f=f"{BASE}/logs/stable/ledger_{method}.jsonl"
    if not os.path.exists(f): return {}
    agg={}
    for l in open(f):
        try:
            d=json.loads(l); t=d.get("task_id")
            if not t or str(t).startswith(("UNKNOWN","NO_")): continue
            ec=(d.get("input_tokens") or 0)*1.0+(d.get("cache_read_tokens") or 0)*0.1 \
               +(d.get("cache_creation_tokens") or 0)*1.25+(d.get("output_tokens") or 0)*5.0
            a=agg.setdefault(t,{"eff":0.0,"raw_prompt":0,"out":0,"calls":0})
            a["eff"]+=ec
            a["raw_prompt"]+=(d.get("input_tokens") or 0)+(d.get("cache_read_tokens") or 0)+(d.get("cache_creation_tokens") or 0)
            a["out"]+=(d.get("output_tokens") or 0); a["calls"]+=1
        except: pass
    return agg

def resolved(method):
    for p in [f"{BASE}/results/pruning_ab/stable/grade_{method}.json"]:
        if os.path.exists(p): return set(json.load(open(p)).get("resolved_ids",[]))
    return None

def wilson_upper(k,n,z=1.645):
    if n==0: return 1.0
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; m=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return min(1.0,c+m)

def main():
    golden=set(json.load(open("/tmp/golden50.json")))
    c0_eff=per_task_eff("C0_identity")
    c0_res=resolved("C0_identity")
    methods=["CAP1K_stable","CAP800_stable","CAP500_stable","SMART_stable","COMBOSC_stable"]
    rows=[]
    print(f"C0 baseline: {len(c0_eff)} tasks with cost data, {len(c0_res) if c0_res else '?'} resolved\n")
    print(f"{'method':16s}{'med eff-cost save%':>18s}{'mean':>8s}{'regr':>6s}{'impr':>6s}{'loss_UB':>9s}{'verdict':>16s}")
    print("-"*80)
    for m in methods:
        meff=per_task_eff(m); mres=resolved(m)
        common=sorted(set(c0_eff)&set(meff))
        if not common: print(f"{m:16s}  (no paired data yet)"); continue
        save=[100*(c0_eff[t]["eff"]-meff[t]["eff"])/c0_eff[t]["eff"] for t in common if c0_eff[t]["eff"]>0]
        med=st.median(save); mean=st.mean(save)
        if c0_res is not None and mres is not None:
            reg=len(c0_res & golden - mres); imp=len((mres & golden) - c0_res)
            loss_ub=wilson_upper(reg, len(c0_res & golden))
        else: reg=imp=-1; loss_ub=-1
        # verdict: positive median saving AND regressions within A/A noise
        win = med>0 and loss_ub>=0 and loss_ub<=0.10  # within ~2x A/A floor
        verdict="*** TRUE WIN ***" if (med>2 and 0<=loss_ub<=0.10) else ("marginal" if med>0 else "no saving")
        rows.append({"method":m,"median_eff_save_pct":round(med,1),"mean_eff_save_pct":round(mean,1),
                     "regressions":reg,"improvements":imp,"loss_ub":round(loss_ub,3),"n_paired":len(common),"verdict":verdict})
        print(f"{m:16s}{med:>17.1f}%{mean:>7.1f}%{reg:>6d}{imp:>6d}{loss_ub:>9.3f}{verdict:>16s}")
    json.dump({"baseline":"C0_identity_tagged","aa_noise_rate":AA_NOISE_RATE,"results":rows},
              open(f"{BASE}/results/pruning_ab/stable/effective_cost_frontier.json","w"), indent=1)
    print(f"\n=> A TRUE WIN = positive median effective-cost saving with loss_UB within ~2x A/A floor ({AA_LOSS_UB})")
    wins=[r for r in rows if "WIN" in r["verdict"]]
    if wins: print(f"\n🎯 {len(wins)} TRUE TASK-LEVEL WIN(S): {[w['method'] for w in wins]}")
    else: print("\nNo true win yet (need positive median eff-cost saving + regressions within noise).")

if __name__=="__main__": main()
