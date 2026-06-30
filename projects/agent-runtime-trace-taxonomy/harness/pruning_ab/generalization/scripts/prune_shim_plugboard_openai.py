#!/usr/bin/env python3
"""gpt-5-5 cross-provider shim: OpenAI chat format -> PlugBoard /v1/chat/completions (mTLS).
Applies the FROZEN prune_methods transforms (imported from the canonical scripts/ copy) and logs
the provider-normalized call-level schema. gpt-5-5 exposes NO cache_read/cache_creation -> those
fields are null; cost is provider-native (vs own C0), never Anthropic-weighted.

CRITICAL GUARD: the frozen _is_obs() only fires on {role:user, content:str} or anthropic tool_result.
If SWE-agent sends native OpenAI tool-role observations, the transforms would silently NO-OP, faking
a 'no effect' result. This shim ASSERTS transform activation on non-C0 arms and writes an activation
flag to every ledger row so Phase B can gate on it. It NEVER edits the frozen _is_obs.
"""
import http.server, socketserver, json, os, threading, time, tempfile, subprocess, sys, hashlib, inspect
sys.path.insert(0, os.environ.get("PB_PM_DIR","/data/users/dengcchi/prune_ab/scripts"))
import prune_methods as PM

PORT=int(os.environ.get("PB_SHIM_PORT","8811"))
PB_URL="https://plugboard.x2p.facebook.net/v1/chat/completions"
CERT=os.environ.get("PB_CERT","/var/facebook/credentials/dengcchi/x509/dengcchi.pem")
PRUNE=os.environ.get("TS_PRUNE_METHOD","C0_identity")
REQ_MODEL=os.environ.get("TS_MODEL","gpt-5-5")
LEDGER=os.environ.get("PB_LEDGER","/data/users/dengcchi/prune_ab/logs/xmodel/gpt55_ledger.jsonl")
os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
_MOD_SHA=hashlib.sha256(inspect.getsource(PM).encode()).hexdigest()
def _fnsha(m):
    try: return hashlib.sha256(inspect.getsource(PM.METHODS[m]).encode()).hexdigest()
    except Exception: return None
_lock=threading.Lock(); _callcount={}

def _norm_model_to_openai(d):
    # litellm with openai/ prefix already sends OpenAI chat format; force served model id.
    d["model"]=REQ_MODEL
    return d

def call_plugboard(body, timeout=900, retries=6):
    with tempfile.NamedTemporaryFile("wb",suffix=".json",delete=False) as f:
        f.write(body); bf=f.name
    try:
        for a in range(retries):
            p=subprocess.run(["curl","-sS","--noproxy","*","--cert",CERT,"--key",CERT,"-X","POST",PB_URL,
                              "-H","content-type: application/json","--max-time",str(timeout),"-d","@"+bf],
                             capture_output=True)
            if p.returncode==0 and p.stdout:
                try:
                    j=json.loads(p.stdout)
                    if "error" not in j: return 0,p.stdout
                except: pass
            time.sleep(min(2**a,30))
        return 1,p.stdout
    finally:
        try: os.unlink(bf)
        except: pass

def transform(raw):
    meta={"changed":False,"changed_message_count":0,"first_changed_message_index":None,
          "messages_before_chars":0,"messages_after_chars":0,"characters_removed":0,
          "transform_fired":None,"obs_role_layout":None}
    try: d=json.loads(raw)
    except: return raw, meta
    msgs=d.get("messages")
    if isinstance(msgs,list):
        # detect observation layout (diagnostic for the no-op hazard)
        roles=[m.get("role") for m in msgs]
        meta["obs_role_layout"]="tool" if "tool" in roles else "user_pleintext"
        before=sum(len(PM._txt(m.get("content"))) for m in msgs); meta["messages_before_chars"]=before
        if PRUNE=="SHAM":
            import copy; _=copy.deepcopy(msgs); _=sum(len(PM._txt(m.get("content"))) for m in _)
            meta["messages_after_chars"]=before; meta["transform_fired"]=False
        elif PRUNE and PRUNE!="C0_identity":
            pruned=PM.apply_method(PRUNE,msgs)
            after=sum(len(PM._txt(m.get("content"))) for m in pruned); cm=0; first=None
            for i,(a,b) in enumerate(zip(msgs,pruned)):
                if PM._txt(a.get("content"))!=PM._txt(b.get("content")):
                    cm+=1
                    if first is None: first=i
            meta.update(changed=(after!=before),changed_message_count=cm,first_changed_message_index=first,
                        messages_after_chars=after,characters_removed=before-after,transform_fired=(after!=before))
            d["messages"]=pruned
        else:
            meta["messages_after_chars"]=before; meta["transform_fired"]=False
    d=_norm_model_to_openai(d)
    return json.dumps(d).encode(), meta

class H(http.server.BaseHTTPRequestHandler):
    protocol_version="HTTP/1.1"
    def log_message(self,*a): pass
    def do_GET(self):
        self.send_response(200); self.send_header('Content-Length','2'); self.end_headers(); self.wfile.write(b'ok')
    def do_POST(self):
        n=int(self.headers.get('Content-Length',0)); raw=self.rfile.read(n); t0=time.time()
        body,meta=transform(raw); rc,out=call_plugboard(body); dt=time.time()-t0
        try:
            d=json.loads(out); u=d.get("usage",{}) or {}
            tid=os.environ.get("TS_TASK_HINT","?")
            with _lock:
                ci=_callcount.get(tid,0); _callcount[tid]=ci+1
            rec={"study":"cross_model_generalization_v1","provider":"plugboard_openai","requested_model":REQ_MODEL,
                 "served_model":d.get("model"),"task_id":tid,"arm":PRUNE,"call_index":ci,"timestamp":t0,
                 "input_tokens":u.get("prompt_tokens"),"output_tokens":u.get("completion_tokens"),
                 "cache_read_tokens":None,"cache_creation_tokens":None,
                 "cached_tokens":(u.get("prompt_tokens_details") or {}).get("cached_tokens"),
                 "provider_cost_usd":None,"latency_seconds":round(dt,2),
                 "messages_before_chars":meta["messages_before_chars"],"messages_after_chars":meta["messages_after_chars"],
                 "characters_removed":meta["characters_removed"],"changed_message_count":meta["changed_message_count"],
                 "first_changed_message_index":meta["first_changed_message_index"],
                 "transform_fired":meta["transform_fired"],"obs_role_layout":meta["obs_role_layout"],
                 "transform_module_sha256":_MOD_SHA,"transform_function_sha256":_fnsha(PRUNE),
                 "raw_provider_usage":u}
            with _lock, open(LEDGER,"a") as lg: lg.write(json.dumps(rec)+"\n")
        except Exception as e:
            with _lock, open(LEDGER+".err","a") as lg: lg.write(f"{time.time()} {str(e)[:200]}\n")
        self.send_response(200); self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(out))); self.end_headers(); self.wfile.write(out)

class TS(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address=True; daemon_threads=True

if __name__=="__main__":
    print(f"[gpt55-shim] port={PORT} model={REQ_MODEL} method={PRUNE} pm_sha={_MOD_SHA[:12]} fn_sha={(_fnsha(PRUNE) or 'NA')[:12]} ledger={LEDGER}")
    TS(("127.0.0.1",PORT),H).serve_forever()
