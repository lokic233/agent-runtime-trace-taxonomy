#!/usr/bin/env python3
"""OpenAI-format pruning shim -> local vLLM. Applies TS_PRUNE_METHOD to messages, forwards to vLLM."""
import http.server, socketserver, json, os, threading, time, sys, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prune_methods as PM
PORT=int(os.environ.get("PB_SHIM_PORT","8801"))
UPSTREAM=os.environ.get("TS_UPSTREAM","http://127.0.0.1:8001/v1/chat/completions")
PRUNE=os.environ.get("TS_PRUNE_METHOD","C0_identity")
LEDGER=os.environ.get("PB_LEDGER","/data/users/dengcchi/prune_ab/logs/qwen_ledger.jsonl")
_lock=threading.Lock()
class H(http.server.BaseHTTPRequestHandler):
    protocol_version="HTTP/1.1"
    def log_message(self,*a): pass
    def do_GET(self):
        self.send_response(200); self.send_header('Content-Length','2'); self.end_headers(); self.wfile.write(b'ok')
    def do_POST(self):
        n=int(self.headers.get('Content-Length',0)); raw=self.rfile.read(n); t0=time.time()
        try:
            d=json.loads(raw); msgs=d.get("messages")
            if isinstance(msgs,list) and PRUNE!="C0_identity":
                d["messages"]=PM.apply_method(PRUNE,msgs); raw=json.dumps(d).encode()
        except Exception: pass
        # forward to vLLM (OpenAI). No proxy (localhost).
        req=urllib.request.Request(UPSTREAM, data=raw, headers={"Content-Type":"application/json","Authorization":"Bearer x"})
        try:
            with urllib.request.urlopen(req, timeout=900) as r: out=r.read()
        except Exception as e:
            out=json.dumps({"error":{"message":f"shim upstream: {e}"}}).encode()
        try:
            rd=json.loads(out); u=rd.get("usage",{})
            with _lock, open(LEDGER,"a") as lg:
                lg.write(json.dumps({"ts":t0,"prune":PRUNE,"input":u.get("prompt_tokens"),"output":u.get("completion_tokens")})+"\n")
        except Exception: pass
        self.send_response(200); self.send_header('Content-Type','application/json')
        self.send_header('Content-Length',str(len(out))); self.end_headers(); self.wfile.write(out)
class TS(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address=True; daemon_threads=True
if __name__=="__main__":
    print(f"openai-prune-shim :{PORT} -> {UPSTREAM} prune={PRUNE}",flush=True)
    TS(("127.0.0.1",PORT),H).serve_forever()
