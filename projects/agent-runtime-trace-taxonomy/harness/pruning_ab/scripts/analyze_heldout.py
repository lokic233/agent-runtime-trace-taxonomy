#!/usr/bin/env python3
"""Phase 6 Stage D: held-out validation analysis.
Computes paired task-level token totals (from task-tagged ledgers), solve-rate preservation,
and excess success->failure flips beyond the A/A noise floor. Emits heldout_outcomes.jsonl."""
import json, glob, os, statistics as st, math
BASE="/data/users/dengcchi/prune_ab"
GD=f"{BASE}/results/pruning_ab/phase6"; LD=f"{BASE}/logs/phase6"

def resolved(tag):
    f=f"{GD}/grade_{tag}.json"
    return set(json.load(open(f)).get("resolved_ids",[])) if os.path.exists(f) else None

def task_tokens(tag):
    """per-task total tokens (input_side + output) from the task-tagged ledger."""
    f=f"{LD}/ledger_{tag}.jsonl"
    if not os.path.exists(f): return {}
    agg={}
    for l in open(f):
        try:
            d=json.loads(l); t=d.get("task_id")
            if not t or str(t).startswith("UNKNOWN"): continue
            a=agg.setdefault(t,{"input_side":0,"output":0,"calls":0,"chars_removed":0,"changed_calls":0})
            a["input_side"]+=(d.get("input_tokens") or 0)+(d.get("cache_read_tokens") or 0)+(d.get("cache_creation_tokens") or 0)
            a["output"]+=(d.get("output_tokens") or 0); a["calls"]+=1
            a["chars_removed"]+=d.get("characters_removed",0)
            if d.get("changed"): a["changed_calls"]+=1
        except: pass
    for t in agg: agg[t]["total"]=agg[t]["input_side"]+agg[t]["output"]
    return agg

def wilson_upper(k,n,z=1.645):
    if n==0: return 1.0
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; m=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return min(1.0,c+m)

def main():
    heldout=set(json.load(open(f"{BASE}/heldout_tasks.json")))
    c0=resolved("heldout_C0_identity"); hyb=resolved("heldout_HYBRID1_m7_agg2"); sham=resolved("heldout_SHAM")
    if c0 is None or hyb is None:
        print("held-out grades not ready:", "C0" if c0 is None else "", "HYBRID1" if hyb is None else "")
        return
    c0&=heldout; hyb&=heldout
    tk_c0=task_tokens("heldout_C0_identity"); tk_h=task_tokens("heldout_HYBRID1_m7_agg2")
    common=sorted(set(tk_c0)&set(tk_h)&heldout)
    # paired token saving
    sav=[]; outd=[]
    for t in common:
        if tk_c0[t]["total"]>0:
            sav.append(100*(tk_c0[t]["total"]-tk_h[t]["total"])/tk_c0[t]["total"])
            outd.append(tk_h[t]["output"]-tk_c0[t]["output"])
    # outcomes
    regressions=sorted(c0-hyb)  # C0 resolved, HYBRID didn't
    improvements=sorted(hyb-c0)
    rows=[]
    for t in heldout:
        rows.append({"task_id":t,"c0_resolved":t in c0,"hybrid_resolved":t in hyb,
                     "sham_resolved":(t in sham) if sham else None,
                     "vs_baseline":("REGRESSION" if t in c0 and t not in hyb else
                                    "IMPROVEMENT" if t not in c0 and t in hyb else
                                    "both_pass" if t in hyb else "both_fail"),
                     "c0_total_tokens":tk_c0.get(t,{}).get("total"),
                     "hybrid_total_tokens":tk_h.get(t,{}).get("total"),
                     "hybrid_changed_calls":tk_h.get(t,{}).get("changed_calls")})
    with open(f"{BASE}/results/pruning_ab/heldout_outcomes.jsonl","w") as fo:
        for r in rows: fo.write(json.dumps(r)+"\n")
    summary={
        "n_heldout":len(heldout),"n_paired_tokens":len(common),
        "c0_resolved":len(c0),"hybrid_resolved":len(hyb),
        "solve_rate_c0":round(len(c0)/len(heldout),3),"solve_rate_hybrid":round(len(hyb)/len(heldout),3),
        "net_resolution_change":len(hyb)-len(c0),
        "paired_regressions":len(regressions),"paired_improvements":len(improvements),
        "regression_rate":round(len(regressions)/len(c0),3) if c0 else None,
        "regression_loss_ub_95":round(wilson_upper(len(regressions),len(c0)),3) if c0 else None,
        "mean_token_saving_pct":round(st.mean(sav),1) if sav else None,
        "median_token_saving_pct":round(st.median(sav),1) if sav else None,
        "mean_output_delta":round(st.mean(outd),1) if outd else None,
        "regressed_ids":regressions,"improved_ids":improvements,
    }
    json.dump(summary, open(f"{BASE}/results/pruning_ab/heldout_summary.json","w"), indent=1)
    print(json.dumps(summary, indent=1))

if __name__=="__main__": main()
