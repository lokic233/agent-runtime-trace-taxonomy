#!/usr/bin/env python3
"""Minimal passthrough shim for the Study-2 eligibility DRY RUN. Normalizes tools for PlugBoard
(strips type:custom, drops top_p when temperature present), forwards to PlugBoard with a frozen
retry policy, and NEVER randomizes or transforms. Fail-closed (502) on invalid upstream; never
synthesizes content. Its only purpose is to generate real trajectories for OFFLINE eligibility
analysis on NEW tasks. Env: MRT_DRY_PORT (default 8913)."""
import os, json, time, tempfile, subprocess, http.server, socketserver
PORT=int(os.environ.get("MRT_DRY_PORT","8913"))
PB_URL="https://plugboard.x2p.facebook.net/v1/messages"
CERT=os.environ.get("PB_CERT","/var/facebook/credentials/dengcchi/x509/dengcchi.pem")

def normalize(d):
    tools=d.get("tools")
    if isinstance(tools,list):
        for t in tools:
            if isinstance(t,dict) and t.get("type")=="custom" and "input_schema" in t: del t["type"]
    if "temperature" in d and "top_p" in d: del d["top_p"]
    return d

def call_pb(body,timeout=900):
    with tempfile.NamedTemporaryFile("wb",suffix=".json",delete=False) as f:
        f.write(body); bf=f.name
    try:
        last=b""
        for a in range(6):
            p=subprocess.run(["curl","-sS","--noproxy","*","--cert",CERT,"--key",CERT,"-X","POST",PB_URL,
                "-H","content-type: application/json","-H","anthropic-version: 2023-06-01",
                "--max-time",str(timeout),"-d","@"+bf],capture_output=True)
            last=p.stdout
            if p.returncode==0 and last:
                try:
                    j=json.loads(last)
                    if "content" in j and "error" not in j: return last,True
                except Exception: pass
            time.sleep(min(2**a,30))
        return last,False
    finally:
        try: os.unlink(bf)
        except Exception: pass

class H(http.server.BaseHTTPRequestHandler):
    protocol_version="HTTP/1.1"
    def log_message(self,*a): pass
    def _send(self,out,code=200):
        self.send_response(code); self.send_header("Content-Type","application/json")
        self.send_header("Content-Length",str(len(out))); self.end_headers(); self.wfile.write(out)
    def do_GET(self): self._send(b"ok")
    def do_POST(self):
        n=int(self.headers.get("Content-Length",0)); raw=self.rfile.read(n)
        try: d=normalize(json.loads(raw)); body=json.dumps(d).encode()
        except Exception: body=raw
        out,ok=call_pb(body)
        if not ok:
            self._send(json.dumps({"type":"error","error":{"type":"upstream_invalid","message":"dry-run shim fail-closed"}}).encode(),code=502); return
        self._send(out)

class TS(socketserver.ThreadingMixIn,socketserver.TCPServer):
    allow_reuse_address=True; daemon_threads=True

if __name__=="__main__":
    print(f"DRY-RUN passthrough shim :{PORT}",flush=True)
    TS(("127.0.0.1",PORT),H).serve_forever()
