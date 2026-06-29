#!/usr/bin/env python3
"""Instrumented shim v2: task-tagged + full Phase-2 ledger + SHAM mode.
SHAM (TS_PRUNE_METHOD=SHAM): runs the IDENTICAL code path (deepcopy, token count, normalize)
but returns byte-identical messages — isolates code-path effects from pruning effects."""
import os, sys, json, time, tempfile, subprocess, http.server, socketserver, threading, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prune_methods as PM

PORT=int(os.environ.get("PB_SHIM_PORT","8751"))
LEDGER=os.environ.get("PB_LEDGER","/data/users/dengcchi/prune_ab/logs/ledger_v2.jsonl")
PRUNE_METHOD=os.environ.get("TS_PRUNE_METHOD","C0_identity")
PB_URL="https://plugboard.x2p.facebook.net/v1/messages"
CERT=os.environ.get("PB_CERT","/var/facebook/credentials/dengcchi/x509/dengcchi.pem")
FP_INDEX=json.load(open("/data/users/dengcchi/prune_ab/task_fingerprints.json")) if os.path.exists("/data/users/dengcchi/prune_ab/task_fingerprints.json") else {}
_lock=threading.Lock()
_callcount={}  # task_id -> running call index

def fingerprint_task(msgs):
    for m in msgs:
        if m.get("role")=="user":
            t=m.get("content")
            if isinstance(t,list): t=" ".join(x.get("text","") for x in t if isinstance(x,dict))
            elif not isinstance(t,str): t=str(t)
            fp=hashlib.sha256(t[:2000].encode()).hexdigest()[:16]
            return FP_INDEX.get(fp, f"UNKNOWN_{fp}")
    return "NO_USER_MSG"

def call_plugboard(body_bytes, timeout=900, max_retries=6):
    with tempfile.NamedTemporaryFile("wb",suffix=".json",delete=False) as f:
        f.write(body_bytes); bodyf=f.name
    try:
        for attempt in range(max_retries):
            cmd=["curl","-sS","--noproxy","*","--cert",CERT,"--key",CERT,"-X","POST",PB_URL,
                 "-H","content-type: application/json","-H","anthropic-version: 2023-06-01",
                 "--max-time",str(timeout),"-d","@"+bodyf]
            p=subprocess.run(cmd,capture_output=True)
            if p.returncode==0 and p.stdout:
                try:
                    j=json.loads(p.stdout)
                    if "error" not in j: return 0,p.stdout,b""
                except: pass
            time.sleep(min(2**attempt,30))
        return 1,p.stdout,p.stderr
    finally:
        try: os.unlink(bodyf)
        except: pass

def transform(raw):
    """Returns (out_bytes, meta). meta has all Phase-2 activation fields."""
    meta={"changed":False,"changed_message_count":0,"first_changed_message_index":None,
          "messages_before_chars":0,"messages_after_chars":0,"characters_removed":0,"task_id":None}
    try: d=json.loads(raw)
    except: return raw, meta
    msgs=d.get("messages")
    if isinstance(msgs,list):
        meta["task_id"]=fingerprint_task(msgs)
        before_chars=sum(len(PM._txt(m.get("content"))) for m in msgs)
        meta["messages_before_chars"]=before_chars
        # SHAM: run code path but DO NOT mutate (deepcopy + recount only)
        if PRUNE_METHOD=="SHAM":
            import copy
            _=copy.deepcopy(msgs); _=sum(len(PM._txt(m.get("content"))) for m in _)  # identical work
            meta["messages_after_chars"]=before_chars
        elif PRUNE_METHOD and PRUNE_METHOD not in ("C0_identity","C0_A","C0_B","C0_C"):
            try:
                pruned=PM.apply_method(PRUNE_METHOD, msgs)
                after_chars=sum(len(PM._txt(m.get("content"))) for m in pruned)
                # count changed messages
                cm=0; first=None
                for i,(a,b) in enumerate(zip(msgs,pruned)):
                    if PM._txt(a.get("content"))!=PM._txt(b.get("content")):
                        cm+=1
                        if first is None: first=i
                meta.update(changed=(after_chars!=before_chars),changed_message_count=cm,
                            first_changed_message_index=first,messages_after_chars=after_chars,
                            characters_removed=before_chars-after_chars)
                d["messages"]=pruned
            except Exception as e:
                meta["error"]=str(e)[:100]; meta["messages_after_chars"]=before_chars
        else:
            meta["messages_after_chars"]=before_chars
    # tool normalize + top_p fix (unchanged)
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
        body,meta=transform(raw)
        rc,out,err=call_plugboard(body); dt=time.time()-t0
        try:
            d=json.loads(out); u=d.get('usage',{})
            tid=meta.get("task_id","?")
            with _lock:
                ci=_callcount.get(tid,0); _callcount[tid]=ci+1
            rec={"task_id":tid,"method":PRUNE_METHOD,"call_index":ci,
                 "request_id":d.get("id"),
                 "messages_before_tokens":meta["messages_before_chars"]//4,  # ~4 chars/token est
                 "messages_after_tokens":meta["messages_after_chars"]//4,
                 "characters_removed":meta["characters_removed"],
                 "tokens_removed_estimate":meta["characters_removed"]//4,
                 "changed":meta["changed"],"changed_message_count":meta["changed_message_count"],
                 "first_changed_message_index":meta["first_changed_message_index"],
                 "input_tokens":u.get('input_tokens'),"cache_read_tokens":u.get('cache_read_input_tokens'),
                 "cache_creation_tokens":u.get('cache_creation_input_tokens'),"output_tokens":u.get('output_tokens'),
                 "latency_seconds":round(dt,2),"timestamp":t0,"stop":d.get('stop_reason')}
            with _lock, open(LEDGER,'a') as lg: lg.write(json.dumps(rec)+"\n")
        except Exception: pass
        self.send_response(200); self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(out))); self.end_headers(); self.wfile.write(out)
    def do_GET(self):
        self.send_response(200); self.send_header('Content-Length','2'); self.end_headers(); self.wfile.write(b'ok')
class TS(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address=True; daemon_threads=True
if __name__=="__main__":
    print(f"shim_v2 on 127.0.0.1:{PORT} method={PRUNE_METHOD} ledger={LEDGER}",flush=True)
    TS(("127.0.0.1",PORT),H).serve_forever()
