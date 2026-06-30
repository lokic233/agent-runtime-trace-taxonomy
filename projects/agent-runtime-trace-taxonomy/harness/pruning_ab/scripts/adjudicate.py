import json, os, sys
BASE="/data/users/dengcchi/prune_ab"
G=set(json.load(open("/tmp/golden50.json")))
sealed=json.load(open(f"{BASE}/results/pruning_ab/sealed_outcomes.json"))
anns=[json.loads(l) for l in open(f"{BASE}/results/pruning_ab/blind_frontier_annotations.jsonl") if '_error' not in l]

# DETERMINISTIC adjudication (no second LLM needed; avoids forensic-storytelling).
# Map preferred_action -> which method's outcome it corresponds to, check if blind cost prediction held.
# preferred_action in {NO_OP/KEEP_FULL_CONTENT} => predicts NO saving (keep). LINE_DEDUP=>LINEDEDUP. GENTLE_CAP=>GENTLE6K.
def task_of(eid): return eid.split("#")[0]
def adjudicate(a):
    t=task_of(a["_event_id"]); o=sealed.get(t+"#task")
    if not o: return "UNIDENTIFIED","no sealed outcome"
    act=a.get("preferred_action"); pred_cost=a.get("predicted_local_effect",{}).get("cost")
    ld=o.get("ld_saving_pct"); g6=o.get("g6_saving_pct")
    # determine the realized saving for the action the annotator preferred
    if act=="LINE_DEDUP": realized=ld
    elif act=="GENTLE_CAP": realized=g6
    elif act in ("NO_OP","KEEP_FULL_CONTENT"): 
        # annotator said keep -> validated if BOTH methods would have hurt or been neutral
        if ld is not None and g6 is not None:
            if max(ld,g6)<=5: return "VALIDATED_CANDIDATE", f"keep correct: best method saving {max(ld,g6):.0f}%<=5%"
            else: return "REJECTED", f"keep wrong: a method saved {max(ld,g6):.0f}%"
        return "UNIDENTIFIED","missing method outcomes"
    else: return "UNIDENTIFIED", f"action {act} not in observational data"
    if realized is None: return "INSUFFICIENT_COUNTERFACTUAL", f"no {act} outcome for task"
    # predicted decrease (saving) and realized saving>5%?
    if pred_cost=="decrease":
        if realized>5: return "VALIDATED_CANDIDATE", f"predicted save, realized +{realized:.0f}%"
        elif realized<-5: return "REJECTED", f"predicted save, realized {realized:.0f}% (hurt)"
        else: return "CONDITIONALLY_VALID", f"predicted save, realized {realized:.0f}% (neutral)"
    elif pred_cost=="increase":
        if realized<-5: return "VALIDATED_CANDIDATE", f"predicted hurt, realized {realized:.0f}%"
        elif realized>5: return "REJECTED", f"predicted hurt, realized +{realized:.0f}%"
        else: return "CONDITIONALLY_VALID", f"predicted hurt, realized {realized:.0f}%"
    else:  # neutral
        return ("VALIDATED_CANDIDATE" if abs(realized)<=5 else "CONDITIONALLY_VALID"), f"predicted neutral, realized {realized:.0f}%"

out=[]
from collections import Counter
verdicts=Counter()
for a in anns:
    v,reason=adjudicate(a)
    verdicts[v]+=1
    out.append({"event_id":a["_event_id"],"role":a["_role"],"preferred_action":a.get("preferred_action"),
                "predicted_cost":a.get("predicted_local_effect",{}).get("cost"),"adjudication":v,"reason":reason,
                "note":"single-paired-run; CONDITIONALLY/REJECTED reflect observational outcome NOT randomized causal proof"})
with open(f"{BASE}/results/pruning_ab/outcome_aware_adjudication.jsonl","w") as fo:
    for r in out: fo.write(json.dumps(r)+"\n")
print(f"adjudicated {len(out)} blind annotations")
for v,n in verdicts.most_common(): print(f"  {v}: {n}")
print("\nIMPORTANT: these are OBSERVATIONAL adjudications (single paired run). VALIDATED_CANDIDATE means")
print("the blind prediction matched the observed outcome — NOT that the effect is randomized-causal.")
print("Phase 8 MRT is required for causal validation. (per mission: forensic plausibility != causal proof)")
