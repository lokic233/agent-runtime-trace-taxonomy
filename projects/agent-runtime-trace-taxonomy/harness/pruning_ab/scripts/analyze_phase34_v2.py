#!/usr/bin/env python3
"""Phase 3+4 analysis: A/A + SHAM noise floor + interesting-task classification.
Emits aa_noise_results.json + interesting_task_repeats.jsonl. Robust to partial completion."""
import json, glob, os, statistics as st, math
from collections import defaultdict
BASE="/data/users/dengcchi/prune_ab"
INT10=json.load(open("/tmp/interesting10.json"))
GD=f"{BASE}/results/pruning_ab/phase34"; LD=f"{BASE}/logs/phase34"

def resolved(tag):
    f=f"{GD}/grade_{tag}.json"
    return set(json.load(open(f)).get("resolved_ids",[])) if os.path.exists(f) else None

def reps(method):
    return {r:resolved(f"{method}_rep{r}") for r in range(1,6) if resolved(f"{method}_rep{r}") is not None}

def activation(method,rep,task):
    f=f"{LD}/ledger_{method}_rep{rep}.jsonl"
    if not os.path.exists(f): return None
    tot=ch=chars=0; calls=0
    for l in open(f):
        try:
            d=json.loads(l)
            if d.get("task_id")==task:
                calls+=1
                if d.get("changed"): ch+=1; chars+=d.get("characters_removed",0)
        except: pass
    return {"calls":calls,"changed_calls":ch,"chars_removed":chars} if calls else None

def task_tokens(method,rep,task):
    """task-level total tokens from ledger (input+cache_read+cache_creation+output)."""
    f=f"{LD}/ledger_{method}_rep{rep}.jsonl"
    if not os.path.exists(f): return None
    ins=out=0; n=0
    for l in open(f):
        try:
            d=json.loads(l)
            if d.get("task_id")==task:
                ins+=(d.get("input_tokens") or 0)+(d.get("cache_read_tokens") or 0)+(d.get("cache_creation_tokens") or 0)
                out+=(d.get("output_tokens") or 0); n+=1
        except: pass
    return {"input_side":ins,"output":out,"total":ins+out,"calls":n} if n else None

def main():
    res={"methods":{},"interesting_tasks":{}}
    print("=== PHASE 3: A/A + SHAM NOISE FLOOR ===")
    for method in ["C0_identity","SHAM","HYBRID1_m7_agg2"]:
        rd=reps(method)
        if not rd: print(f"  {method}: 0 reps graded"); continue
        # outcome stability across reps
        flips=defaultdict(list)
        for t in INT10:
            flips[t]=[1 if (rd[r] and t in rd[r]) else 0 for r in rd]
        unstable={t:o for t,o in flips.items() if len(set(o))>1}
        # token variance per task
        tokvar={}
        for t in INT10:
            tt=[task_tokens(method,r,t) for r in rd]
            tt=[x["total"] for x in tt if x]
            if len(tt)>=2: tokvar[t]=round(st.stdev(tt)/st.mean(tt),3) if st.mean(tt) else 0
        res["methods"][method]={"reps_graded":len(rd),"unstable_tasks":list(unstable.keys()),
            "n_unstable":len(unstable),"flip_detail":dict(unstable),
            "mean_token_cv":round(st.mean(list(tokvar.values())),3) if tokvar else None}
        print(f"  {method}: {len(rd)} reps, {len(unstable)}/{len(INT10)} unstable tasks, token CV={res['methods'][method]['mean_token_cv']}")
        for t,o in unstable.items(): print(f"      {t}: {o}")
    # A/A flip rate = the noise floor
    c0=reps("C0_identity")
    if c0 and len(c0)>=2:
        aa_flips=sum(1 for t in INT10 if len(set(1 if t in c0[r] else 0 for r in c0))>1)
        res["aa_noise_floor_flip_rate"]=round(aa_flips/len(INT10),3)
        print(f"\n  A/A NOISE FLOOR: {aa_flips}/{len(INT10)} tasks flip across C0 reps = {res['aa_noise_floor_flip_rate']} flip rate")

    print("\n=== PHASE 4: INTERESTING-TASK CLASSIFICATION ===")
    c0=reps("C0_identity"); sham=reps("SHAM"); hyb=reps("HYBRID1_m7_agg2")
    repeats=[]
    for t in INT10:
        c0o=[1 if t in c0[r] else 0 for r in c0] if c0 else []
        sho=[1 if t in sham[r] else 0 for r in sham] if sham else []
        hyo=[1 if t in hyb[r] else 0 for r in hyb] if hyb else []
        acts=[activation("HYBRID1_m7_agg2",r,t) for r in (hyb or {})]
        fired=sum(1 for a in acts if a and a["changed_calls"]>0)
        cls="INCONCLUSIVE"
        if c0o and sho and hyo:
            c0_stable=len(set(c0o))==1; sham_stable=len(set(sho))==1
            c0_pass=st.mean(c0o)>0.5; hyb_pass=st.mean(hyo)>0.5
            if not c0_stable or not sham_stable: cls="INHERENTLY_UNSTABLE"
            elif fired==0 and hyo!=c0o: cls="NO_OP_FALSE_ATTRIBUTION"
            elif c0_pass and sham_stable and st.mean(hyo)<0.5 and fired>0: cls="TRUE_PRUNING_FRAGILITY"
            elif (not c0_pass) and hyb_pass and fired>0: cls="TRUE_PRUNING_IMPROVEMENT"
            elif c0_stable and sham_stable and hyo==c0o: cls="STABLE_NO_EFFECT"
        rec={"task_id":t,"C0":c0o,"SHAM":sho,"HYBRID1":hyo,"hybrid_fired_reps":fired,"classification":cls}
        repeats.append(rec); res["interesting_tasks"][t]=rec
        print(f"  {t:35s} C0={c0o} SHAM={sho} HYB={hyo} fired={fired} -> {cls}")
    json.dump(res, open(f"{BASE}/results/pruning_ab/aa_noise_results.json","w"), indent=1)
    with open(f"{BASE}/results/pruning_ab/interesting_task_repeats.jsonl","w") as fo:
        for r in repeats: fo.write(json.dumps(r)+"\n")
    print(f"\nwrote aa_noise_results.json + interesting_task_repeats.jsonl")

if __name__=="__main__": main()
