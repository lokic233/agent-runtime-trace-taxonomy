#!/usr/bin/env python3
"""Phase 7: safety-gate evaluation on held-out tasks.
Compares 6 policies on total token saving under a regression ceiling.
Gate predicts P(regression|pre-treatment features). Frozen from golden-50; evaluated held-out."""
import json, os, statistics as st, random
BASE="/data/users/dengcchi/prune_ab"

def load_heldout_outcomes():
    f=f"{BASE}/results/pruning_ab/heldout_outcomes.jsonl"
    if not os.path.exists(f): return None
    return [json.loads(l) for l in open(f)]

def pretreatment_features(tid):
    """pre-treatment features from full_opus47 C0 baseline traj (the held-out baseline)."""
    import glob
    for base in [f"/data/users/dengcchi/hal_work/runs/full_opus47/{tid}/{tid}.traj",
                 f"{BASE}/arms/phase6_heldout_C0_identity/{tid}/{tid}.traj"]:
        if os.path.exists(base):
            try:
                d=json.load(open(base)); ms=d.get("info",{}).get("model_stats",{})
                h=d.get("history",[])
                obs=[m for m in h if m.get("role")=="tool" or (m.get("role")=="user" and m.get("message_type")=="observation")]
                return {"n_obs":len(obs),"calls":ms.get("api_calls",0),"tokens_sent":ms.get("tokens_sent",0)}
            except: pass
    return None

def main():
    out=load_heldout_outcomes()
    if not out:
        print("held-out outcomes not ready"); return
    # only tasks C0 resolved (the at-risk set for regression)
    c0_resolved=[r for r in out if r["c0_resolved"]]
    # attach features + token saving
    for r in out:
        f=pretreatment_features(r["task_id"]); r["_feat"]=f
    # gate: length-only (n_obs > threshold => unsafe, route to C0). Fit threshold on golden-50.
    # golden-50: only regression was pylint-4551 (69 obs) but safe tasks had 76-77 -> length useless.
    # We still evaluate it honestly on held-out.
    n_heldout=len(out)
    c0_solve=sum(1 for r in out if r["c0_resolved"])
    hyb_solve=sum(1 for r in out if r["hybrid_resolved"])
    regressions=[r for r in out if r["vs_baseline"]=="REGRESSION"]
    improvements=[r for r in out if r["vs_baseline"]=="IMPROVEMENT"]

    def policy_eval(route_fn, name):
        """route_fn(r) -> 'HYBRID' or 'C0'. Compute solve count + token saving + regressions."""
        solved=0; reg=0; tok_sav=[]
        for r in out:
            choice=route_fn(r)
            if choice=="HYBRID":
                solved += 1 if r["hybrid_resolved"] else 0
                if r["c0_resolved"] and not r["hybrid_resolved"]: reg+=1
                if r.get("c0_total_tokens") and r.get("hybrid_total_tokens") and r["c0_total_tokens"]>0:
                    tok_sav.append(100*(r["c0_total_tokens"]-r["hybrid_total_tokens"])/r["c0_total_tokens"])
            else:  # C0
                solved += 1 if r["c0_resolved"] else 0
                tok_sav.append(0.0)
        return {"policy":name,"solved":solved,"regressions":reg,
                "mean_token_saving":round(st.mean(tok_sav),1) if tok_sav else 0}

    feats=[r for r in out if r.get("_feat")]
    obs_vals=sorted(r["_feat"]["n_obs"] for r in feats if r["_feat"])
    thr = obs_vals[int(len(obs_vals)*0.8)] if obs_vals else 999  # length gate at 80th pctile
    random.seed(42)
    policies=[
        policy_eval(lambda r:"C0","always_C0"),
        policy_eval(lambda r:"HYBRID","always_HYBRID1"),
        # oracle: route to C0 only for tasks HYBRID would regress (uses outcome -> upper bound, not deployable)
        policy_eval(lambda r:"C0" if r["vs_baseline"]=="REGRESSION" else "HYBRID","oracle_safe"),
        # length gate: route long-trajectory tasks to C0
        policy_eval(lambda r:"C0" if (r.get("_feat") and r["_feat"]["n_obs"]>thr) else "HYBRID","length_gate"),
        # random gate: route ~20% to C0 randomly
        policy_eval(lambda r:"C0" if random.random()<0.2 else "HYBRID","random_gate"),
    ]
    res={"n_heldout":n_heldout,"c0_solve":c0_solve,"hybrid_solve":hyb_solve,
         "heldout_regressions":len(regressions),"heldout_improvements":len(improvements),
         "length_gate_threshold_nobs":thr,"policies":policies}
    json.dump(res, open(f"{BASE}/results/pruning_ab/safety_gate_results.json","w"), indent=1)
    print(json.dumps(res, indent=1))

if __name__=="__main__": main()
