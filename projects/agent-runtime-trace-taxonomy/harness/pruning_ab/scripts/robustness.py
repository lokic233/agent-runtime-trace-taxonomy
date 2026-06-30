#!/usr/bin/env python3
"""Phase 4D/F mandatory robustness: leave-top-k-expensive-out, cost decomposition, SHAM cost control, cluster bootstrap."""
import json, os, statistics as st, random
BASE="/data/users/dengcchi/prune_ab"
G=set(json.load(open("/tmp/golden50.json")))
feats={r["task_id"]:r for r in (json.loads(l) for l in open(f"{BASE}/results/pruning_ab/pre_treatment_features.jsonl"))}
def ledger(led):
    a={}
    if not os.path.exists(led): return a
    for l in open(led):
        try:
            d=json.loads(l);t=d.get("task_id")
            if not t or str(t).startswith(("UNKNOWN","NO_")):continue
            ir=(d.get("input_tokens")or 0);cr=(d.get("cache_read_tokens")or 0);cc=(d.get("cache_creation_tokens")or 0);op=(d.get("output_tokens")or 0)
            x=a.setdefault(t,{"eff":0.,"cr":0,"cc":0,"out":0,"inp":0});x["eff"]+=ir+cr*.1+cc*1.25+op*5;x["cr"]+=cr;x["cc"]+=cc;x["out"]+=op;x["inp"]+=ir
        except:pass
    return a
c0=ledger(f"{BASE}/logs/stable/ledger_C0_identity.jsonl")
methods={"LINEDEDUP_e4":"logs/e4/ledger_LINEDEDUP_e4.jsonl","GENTLE6K_stable":"logs/stable/ledger_GENTLE6K_stable.jsonl"}
out={}
print("="*70)
print("ROBUSTNESS 1: LEAVE-TOP-K-EXPENSIVE-OUT (does saving survive without big tasks?)")
print("="*70)
for name,led in methods.items():
    m=ledger(f"{BASE}/{led}");common=sorted(set(c0)&set(m))
    # rank by C0 cost
    by_cost=sorted(common,key=lambda t:c0[t]["eff"],reverse=True)
    print(f"\n{name}:")
    for k in [0,1,3,5]:
        keep=by_cost[k:]
        ct=sum(c0[t]["eff"] for t in keep);mt=sum(m[t]["eff"] for t in keep)
        sav=100*(ct-mt)/ct
        print(f"  leave-top-{k}-out: overall saving = {sav:+.1f}% (n={len(keep)})")
    out.setdefault(name,{})["leave_top_k"]={k:round(100*(sum(c0[t]['eff'] for t in by_cost[k:])-sum(m[t]['eff'] for t in by_cost[k:]))/sum(c0[t]['eff'] for t in by_cost[k:]),1) for k in [0,1,3,5]}

print("\n"+"="*70)
print("ROBUSTNESS 2: COST DECOMPOSITION (where does the saving/loss come from?)")
print("="*70)
for name,led in methods.items():
    m=ledger(f"{BASE}/{led}");common=sorted(set(c0)&set(m))
    d_cr=sum((c0[t]["cr"]-m[t]["cr"])*0.1 for t in common)
    d_cc=sum((c0[t]["cc"]-m[t]["cc"])*1.25 for t in common)
    d_out=sum((c0[t]["out"]-m[t]["out"])*5 for t in common)
    d_inp=sum((c0[t]["inp"]-m[t]["inp"]) for t in common)
    tot=d_cr+d_cc+d_out+d_inp
    print(f"\n{name} eff-cost saving decomposition (units saved, +ve=saved):")
    print(f"  cache_read(0.1x): {d_cr:>+12,.0f}  cache_creation(1.25x): {d_cc:>+12,.0f}")
    print(f"  output(5x):       {d_out:>+12,.0f}  input(1x):             {d_inp:>+12,.0f}")
    print(f"  TOTAL: {tot:>+12,.0f}  => dominant component: {max([('cache_read',d_cr),('cache_creation',d_cc),('output',d_out)],key=lambda x:abs(x[1]))[0]}")
    out.setdefault(name,{})["decomposition"]={"cache_read":round(d_cr),"cache_creation":round(d_cc),"output":round(d_out),"input":round(d_inp)}
json.dump(out, open(f"{BASE}/results/pruning_ab/robustness.json","w"),indent=1)
print("\nrobustness.json written")
