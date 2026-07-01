#!/usr/bin/env python3
"""Protocol-conformant MRT rescue shim. Single-shot, segment-local, newest-observation-only.
Fixes: targets newest obs (not largest), one intervention per task, segment-local dedup (not whole-history),
50/50 randomization, preserves prior prefix byte-for-byte."""
import os, sys, json, time, tempfile, subprocess, http.server, socketserver, threading, hashlib, copy

PORT = int(os.environ.get("MRT_RESCUE_PORT", "8910"))
EVENTLOG = os.environ.get("MRT_RESCUE_EVENTLOG", "/data/users/dengcchi/prune_ab/results/pruning_ab/mrt_rescue/events.jsonl")
SEED = int(os.environ.get("MRT_RESCUE_SEED", "20260701"))
PB_URL = "https://plugboard.x2p.facebook.net/v1/messages"
CERT = os.environ.get("PB_CERT", "/var/facebook/credentials/dengcchi/x509/dengcchi.pem")
FP_INDEX = json.load(open("/data/users/dengcchi/prune_ab/task_fingerprints.json")) if os.path.exists("/data/users/dengcchi/prune_ab/task_fingerprints.json") else {}

# protocol constants
MIN_SEGMENT_CHARS = 2000
MIN_DUP_LINES = 5
MIN_DUP_FRACTION = 0.40
MIN_LINE_LEN = 12

_lock = threading.Lock()
_task_state = {}  # task_id -> {"intervened": bool, "event_id": str, "assignment": str}
_call_count = {}  # task_id -> int

SHIM_SHA256 = None  # set at startup

def _compute_shim_hash():
    return hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16]

def _txt(content):
    if isinstance(content, str): return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict):
                if "text" in b: parts.append(b["text"])
                elif b.get("type") == "tool_result":
                    inner = b.get("content")
                    if isinstance(inner, str): parts.append(inner)
                    elif isinstance(inner, list):
                        parts.append("".join(x.get("text","") for x in inner if isinstance(x,dict)))
        return "".join(parts)
    return str(content) if content else ""

def _is_obs(i, m, n):
    if m.get("role") != "user": return False
    if i <= 1: return False
    c = m.get("content")
    if isinstance(c, list):
        # match tool_result blocks OR plain text blocks (SWE-agent sends both formats)
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c):
            return True
        if any(isinstance(b, dict) and b.get("type") == "text" for b in c):
            return True
    return isinstance(c, str)

def _obs_indices(messages):
    n = len(messages)
    return [i for i, m in enumerate(messages) if _is_obs(i, m, n)]

def _eligible_lines(text):
    return [l.strip() for l in text.split("\n") if len(l.strip()) >= MIN_LINE_LEN]

def _task_of(msgs):
    for m in msgs:
        if m.get("role") == "user":
            t = m.get("content")
            if isinstance(t, list): t = " ".join(x.get("text", "") for x in t if isinstance(x, dict))
            elif not isinstance(t, str): t = str(t)
            fp = hashlib.sha256(t[:2000].encode()).hexdigest()[:16]
            return FP_INDEX.get(fp, f"UNK_{fp}")
    return "NO_USER"

def _randomize(task_id, event_id):
    key = f"{task_id}|{event_id}|{SEED}".encode()
    digest = hashlib.sha256(key).digest()
    u = int.from_bytes(digest[:8], "big") / 2**64
    assignment = "LINEDEDUP" if u < 0.5 else "NO_OP"
    return assignment, u

def apply_line_dedup_to_segment(messages, seg_idx):
    """Segment-local LINEDEDUP. Only removes lines from messages[seg_idx] that appear in PRIOR observations."""
    obs_idx = _obs_indices(messages)
    prior_obs = [i for i in obs_idx if i < seg_idx]
    # build prior line set
    prior_lines = set()
    for pi in prior_obs:
        for l in _eligible_lines(_txt(messages[pi].get("content"))):
            prior_lines.add(l)
    # examine target segment
    target_text = _txt(messages[seg_idx].get("content"))
    target_lines = target_text.split("\n")
    kept = []; removed = 0
    for line in target_lines:
        stripped = line.strip()
        if len(stripped) >= MIN_LINE_LEN and stripped in prior_lines:
            removed += 1
        else:
            kept.append(line)
    if removed > 0:
        kept.append(f"[{removed} duplicate lines elided]")
    new_text = "\n".join(kept)
    # apply to messages (deep copy of target only)
    out = [m for m in messages]  # shallow copy list
    out[seg_idx] = copy.deepcopy(messages[seg_idx])
    # set the new text
    c = out[seg_idx].get("content")
    if isinstance(c, list):
        for b in c:
            if isinstance(b, dict) and b.get("type") == "tool_result":
                inner = b.get("content")
                if isinstance(inner, list):
                    b["content"] = [{"type": "text", "text": new_text}]
                else:
                    b["content"] = new_text
                break
    else:
        out[seg_idx]["content"] = new_text
    chars_removed = len(target_text) - len(new_text)
    changed_indices = [seg_idx] if removed > 0 else []
    return out, {"actual_changed": removed > 0, "characters_removed": chars_removed,
                 "lines_removed": removed, "changed_message_indices": changed_indices}

def _verify_prefix(original, transformed, seg_idx):
    """Assert all messages before seg_idx are byte-identical."""
    for i in range(seg_idx):
        if json.dumps(original[i], sort_keys=True) != json.dumps(transformed[i], sort_keys=True):
            return False
    return True

def call_plugboard(body, timeout=900):
    with tempfile.NamedTemporaryFile("wb", suffix=".json", delete=False) as f:
        f.write(body); bf = f.name
    try:
        for a in range(6):
            cmd = ["curl", "-sS", "--noproxy", "*", "--cert", CERT, "--key", CERT, "-X", "POST", PB_URL,
                   "-H", "content-type: application/json", "-H", "anthropic-version: 2023-06-01",
                   "--max-time", str(timeout), "-d", "@" + bf]
            p = subprocess.run(cmd, capture_output=True)
            if p.returncode == 0 and p.stdout:
                try:
                    j = json.loads(p.stdout)
                    if "error" not in j: return p.stdout
                except: pass
            time.sleep(min(2**a, 30))
        return p.stdout
    finally:
        try: os.unlink(bf)
        except: pass

def process_request(raw_body):
    """Core logic: eligibility check, randomize, transform, call PlugBoard, log."""
    try: d = json.loads(raw_body)
    except: return raw_body, {}
    msgs = d.get("messages")
    if not isinstance(msgs, list): return raw_body, {}
    # GATE: skip internal SWE-agent calls that lack full history (no observations possible)
    if len(msgs) <= 2:
        # These are setup/internal calls — pass through without logging or processing
        body_out = json.dumps(d).encode() if isinstance(d, dict) else raw_body
        return body_out, None  # None signals: do not log this event
    # ONE-TIME DEBUG: dump message structure for the first real call
    import os as _os
    if not _os.path.exists('/tmp/rescue_msgs_debug.json'):
        import json as _j
        _j.dump({"n_msgs": len(msgs), "roles": [m.get("role") for m in msgs[:15]],
                 "content_types": [(type(m.get("content")).__name__) for m in msgs[:15]],
                 "msg2_sample": str(msgs[2].get("content"))[:200] if len(msgs)>2 else None},
                open('/tmp/rescue_msgs_debug.json','w'), indent=1)
    
    tid = _task_of(msgs)
    with _lock:
        ci = _call_count.get(tid, 0); _call_count[tid] = ci + 1
    event_id = f"{tid}#call{ci}"
    
    # DEBUG: always write last msg info
    open("/tmp/rescue_debug.txt","w").write(f"{len(msgs)} msgs, obs_count={len(_obs_indices(msgs))}, roles={[m.get(chr(114)+chr(111)+chr(108)+chr(101)) for m in msgs[:8]]}")
    # find newest observation
    obs_idx = _obs_indices(msgs)
    seg_idx = obs_idx[-1] if obs_idx else None
    
    rec = {"task_id": tid, "repo": tid.split("__")[0] if "__" in tid else "",
           "call_index": ci, "event_id": event_id,
           "experimental_event": False, "already_intervened": False,
           "eligible": False, "assignment": "NO_OP", "propensity": 1.0,
           "seed": SEED, "random_u": None,
           "segment_index": seg_idx, "segment_hash": None,
           "segment_chars": 0, "eligible_line_count": 0,
           "duplicate_line_count": 0, "duplicate_line_fraction": 0.0,
           "actual_changed": False, "characters_removed": 0,
           "changed_message_indices": [], "prior_prefix_identical": True,
           "shim_sha256": SHIM_SHA256}
    
    if seg_idx is None:
        return json.dumps(d).encode(), rec
    
    # compute eligibility on newest observation
    seg_text = _txt(msgs[seg_idx].get("content"))
    rec["segment_chars"] = len(seg_text)
    rec["segment_hash"] = hashlib.sha256(seg_text[:2000].encode()).hexdigest()[:12]
    
    if len(seg_text) < MIN_SEGMENT_CHARS:
        return json.dumps(d).encode(), rec
    
    # compute duplicate lines vs prior
    prior_obs = [i for i in obs_idx if i < seg_idx]
    prior_lines = set()
    for pi in prior_obs:
        for l in _eligible_lines(_txt(msgs[pi].get("content"))):
            prior_lines.add(l)
    
    seg_eligible = _eligible_lines(seg_text)
    rec["eligible_line_count"] = len(seg_eligible)
    dup_count = sum(1 for l in seg_eligible if l in prior_lines)
    rec["duplicate_line_count"] = dup_count
    dup_frac = dup_count / max(len(seg_eligible), 1)
    rec["duplicate_line_fraction"] = round(dup_frac, 4)
    
    # eligibility gate
    eligible = (len(seg_text) >= MIN_SEGMENT_CHARS and
                dup_count >= MIN_DUP_LINES and
                dup_frac > MIN_DUP_FRACTION)
    rec["eligible"] = eligible
    
    # check task state
    with _lock:
        state = _task_state.setdefault(tid, {"intervened": False, "event_id": None, "assignment": None})
    
    if state["intervened"]:
        rec["already_intervened"] = True
        return json.dumps(d).encode(), rec
    
    if not eligible:
        return json.dumps(d).encode(), rec
    
    # === EXPERIMENTAL EVENT ===
    assignment, u = _randomize(tid, event_id)
    rec["experimental_event"] = True
    rec["assignment"] = assignment
    rec["propensity"] = 0.5
    rec["random_u"] = round(u, 10)
    
    # mark task as intervened
    with _lock:
        _task_state[tid] = {"intervened": True, "event_id": event_id, "assignment": assignment}
    
    if assignment == "LINEDEDUP":
        transformed, meta = apply_line_dedup_to_segment(msgs, seg_idx)
        prefix_ok = _verify_prefix(msgs, transformed, seg_idx)
        rec["actual_changed"] = meta["actual_changed"]
        rec["characters_removed"] = meta["characters_removed"]
        rec["changed_message_indices"] = meta["changed_message_indices"]
        rec["prior_prefix_identical"] = prefix_ok
        if not prefix_ok:
            # ABORT: prefix mutation detected — do not transform
            return json.dumps(d).encode(), rec
        d["messages"] = transformed
    else:
        # NO_OP: messages unchanged
        rec["actual_changed"] = False
        rec["characters_removed"] = 0
        rec["changed_message_indices"] = []
        rec["prior_prefix_identical"] = True
    
    # tool normalize (standard fixes)
    tools = d.get("tools")
    if isinstance(tools, list):
        for t in tools:
            if isinstance(t, dict) and t.get("type") == "custom" and "input_schema" in t:
                del t["type"]
    if "temperature" in d and "top_p" in d:
        del d["top_p"]
    
    return json.dumps(d).encode(), rec

class H(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0))
        raw = self.rfile.read(n)
        t0 = time.time()
        body, rec = process_request(raw)
        out = call_plugboard(body)
        dt = time.time() - t0
        # parse response for usage
        try:
            resp = json.loads(out); u = resp.get("usage", {})
            rec["input_tokens"] = u.get("input_tokens")
            rec["cache_read_tokens"] = u.get("cache_read_input_tokens")
            rec["cache_creation_tokens"] = u.get("cache_creation_input_tokens")
            rec["output_tokens"] = u.get("output_tokens")
            rec["latency_seconds"] = round(dt, 2)
            rec["stop_reason"] = resp.get("stop_reason")
            rec["timestamp"] = t0
            # compute H=1 effective cost
            ir = rec["input_tokens"] or 0; cr = rec["cache_read_tokens"] or 0
            cc = rec["cache_creation_tokens"] or 0; op = rec["output_tokens"] or 0
            rec["effective_cost_h1"] = ir + 0.1*cr + 1.25*cc + 5*op
        except: pass
        # write event log (skip if rec is None = internal call)
        if rec is None:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)
            return
        with _lock:
            os.makedirs(os.path.dirname(EVENTLOG), exist_ok=True)
            with open(EVENTLOG, "a") as f: f.write(json.dumps(rec) + "\n")
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(out)))
        self.end_headers()
        self.wfile.write(out)
    def do_GET(self):
        self.send_response(200); self.send_header('Content-Length', '2')
        self.end_headers(); self.wfile.write(b'ok')

class TS(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True; daemon_threads = True

if __name__ == "__main__":
    SHIM_SHA256 = _compute_shim_hash()
    os.makedirs(os.path.dirname(EVENTLOG), exist_ok=True)
    print(f"MRT RESCUE shim on 127.0.0.1:{PORT} seed={SEED} sha={SHIM_SHA256}", flush=True)
    TS(("127.0.0.1", PORT), H).serve_forever()
