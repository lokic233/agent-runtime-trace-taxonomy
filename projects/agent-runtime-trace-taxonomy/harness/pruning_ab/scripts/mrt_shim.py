#!/usr/bin/env python3
"""Micro-Randomized Trial shim: per-call action randomization with propensity + prefix-feature logging.
Each eligible call randomizes among {NO_OP, LINEDEDUP_seg, GENTLE_CAP_seg} and logs everything for
event-level causal estimation. Preserves original content for rollback analysis."""
import os, sys, json, time, tempfile, subprocess, http.server, socketserver, threading, hashlib, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prune_methods as PM

PORT=int(os.environ.get("PB_SHIM_PORT","8901"))
LEDGER=os.environ.get("PB_LEDGER","/data/users/dengcchi/prune_ab/logs/mrt/ledger.jsonl")
EVENTLOG=os.environ.get("PB_EVENTLOG","/data/users/dengcchi/prune_ab/logs/mrt/events.jsonl")
SEED=int(os.environ.get("MRT_SEED","12345"))
PB_URL="https://plugboard.x2p.facebook.net/v1/messages"
CERT=os.environ.get("PB_CERT","/var/facebook/credentials/dengcchi/x509/dengcchi.pem")
FP=json.load(open("/data/users/dengcchi/prune_ab/task_fingerprints.json")) if os.path.exists("/data/users/dengcchi/prune_ab/task_fingerprints.json") else {}
_lock=threading.Lock(); _callcount={}; _rng={}

# randomization probabilities (preregistered)
PROBS=[("NO_OP",0.50),("LINEDEDUP_seg",0.25),("GENTLE_CAP_seg",0.25)]
MIN_SEGMENT_CHARS=2000  # eligibility: only randomize if a candidate obs exceeds this

def task_of(msgs):
    for m in msgs:
        if m.get("role")=="user":
            t=m.get("content")
            if isinstance(t,list): t=" ".join(x.get("text","") for x in t if isinstance(x,dict))
            elif not isinstance(t,str): t=str(t)
            return FP.get(hashlib.sha256(t[:2000].encode()).hexdigest()[:16], "UNK")
    return "UNK"

def obs_indices(msgs):
    n=len(msgs)
    return [i for i,m in enumerate(msgs) if PM._is_obs(i,m,n)]

def prefix_features(msgs, tid):
    """PREFIX-STATE features at this call — computed ONLY from messages present now."""
    oidx=obs_indices(msgs)
    obs=[PM._txt(msgs[i].get("content")) for i in oidx]
    all_lines=[]; 
    for o in obs: all_lines+=[l.strip() for l in o.split("\n") if len(l.strip())>=12]
    seen=set(); dup=0
    for l in all_lines:
        if l in seen: dup+=1
        else: seen.add(l)
    sizes=sorted(len(o) for o in obs) or [0]
    return {
      "calls_so_far": len(oidx),
      "context_chars_so_far": sum(len(o) for o in obs),
      "n_obs_so_far": len(obs),
      "largest_obs_so_far": sizes[-1],
      "dup_line_ratio_prefix": dup/max(len(all_lines),1),
      "task_id": tid,
    }

def candidate_segment(msgs):
    """the most recent large observation = the candidate for this decision."""
    oidx=obs_indices(msgs)
    best=None;bsz=0
    for i in oidx:
        sz=len(PM._txt(msgs[i].get("content")))
        if sz>=bsz: bsz=sz; best=i
    return best, bsz

def randomize(tid, call_idx):
    key=(tid,call_idx,SEED)
    r=random.Random(hash(key)&0xffffffff).random()
    cum=0
    for a,p in PROBS:
        cum+=p
        if r<cum: return a, p
    return PROBS[-1][0], PROBS[-1][1]

def call_plugboard(body, timeout=900):
    with tempfile.NamedTemporaryFile("wb",suffix=".json",delete=False) as f: f.write(body); bf=f.name
    try:
        for a in range(6):
            cmd=["curl","-sS","--noproxy","*","--cert",CERT,"--key",CERT,"-X","POST",PB_URL,
                 "-H","content-type: application/json","-H","anthropic-version: 2023-06-01","--max-time",str(timeout),"-d","@"+bf]
            p=subprocess.run(cmd,capture_output=True)
            if p.returncode==0 and p.stdout:
                try:
                    j=json.loads(p.stdout)
                    if "error" not in j: return p.stdout
                except: pass
            time.sleep(min(2**a,30))
        return p.stdout
    finally:
        try: os.unlink(bf)
        except: pass

def transform(raw):
    meta={"action":"NO_OP","propensity":1.0,"eligible":False,"seg_idx":None,"seg_chars":0,"chars_removed":0}
    try: d=json.loads(raw)
    except: return raw, meta
    msgs=d.get("messages")
    if not isinstance(msgs,list): return raw, meta
    tid=task_of(msgs)
    with _lock: ci=_callcount.get(tid,0); _callcount[tid]=ci+1
    meta["call_index"]=ci
    meta["prefix_features"]=prefix_features(msgs,tid)
    seg_idx,seg_sz=candidate_segment(msgs)
    meta["seg_idx"]=seg_idx; meta["seg_chars"]=seg_sz
    # eligibility: candidate segment big enough
    if seg_sz>=MIN_SEGMENT_CHARS and seg_idx is not None:
        meta["eligible"]=True
        action,prop=randomize(tid,ci)
        meta["action"]=action; meta["propensity"]=prop
        if action!="NO_OP":
            before=PM._txt(msgs[seg_idx].get("content"))
            after=before
            if action=="LINEDEDUP_seg":
                pruned=PM.line_level_dedup(msgs)
                after=PM._txt(pruned[seg_idx].get("content")) if seg_idx<len(pruned) else before
                d["messages"]=pruned
            elif action=="GENTLE_CAP_seg":
                pruned=PM.cap_all_obs(msgs,6000)
                after=PM._txt(pruned[seg_idx].get("content")) if seg_idx<len(pruned) else before
                d["messages"]=pruned
            meta["chars_removed"]=len(before)-len(after)
            meta["original_segment_sha"]=hashlib.sha256(before.encode()).hexdigest()[:12]
    # tool normalize
    tools=d.get("tools")
    if isinstance(tools,list):
        for t in tools:
            if isinstance(t,dict) and t.get("type")=="custom" and "input_schema" in t: del t["type"]
    if "temperature" in d and "top_p" in d: del d["top_p"]
    return json.dumps(d).encode(), meta

class H(http.server.BaseHTTPRequestHandler):
    protocol_version="HTTP/1.1"
    def log_message(self,*a): pass
    def do_POST(self):
        n=int(self.headers.get('Content-Length',0)); raw=self.rfile.read(n); t0=time.time()
        body,meta=transform(raw); out=call_plugboard(body); dt=time.time()-t0
        try:
            d=json.loads(out); u=d.get('usage',{})
            pf=meta.get("prefix_features") or {}
            rec={"task_id":pf.get("task_id","UNK"),"call_index":meta.get("call_index"),
                 "action":meta["action"],"propensity":meta["propensity"],"eligible":meta["eligible"],
                 "seg_chars":meta["seg_chars"],"chars_removed":meta["chars_removed"],
                 "prefix_features":pf,
                 "input_tokens":u.get('input_tokens'),"cache_read_tokens":u.get('cache_read_input_tokens'),
                 "cache_creation_tokens":u.get('cache_creation_input_tokens'),"output_tokens":u.get('output_tokens'),
                 "latency":round(dt,2),"timestamp":t0,"stop":d.get('stop_reason')}
            with _lock, open(EVENTLOG,'a') as lg: lg.write(json.dumps(rec)+"\n")
        except Exception as e:
            with _lock, open(EVENTLOG+'.err','a') as lg: lg.write(str(e)[:200]+"\n")
        self.send_response(200); self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(out))); self.end_headers(); self.wfile.write(out)
    def do_GET(self):
        self.send_response(200); self.send_header('Content-Length','2'); self.end_headers(); self.wfile.write(b'ok')
class TS(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address=True; daemon_threads=True
if __name__=="__main__":
    os.makedirs(os.path.dirname(EVENTLOG),exist_ok=True)
    print(f"MRT shim on 127.0.0.1:{PORT} seed={SEED} probs={PROBS}",flush=True)
    TS(("127.0.0.1",PORT),H).serve_forever()
