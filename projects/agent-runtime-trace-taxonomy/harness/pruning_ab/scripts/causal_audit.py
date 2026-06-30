#!/usr/bin/env python3
"""Phase 0: causal data audit. Inventory all runs, reconcile report contradictions, freeze baseline."""
import json, os, glob, hashlib, statistics as st
BASE="/data/users/dengcchi/prune_ab"
G=set(json.load(open("/tmp/golden50.json")))

def ledger_summary(path):
    if not os.path.exists(path): return None
    tasks={}; calls=0; unk=0
    for l in open(path):
        try:
            d=json.loads(l); t=d.get("task_id"); calls+=1
            if not t or str(t).startswith(("UNKNOWN","NO_")): unk+=1; continue
            tasks.setdefault(t,0); tasks[t]+=1
        except: pass
    return {"calls":calls,"unknown_calls":unk,"n_tasks":len(set(tasks)&G),"path":path}

def grade_summary(path):
    if not os.path.exists(path): return None
    d=json.load(open(path))
    return {"completed":len(set(d.get("completed_ids",[]))&G),"resolved":len(set(d.get("resolved_ids",[]))&G)}

manifest={"commit":"bb43b49612760b56a3f8d620fbffcae9dc347bf6",
          "prune_methods_sha256":"cb06efb69c9a08e7a48a1fca747a9fe1e9f71fcf657158a3c5463b028e0d10cf",
          "golden50_size":len(G),"runs":{}}

# canonical treatment set
TREAT={
 "C0_identity":{"ledger":"logs/stable/ledger_C0_identity.jsonl","grade":"results/pruning_ab/stable/grade_C0_identity.json","role":"baseline"},
 "SHAM":{"ledger":None,"grade":None,"role":"noop-control","note":"only in phase34 A/A reps (10 interesting tasks)"},
 "LINEDEDUP_e4":{"ledger":"logs/e4/ledger_LINEDEDUP_e4.jsonl","grade":"results/pruning_ab/e4/grade_LINEDEDUP_e4.json","role":"treatment"},
 "GENTLE6K_stable":{"ledger":"logs/stable/ledger_GENTLE6K_stable.jsonl","grade":"results/pruning_ab/stable/grade_GENTLE6K_stable.json","role":"treatment"},
 "HYBRID1_m7_agg2":{"ledger":"logs/ledger_HYBRID1_m7_agg2.jsonl","grade":"results/pruning_ab/grade_HYBRID1_m7_agg2.json","role":"cache-bust-control","note":"ledger is POOLED/contaminated (not task-tagged)"},
 "RETRIEVREF_e4":{"ledger":"logs/e4/ledger_RETRIEVREF_e4.jsonl","grade":"results/pruning_ab/e4/grade_RETRIEVREF_e4.json","role":"near-neutral-control"},
}
for m,info in TREAT.items():
    rec={"role":info["role"]}
    if info.get("note"): rec["note"]=info["note"]
    if info["ledger"]: rec["ledger"]=ledger_summary(f"{BASE}/{info['ledger']}")
    if info["grade"]: rec["grade"]=grade_summary(f"{BASE}/{info['grade']}")
    manifest["runs"][m]=rec

# A/A repeated runs (the causal repeated-measures data)
aa={}
for method in ["C0_identity","SHAM","HYBRID1_m7_agg2"]:
    reps={}
    for r in range(1,6):
        g=grade_summary(f"{BASE}/results/pruning_ab/phase34/grade_{method}_rep{r}.json")
        led=ledger_summary(f"{BASE}/logs/phase34/ledger_{method}_rep{r}.jsonl")
        if g or led: reps[f"rep{r}"]={"grade":g,"ledger":led}
    aa[method]=reps
manifest["aa_repeated_runs"]={"n_interesting_tasks":10,"methods":aa}

# canonical baseline decision
manifest["canonical_baseline"]={
 "for_golden50_cost":"logs/stable/ledger_C0_identity.jsonl (task-tagged, 50 tasks)",
 "for_golden50_resolution":"results/pruning_ab/stable/grade_C0_identity.json",
 "for_AA_repeated":"phase34 C0 reps 1-5 (10 interesting tasks, repeated)",
 "note":"original results/pruning_ab/grade_C0_identity.json (48/50) used DIFFERENT run; stable tagged C0 (46/50) is canonical for E3/E4 pairing"}

os.makedirs(f"{BASE}/results/pruning_ab",exist_ok=True)
json.dump(manifest, open(f"{BASE}/results/pruning_ab/causal_data_manifest.json","w"), indent=1, default=str)
print("=== CANONICAL TREATMENT SET ===")
for m,r in manifest["runs"].items():
    led=r.get("ledger"); grd=r.get("grade")
    print(f"  {m:18s} role={r['role']:18s} ledger_tasks={led['n_tasks'] if led else 'NONE'} grade={grd if grd else 'NONE'}")
    if r.get("note"): print(f"      NOTE: {r['note']}")
print("\n=== A/A REPEATED RUNS (causal repeated-measures, 10 interesting tasks) ===")
for m,reps in aa.items():
    graded=[r for r,v in reps.items() if v.get('grade')]
    print(f"  {m}: {len(graded)} graded reps {graded}")
print("\ncausal_data_manifest.json written")
