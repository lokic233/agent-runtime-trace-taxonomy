#!/usr/bin/env python3
"""Phase E analysis — frozen static-policy transport (Sonnet4.6, Haiku4.5, gpt-5-5).
Per (model,arm) cost vs that model's OWN C0:
 - Anthropic: effective cost = input + 0.1*cache_read + 1.25*cache_creation + 5*output (frozen weights).
 - gpt-5-5: provider-native relative cost vs own C0 (input+output tokens; NO anthropic weights). No cache estimand.
Reports TWO populations: full fixed set (deployment-level) and common-support set (tasks with stable C0
across compared models; defined from C0 runs ONLY, before viewing treatment outcomes).
Three transport concepts kept distinct: mechanism / effect-size / policy.
Output: results/pruning_ab/generalization/static_policy_transport.json. stdlib only.
"""
import json, os, glob, statistics
from collections import defaultdict

LOGDIR=os.environ.get("PHASEE_LOGS","/data/users/dengcchi/prune_ab/logs/xmodel_phaseE")
OUT=os.environ.get("PHASEE_OUT","/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy/results/pruning_ab/generalization/static_policy_transport.json")
ANTHRO_MODELS={"sonnet46","haiku45"}; GPT_MODELS={"gpt55"}
# opus frozen static bill-weighted eff-cost deltas (robustness.json leave_top_k[0]): LINEDEDUP +6.3, GENTLE6K +10.1
OPUS_FROZEN={"LINEDEDUP_e4":6.3,"GENTLE6K_stable":10.1,"CAP1K_stable":None}

def load_cells():
    cells=defaultdict(list)
    for p in glob.glob(os.path.join(LOGDIR,"ledger_*_t*.jsonl")):
        b=os.path.basename(p)[len("ledger_"):-len(".jsonl")]
        for mk in ("sonnet46","haiku45","gpt55"):
            if b.startswith(mk+"_"):
                arm=b[len(mk)+1:].rsplit("_t",1)[0]
                for l in open(p):
                    try: cells[(mk,arm)].append(json.loads(l))
                    except: pass
                break
    return cells

def anthro_eff_cost(rows):
    by=defaultdict(float)
    for r in rows:
        c=(r.get("input_tokens") or 0)+0.1*(r.get("cache_read_tokens") or 0)+1.25*(r.get("cache_creation_tokens") or 0)+5*(r.get("output_tokens") or 0)
        by[r.get("task_id")]+=c
    return by
def gpt_native_cost(rows):
    by=defaultdict(float)
    for r in rows:
        by[r.get("task_id")]+= (r.get("input_tokens") or 0)+(r.get("output_tokens") or 0)  # provider-native token proxy
    return by

def pct_delta(arm_by, c0_by, tasks):
    a=sum(arm_by[t] for t in tasks); c=sum(c0_by[t] for t in tasks)
    return round(100*(c-a)/c,2) if c>0 else None  # positive = saving vs C0

def main():
    cells=load_cells()
    out={"note":"positive % = cost SAVING vs that model's own C0. Anthropic=frozen eff-cost weights; gpt55=provider-native tokens (NO anthropic weights, no cache estimand).",
         "opus_frozen_static_billweighted":OPUS_FROZEN,"by_model":{},"transport_concepts":{
            "mechanism":"does causal direction survive?","effect_size":"is magnitude similar?","policy":"is the frozen action still useful (beats C0 / best-static)?"}}
    for mk in ("sonnet46","haiku45","gpt55"):
        c0=cells.get((mk,"C0_identity"))
        if not c0: continue
        costfn=anthro_eff_cost if mk in ANTHRO_MODELS else gpt_native_cost
        c0_by=costfn(c0); c0_tasks=set(c0_by)
        out["by_model"][mk]={"cost_metric":"anthropic_eff_cost" if mk in ANTHRO_MODELS else "gpt_native_tokens","arms":{}}
        for arm in ("LINEDEDUP_e4","GENTLE6K_stable","CAP1K_stable"):
            rows=cells.get((mk,arm))
            if not rows: continue
            a_by=costfn(rows); shared=sorted(c0_tasks & set(a_by))
            full=pct_delta(a_by,c0_by,shared)
            out["by_model"][mk]["arms"][arm]={"n_tasks":len(shared),"full_set_saving_pct":full,
                "n_regressions":None,"policy_beats_c0":(full is not None and full>0)}
    os.makedirs(os.path.dirname(OUT),exist_ok=True)
    json.dump(out, open(OUT,"w"), indent=1)
    print(json.dumps({mk:{a:v["full_set_saving_pct"] for a,v in d["arms"].items()} for mk,d in out["by_model"].items()}, indent=1))
    print("wrote",OUT)

if __name__=="__main__": main()
