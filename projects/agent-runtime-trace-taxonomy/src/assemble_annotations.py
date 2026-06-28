import json, glob, os, sys, re
sys.path.insert(0,'/data/users/dengcchi/agent_runtime_proj/arttx_repo/projects/agent-runtime-trace-taxonomy/src')
from parse_annotator_output import extract_json
def trace_id_of(r):
    tid=r.get("trace_id")
    if tid: return tid
    sid=r.get("sample_id") or ""
    # sample_id like BOOT/PILOT-<task>@solver_X  or BOOT-<task>@solver_X
    m=re.search(r'([\w.\-]+@solver_[A-F])', sid)
    return m.group(1) if m else None
out={}
for ann in ("ann1","ann2","ann3"):
    recs=[]; bad=0
    for bi in range(10):
        f=f"/tmp/pilot_out/{ann}_b{bi}.json"
        if not os.path.exists(f) or os.path.getsize(f)==0: continue
        d=extract_json(open(f).read())
        if isinstance(d,list): recs+=d
        elif isinstance(d,dict): recs.append(d)
        else: bad+=1
    seen=set(); uniq=[]
    for r in recs:
        if not isinstance(r,dict): continue
        tid=trace_id_of(r)
        if tid and tid not in seen:
            seen.add(tid); r["trace_id"]=tid; uniq.append(r)
    json.dump(uniq, open(f"/tmp/pilot_out/{ann}_assembled.json","w"))
    out[ann]={"records":len(uniq),"bad_batches":bad}
print(json.dumps(out,indent=2))
