#!/usr/bin/env python3
"""Localhost Anthropic-Messages shim -> PlugBoard via proven curl path (mTLS + fwdproxy)."""
import http.server, socketserver, json, subprocess, os, threading, time, tempfile, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prune_methods as PM
PRUNE_METHOD=os.environ.get("TS_PRUNE_METHOD","C0_identity")
CAPTURE_ONE=os.environ.get("TS_CAPTURE_BODY")  # path to dump first body, for inspection
PORT=int(os.environ.get("PB_SHIM_PORT","8731"))
CERT=os.environ.get("PB_CERT","/var/facebook/credentials/dengcchi/x509/dengcchi.pem")
PB_URL="https://plugboard.x2p.facebook.net/v1/messages"
LEDGER=os.environ.get("PB_LEDGER", "/data/users/dengcchi/hal_work/artifacts/pb_token_ledger.jsonl")
_lock=threading.Lock()
def call_plugboard(body_bytes, timeout=900, max_retries=6):
    with tempfile.NamedTemporaryFile('wb',suffix='.json',delete=False) as f:
        f.write(body_bytes); bodyf=f.name
    try:
        last_out=b""; last_err=b""
        for attempt in range(max_retries):
            # x2p endpoints are DIRECTLY reachable; routing via fwdproxy returns 403 after CONNECT.
            # Connect direct, and explicitly bypass any inherited proxy with --noproxy '*'.
            cmd=["curl","-sS","--noproxy","*","--cert",CERT,"--key",CERT,PB_URL,
                 "-H","Content-Type: application/json","-H","anthropic-version: 2023-06-01",
                 "--max-time",str(timeout),"-d","@"+bodyf]
            try:
                p=subprocess.run(cmd,capture_output=True,timeout=timeout+30)
            except subprocess.TimeoutExpired:
                last_err=b"curl timeout"; time.sleep(1.5*(attempt+1)); continue
            out,err=p.stdout,p.stderr; last_out,last_err=out,err
            try:
                d=json.loads(out)
                if isinstance(d,dict) and ("content" in d or d.get("type")=="error"):
                    return 0, out, err
            except Exception: pass
            time.sleep(1.0*(attempt+1))
        msg=(last_out[:300] or last_err[:300] or b"proxy_exhausted").decode("utf-8","replace")
        synth=json.dumps({"type":"error","error":{"type":"api_error",
            "message":f"plugboard shim: {max_retries} retries exhausted: {msg}"}}).encode()
        return 0, synth, last_err
    finally:
        try: os.unlink(bodyf)
        except: pass
def normalize_body(raw):
    """Rewrite litellm's Anthropic body into the classic format PlugBoard (anthropic-version 2023-06-01) accepts.
    Fix: tools sent as {name,input_schema,type:'custom',description} -> strip type:'custom' (PlugBoard then
    reads top-level input_schema). Leaves native/server tool types (text_editor_*, bash_2024*, etc.) untouched."""
    try:
        d=json.loads(raw)
    except Exception:
        return raw
    changed=False
    # capture the body with the MOST messages (a mid/late trajectory call)
    if CAPTURE_ONE:
        try:
            nm=len(d.get("messages",[]))
            import os.path
            prevn=0
            if os.path.exists(CAPTURE_ONE+".n"):
                prevn=int(open(CAPTURE_ONE+".n").read() or 0)
            if nm>prevn:
                open(CAPTURE_ONE,"w").write(json.dumps(d))
                open(CAPTURE_ONE+".n","w").write(str(nm))
        except Exception: pass
    # PRUNE: apply the configured method to the messages array (the wire history)
    msgs=d.get("messages")
    if isinstance(msgs,list) and PRUNE_METHOD and PRUNE_METHOD!="C0_identity":
        try:
            before=sum(len(PM._txt(m.get("content"))) for m in msgs)
            d["messages"]=PM.apply_method(PRUNE_METHOD, msgs)
            after=sum(len(PM._txt(m.get("content"))) for m in d["messages"])
            if after!=before: changed=True
        except Exception: pass
    tools=d.get("tools")
    if isinstance(tools,list):
        for t in tools:
            if isinstance(t,dict) and t.get("type")=="custom" and "input_schema" in t:
                del t["type"]; changed=True
    # Fix: claude-opus-4-6 rejects requests with BOTH temperature and top_p
    # ("`temperature` and `top_p` cannot both be specified"). Drop top_p, keep
    # temperature (explicitly set to 0.0 by run_model_full.sh).
    if "temperature" in d and "top_p" in d:
        del d["top_p"]; changed=True
    if changed:
        return json.dumps(d).encode()
    return raw

class H(http.server.BaseHTTPRequestHandler):
    protocol_version="HTTP/1.1"
    def log_message(self,*a): pass
    def do_POST(self):
        n=int(self.headers.get('Content-Length',0)); raw=self.rfile.read(n)
        tag=self.headers.get('X-TS-Tag',''); t0=time.time()
        raw=normalize_body(raw)
        rc,out,err=call_plugboard(raw); dt=time.time()-t0
        try:
            d=json.loads(out); u=d.get('usage',{})
            with _lock, open(LEDGER,'a') as lg:
                lg.write(json.dumps({"ts":t0,"dt":round(dt,2),"tag":tag,"served":d.get('model'),"prune":PRUNE_METHOD,
                    "input":u.get('input_tokens'),"output":u.get('output_tokens'),
                    "cache_read":u.get('cache_read_input_tokens'),"cache_creation":u.get('cache_creation_input_tokens'),
                    "stop":d.get('stop_reason')})+"\n")
        except Exception: pass
        self.send_response(200); self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(out))); self.end_headers(); self.wfile.write(out)
    def do_GET(self):
        self.send_response(200); self.send_header('Content-Length','2'); self.end_headers(); self.wfile.write(b'ok')
class TS(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address=True; daemon_threads=True
if __name__=="__main__":
    print(f"shim on 127.0.0.1:{PORT} -> {PB_URL} ledger={LEDGER}",flush=True)
    TS(("127.0.0.1",PORT),H).serve_forever()
