#!/usr/bin/env python3
"""Phase 3+4 analysis: A/A noise floor + interesting-task classification."""
import json, glob, os, statistics as st
from collections import defaultdict

INT10=json.load(open("/tmp/interesting10.json"))
GRADE_DIR="results/pruning_ab/phase34"
LED_DIR="logs/phase34"

def resolved(tag):
    f=f"{GRADE_DIR}/grade_{tag}.json"
    if os.path.exists(f):
        return set(json.load(open(f)).get("resolved_ids",[]))
    return None

def reps(method):
    out={}
    for r in [1,2,3,4,5]:
        rs=resolved(f"{method}_rep{r}")
        if rs is not None: out[r]=rs
    return out

def activation(method, rep, task):
    """did pruning actually fire for this task in this rep?"""
    f=f"{LED_DIR}/ledger_{method}_rep{rep}.jsonl"
    if not os.path.exists(f): return None
    ch=0; tot=0; chars=0
    for l in open(f):
        try:
            d=json.loads(l)
            if d.get("task_id")==task:
                tot+=1
                if d.get("changed"): ch+=1; chars+=d.get("characters_removed",0)
        except: pass
    return {"calls":tot,"changed_calls":ch,"chars_removed":chars} if tot else None

def flip_rates(reps_dict, tasks):
    """across all rep-pairs, success<->failure flip rates per task"""
    per_task=defaultdict(list)
    rs_list=list(reps_dict.values())
    for t in tasks:
        outcomes=[1 if t in rs else 0 for rs in rs_list]
        per_task[t]=outcomes
    return per_task

if __name__=="__main__":
    print("=== PHASE 3: A/A + SHAM NOISE FLOOR ===")
    for method in ["C0_identity","SHAM","HYBRID1_m7_agg2"]:
        rd=reps(method)
        if not rd: print(f"  {method}: no graded reps yet"); continue
        print(f"\n{method}: {len(rd)} reps graded")
        ft=flip_rates(rd, INT10)
        # flip = any task whose outcome is not constant across reps
        flippers={t:o for t,o in ft.items() if len(set(o))>1}
        print(f"  unstable tasks (outcome varies across reps): {len(flippers)}/{len(INT10)}")
        for t,o in flippers.items(): print(f"    {t}: {o}")
    print("\n=== PHASE 4: CLASSIFICATION ===")
    c0=reps("C0_identity"); sham=reps("SHAM"); hyb=reps("HYBRID1_m7_agg2")
    for t in INT10:
        c0_o=[1 if t in c0[r] else 0 for r in c0] if c0 else []
        sh_o=[1 if t in sham[r] else 0 for r in sham] if sham else []
        hy_o=[1 if t in hyb[r] else 0 for r in hyb] if hyb else []
        # activation check for HYBRID
        act=[activation("HYBRID1_m7_agg2",r,t) for r in (hyb or {})]
        act_fired=sum(1 for a in act if a and a["changed_calls"]>0)
        c0_stable = c0_o and len(set(c0_o))==1
        sham_stable = sh_o and len(set(sh_o))==1
        c0_pass = c0_o and st.mean(c0_o)>0.5
        hyb_pass = hy_o and st.mean(hy_o)>0.5
        cls="INCONCLUSIVE"
        if c0_o and sham_o and hy_o:
            if not c0_stable or not sham_stable: cls="INHERENTLY_UNSTABLE"
            elif act_fired==0 and hy_o!=c0_o: cls="NO_OP_FALSE_ATTRIBUTION"
            elif c0_pass and sham_stable and st.mean(hy_o)<0.5 and act_fired>0: cls="TRUE_PRUNING_FRAGILITY"
            elif not c0_pass and st.mean(hy_o)>0.5 and act_fired>0: cls="TRUE_PRUNING_IMPROVEMENT"
        print(f"  {t:35s} C0={c0_o} SHAM={sh_o} HYB={hy_o} fired={act_fired} -> {cls}")
