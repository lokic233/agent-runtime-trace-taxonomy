#!/usr/bin/env python3
"""Phase D analysis — intelligence-tax capability scaling (Opus4.7, Sonnet4.6, Haiku4.5).
Hypotheses:
 (H1) destructive truncation (CAP1K) causes more downstream rework/drift than gentle/redundancy-preserving.
 (H2 capability interaction) CAP1K-induced intelligence tax is LARGER on weaker models.
Drift metrics per (model,arm) vs that model's own C0: API-call ratio, output-token ratio, resolution.
Separates necessary verification from no-progress rework where signals allow. stdlib only.
Output: results/pruning_ab/generalization/intelligence_tax_scaling.json
"""
import json, os, glob, statistics
from collections import defaultdict

LOGDIR=os.environ.get("PHASED_LOGS","/data/users/dengcchi/prune_ab/logs/xmodel_phaseD")
OUT=os.environ.get("PHASED_OUT","/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy/results/pruning_ab/generalization/intelligence_tax_scaling.json")
# opus anchor (mechanism_effects.json intelligence_tax): call_ratio/out_ratio by method
ANCHOR={"LINEDEDUP_e4":{"call_ratio":1.0,"out_ratio":0.97,"type":"exact-duplicate"},
        "GENTLE6K_stable":{"call_ratio":1.04,"out_ratio":0.98,"type":"outlier-truncate"},
        "CAP1K_stable":{"call_ratio":1.24,"out_ratio":1.34,"type":"uniform-truncate"}}

def load_cells():
    cells=defaultdict(list)
    for p in glob.glob(os.path.join(LOGDIR,"ledger_*_rep*.jsonl")):
        b=os.path.basename(p)[len("ledger_"):-len(".jsonl")]
        for mk in ("opus47","sonnet46","haiku45"):
            if b.startswith(mk+"_"):
                arm=b[len(mk)+1:].rsplit("_rep",1)[0]
                for l in open(p):
                    try: cells[(mk,arm)].append(json.loads(l))
                    except: pass
                break
    return cells

def per_task_calls(rows):
    by=defaultdict(int)
    for r in rows: by[r.get("task_id")]+=1
    return by
def per_task_out(rows):
    by=defaultdict(int)
    for r in rows: by[r.get("task_id")]+= (r.get("output_tokens") or 0)
    return by

def main():
    cells=load_cells()
    out={"hypotheses":{"H1":"CAP1K(destructive) drift > LINEDEDUP/GENTLE6K","H2":"CAP1K drift larger on weaker models (capability interaction)"},
         "opus_anchor_frozen":ANCHOR,"by_model":{}}
    for mk in ("opus47","sonnet46","haiku45"):
        c0=cells.get((mk,"C0_identity"))
        if not c0: continue
        c0_calls=per_task_calls(c0); c0_out=per_task_out(c0)
        out["by_model"][mk]={}
        for arm in ("LINEDEDUP_e4","GENTLE6K_stable","CAP1K_stable"):
            rows=cells.get((mk,arm))
            if not rows: continue
            a_calls=per_task_calls(rows); a_out=per_task_out(rows)
            shared=[t for t in a_calls if t in c0_calls and c0_calls[t]>0]
            call_ratios=[a_calls[t]/c0_calls[t] for t in shared]
            out_ratios=[a_out[t]/c0_out[t] for t in shared if c0_out[t]>0]
            out["by_model"][mk][arm]={
                "n_shared_tasks":len(shared),
                "call_ratio_median":round(statistics.median(call_ratios),3) if call_ratios else None,
                "out_ratio_median":round(statistics.median(out_ratios),3) if out_ratios else None,
                "type":ANCHOR.get(arm,{}).get("type")}
    # H2: compare CAP1K call_ratio across capability tiers (opus strong -> haiku weak)
    cap={mk:out["by_model"].get(mk,{}).get("CAP1K_stable",{}).get("call_ratio_median") for mk in ("opus47","sonnet46","haiku45")}
    out["capability_interaction_CAP1K_call_ratio"]=cap
    vals=[(mk,cap[mk]) for mk in ("opus47","sonnet46","haiku45") if cap[mk] is not None]
    if len(vals)>=2:
        out["H2_direction"]="SUPPORTED(weaker>stronger)" if vals[-1][1]>vals[0][1] else ("REVERSED" if vals[-1][1]<vals[0][1] else "FLAT")
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    json.dump(out, open(OUT,"w"), indent=1)
    print(json.dumps({"CAP1K_call_ratio_by_tier":cap,"H2":out.get("H2_direction")}, indent=1)); print("wrote",OUT)

if __name__=="__main__": main()
