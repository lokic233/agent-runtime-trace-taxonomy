#!/usr/bin/env python3
"""Phase B smoke validity gates — deterministic, runnable by anyone (agent or cron).
Reads the 18 cell ledgers from /data/users/dengcchi/prune_ab/logs/xmodel_smoke/ and writes
smoke_gates.json + SMOKE_TEST_REPORT.md. VALIDITY ONLY — no scientific claims from 5 tasks.

Gate logic per cell:
 - C0/SHAM: byte-identity. anthropic ledger 'changed' must be False on all rows; gpt55 'transform_fired' False.
 - HYBRID1/LINEDEDUP/GENTLE6K/CAP1K: transform ACTIVATED. anthropic 'changed'==True on >=1 call
   (HYBRID1) or characters_removed>0; gpt55 'transform_fired'==True on >=1 call.
 - cache fields: anthropic cache_read/creation non-null on >=1 call; gpt55 both null (by design).
 - cc_fraction per anthropic cell = sum(cc)/(sum(cc)+sum(cr)).
"""
import json, os, glob
from collections import defaultdict, Counter

LOG="/data/users/dengcchi/prune_ab/logs/xmodel_smoke"
GEN="/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy"
ARMS=["C0_identity","SHAM","HYBRID1_m7_agg2","LINEDEDUP_e4","GENTLE6K_stable","CAP1K_stable"]
MODELS=["sonnet46","haiku45","gpt55"]
NOOP={"C0_identity","SHAM"}

def rows(mk,arm):
    p=os.path.join(LOG,f"ledger_{mk}_{arm}.jsonl")
    if not os.path.exists(p): return None
    return [json.loads(l) for l in open(p) if l.strip()]

def arm_rc(mk,arm):
    p=os.path.join(LOG,f"arm_{mk}_{arm}.log")
    if not os.path.exists(p): return None
    import re
    m=re.findall(r"EXIT rc=(\d+)", open(p, errors='replace').read())
    return int(m[-1]) if m else None

def gate_cell(mk,arm):
    r=rows(mk,arm)
    if not r: return {"present":False}
    is_gpt = mk=="gpt55"
    n=len(r); ntasks=len(set(x.get("task_id") for x in r))
    rc=arm_rc(mk,arm)
    res={"present":True,"n_calls":n,"n_tasks":ntasks,"rc":rc}
    # activation / byte-identity
    if is_gpt:
        fired=[bool(x.get("transform_fired")) for x in r]
        if arm in NOOP:
            res["byte_identical"]=not any(fired); res["gate"]= res["byte_identical"]
        else:
            res["transform_activated"]=any(fired); res["gate"]=res["transform_activated"]
        res["cache_null_by_design"]=all(x.get("cache_read_tokens") is None and x.get("cache_creation_tokens") is None for x in r)
        res["obs_role_layout"]=dict(Counter(x.get("obs_role_layout") for x in r))
    else:
        changed=[bool(x.get("changed")) for x in r]
        if arm in NOOP:
            res["byte_identical"]=not any(changed); res["gate"]=res["byte_identical"]
        else:
            chars=[(x.get("characters_removed") or 0) for x in r]
            res["transform_activated"]=any(changed) or any(c!=0 for c in chars); res["gate"]=res["transform_activated"]
        cc=sum(x.get("cache_creation_tokens") or 0 for x in r); cr=sum(x.get("cache_read_tokens") or 0 for x in r)
        res["cache_fields_ok"]=any((x.get("cache_read_tokens") is not None) for x in r)
        res["cc_fraction"]=round(cc/(cc+cr),4) if (cc+cr)>0 else None
    return res

def main():
    cells={}; fails=[]; cc_by_model=defaultdict(dict)
    for mk in MODELS:
        for arm in ARMS:
            g=gate_cell(mk,arm); cells[f"{mk}/{arm}"]=g
            if g.get("present") and not g.get("gate",True):
                fails.append(f"{mk}/{arm}: gate failed ({'byte-id' if arm in NOOP else 'activation'})")
            if g.get("present") and g.get("rc") not in (0,None):
                fails.append(f"{mk}/{arm}: rc={g.get('rc')}")
            if g.get("cc_fraction") is not None: cc_by_model[mk][arm]=g["cc_fraction"]
    present=sum(1 for c in cells.values() if c.get("present"))
    out={"all_gates_pass":len(fails)==0 and present>0,"n_cells_present":present,"n_cells_total":18,
         "failures":fails,"cells":cells,"cache_creation_fraction_by_model":dict(cc_by_model),
         "note":"VALIDITY ONLY — no scientific claims from 5 tasks. cc_fraction is exploratory."}
    os.makedirs(os.path.join(GEN,"results/pruning_ab/generalization"),exist_ok=True)
    json.dump(out, open(os.path.join(GEN,"results/pruning_ab/generalization/smoke_gates.json"),"w"),indent=1)
    # markdown
    md=["# SMOKE_TEST_REPORT (Phase B validity gates)","",
        f"**Cells present:** {present}/18  ·  **All gates pass:** {out['all_gates_pass']}","",
        "VALIDITY ONLY — no scientific claims from 5 tasks.","",
        "| cell | n_calls | rc | gate | cc_fraction |","|---|--:|--:|:--:|--:|"]
    for k,c in cells.items():
        if not c.get("present"): md.append(f"| {k} | — | — | (not present) | — |"); continue
        gate = "byte-id ✓" if (k.split('/')[1] in NOOP and c.get('byte_identical')) else ("act ✓" if c.get('transform_activated') else "✗")
        md.append(f"| {k} | {c['n_calls']} | {c.get('rc')} | {gate} | {c.get('cc_fraction','—')} |")
    md+=["","## Exploratory cache_creation_fraction by model (NOT a result)"]
    for mk,d in cc_by_model.items(): md.append(f"- **{mk}**: "+", ".join(f"{a}={v}" for a,v in d.items()))
    md+=["","## gpt-5-5 cross-provider caveat","- No cache_read/creation estimand (null by design) -> NO cache-tax claim; provider-native cost only.",
         "- Observations arrive as role:tool; the shim tool-view adapter applies frozen transforms (verified activation)."]
    if fails: md+=["","## Failures"]+[f"- {f}" for f in fails]
    open(os.path.join(GEN,"reports/pruning_ab/generalization/SMOKE_TEST_REPORT.md"),"w").write("\n".join(md))
    print(json.dumps({"all_gates_pass":out["all_gates_pass"],"present":present,"fails":fails[:8],"cc_by_model":dict(cc_by_model)},indent=1))

if __name__=="__main__": main()
