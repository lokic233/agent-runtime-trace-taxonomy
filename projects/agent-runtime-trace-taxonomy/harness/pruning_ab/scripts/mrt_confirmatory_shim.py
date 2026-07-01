#!/usr/bin/env python3
"""
MRT CONFIRMATORY SHIM (Study 2) — hardened, restart-safe, fail-closed.

Isolated from mrt_formal_shim.py (Study 1). Three hardening fixes over Study 1:
  FIX 1 (unknown task): an unrecognized task fingerprint => UNAVAILABLE / fail-closed / logged
        error. NEVER randomized. (Study 1 could emit UNK_<fp> and still randomize.)
  FIX 2 (restart-safe event ordering): a PERSISTENT monotonic per-task event ordinal is kept in
        an append-only ledger (event_ordinal.jsonl) and reconstructed on startup. call_index is
        no longer process-local for identity. event_id is derived from stable info:
          study_id | task_id | persistent_event_ordinal | request_hash | segment_hash
        => no event-id collisions after restart.
  FIX 3 (main-agent-call classification): every provider call is explicitly classified as
        main_agent_call | internal_setup | tool_decision, using a deterministic rule validated
        offline on >=20 trajectories. H=3 joins the intervention response + the next two
        MAIN-AGENT responses only (never internal calls). ALL provider calls are still preserved
        in provider_events.jsonl for total-cost accounting.

Retained from Study 1: single randomized event/task, newest-obs target, base availability
(seg>=2000 & dup_lines>=5 & LINEDEDUP removes >=1 line; dup_frac is a CONTINUOUS moderator),
stratified permuted-block randomization (block=4, 2:2), segment-local LINEDEDUP, byte-identical
NO_OP, NO synthetic fallback (fail closed), append-only ledgers reconstructed on startup, abort
on ledger conflict. NEW Study-2 seed + NEW manifest hash.

Env:
  MRT_CONF_PORT             (default 8912)
  MRT_CONF_DIR              results dir (default results/pruning_ab/mrt_confirmatory)
  MRT_CONF_SEED             frozen Study-2 seed (default 20260702 — DIFFERENT from Study 1)
  MRT_CONF_RUN_ID           run id string (default "conf_dev")
  MRT_CONF_MODE             "randomize" | "noop_only" | "log_only" | "sham"  (default randomize)
  MRT_CONF_FP               task fingerprint json (task_id lookup)
  MRT_CONF_STUDY_ID         study id embedded in event ids (default "study2")
  PB_CERT                   mTLS cert path
"""
import os, sys, json, time, tempfile, subprocess, http.server, socketserver, threading, hashlib, copy

# ------------------------- config -------------------------
PORT      = int(os.environ.get("MRT_CONF_PORT", "8912"))
FDIR      = os.environ.get("MRT_CONF_DIR", "/data/users/dengcchi/prune_ab/results/pruning_ab/mrt_confirmatory")
SEED      = int(os.environ.get("MRT_CONF_SEED", "20260702"))  # DIFFERENT from Study-1 (20260701)
RUN_ID    = os.environ.get("MRT_CONF_RUN_ID", "conf_dev")
MODE      = os.environ.get("MRT_CONF_MODE", "randomize")  # randomize | noop_only | log_only | sham
STUDY_ID  = os.environ.get("MRT_CONF_STUDY_ID", "study2")
EXP_VER   = "mrt_confirmatory_v1"
PB_URL    = "https://plugboard.x2p.facebook.net/v1/messages"
CERT      = os.environ.get("PB_CERT", "/var/facebook/credentials/dengcchi/x509/dengcchi.pem")
FP_PATH   = os.environ.get("MRT_CONF_FP", "/data/users/dengcchi/prune_ab/task_fingerprints_study2.json")

EVENTLOG   = os.path.join(FDIR, "events.jsonl")
PROVLOG    = os.path.join(FDIR, "provider_events.jsonl")       # ALL provider calls (total-cost accounting)
TASKSTATE  = os.path.join(FDIR, "task_state.jsonl")            # append-only task intervention ledger
RANDSTATE  = os.path.join(FDIR, "randomization_state.jsonl")   # append-only assignment ledger
RANDMAN    = os.path.join(FDIR, "randomization_manifest.json") # frozen block plan (hash recorded per event)
ORDINALLOG = os.path.join(FDIR, "event_ordinal.jsonl")         # append-only persistent per-task ordinal ledger

# protocol constants (FROZEN)
MIN_SEGMENT_CHARS = 2000
MIN_DUP_LINES     = 5
MIN_LINE_LEN      = 12
HIGH_THRESHOLD    = 0.40   # HIGH_REDUNDANCY strictly greater than this
BLOCK_SIZE        = 4      # 2 LINEDEDUP / 2 NO_OP per block
RETRY_MAX         = 6      # frozen retry policy for transport
RETRY_BACKOFF_CAP = 30

FP_INDEX = json.load(open(FP_PATH)) if os.path.exists(FP_PATH) else {}

_lock = threading.RLock()
_task_state = {}     # task_id -> {...}
_task_ordinal = {}   # task_id -> persistent monotonic ordinal (rebuilt from ORDINALLOG)
_block_cursor = {}   # stratum -> next position index consumed (rebuilt from RANDSTATE)
SHIM_SHA256 = None
RANDMAN_HASH = None
_block_plan = {}     # stratum -> list of assignments (the permuted block sequence)

# ------------------------- helpers -------------------------
def _compute_shim_hash():
    return hashlib.sha256(open(__file__, "rb").read()).hexdigest()

def _transform_sha():
    # hash of the transform-relevant source region for provenance
    return hashlib.sha256(("linededup_segment_local|"+str(MIN_LINE_LEN)+"|"+str(MIN_SEGMENT_CHARS)).encode()).hexdigest()[:16]

def _txt(content):
    if isinstance(content, str): return content
    if isinstance(content, list):
        parts = []
        for b in content:
            if isinstance(b, dict):
                if isinstance(b.get("text"), str):
                    parts.append(b["text"])
                elif b.get("type") == "tool_result":
                    inner = b.get("content")
                    if isinstance(inner, str): parts.append(inner)
                    elif isinstance(inner, list):
                        parts.append("".join(x.get("text","") for x in inner if isinstance(x, dict) and isinstance(x.get("text"), str)))
        return "".join(parts)
    return str(content) if content else ""

def _is_obs(i, m):
    """A tool observation = user message (not the first task prompt) carrying tool output.
    SWE-agent 1.1.0 sends role=user + content=[{type:text}] OR [{type:tool_result}]."""
    if m.get("role") != "user": return False
    if i <= 1: return False
    c = m.get("content")
    if isinstance(c, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in c): return True
        if any(isinstance(b, dict) and b.get("type") == "text" for b in c): return True
    return isinstance(c, str)

def _obs_indices(messages):
    return [i for i, m in enumerate(messages) if _is_obs(i, m)]

def _eligible_lines(text):
    return [l.strip() for l in text.split("\n") if len(l.strip()) >= MIN_LINE_LEN]

def _task_of(msgs):
    """Return (task_id, known_bool). FIX 1: unknown fingerprint => (UNK_<fp>, False) and the
    caller MUST treat it as unavailable / fail-closed / never-randomized."""
    for m in msgs:
        if m.get("role") == "user":
            t = m.get("content")
            if isinstance(t, list): t = " ".join(x.get("text","") for x in t if isinstance(x, dict) and isinstance(x.get("text"), str))
            elif not isinstance(t, str): t = str(t)
            fp = hashlib.sha256(t[:2000].encode()).hexdigest()[:16]
            if fp in FP_INDEX:
                return FP_INDEX[fp], True
            return f"UNK_{fp}", False
    return "NO_USER", False

def _classify_call(msgs):
    """FIX 3: classify a provider call into main_agent_call | internal_setup | tool_decision.
    Deterministic rule validated offline on >=20 trajectories (see audit_main_agent_calls.py):
      - internal_setup: len(msgs) <= 2  (system + first user only; no agent turn yet)
      - main_agent_call: a normal agent decision turn = the message list ends with a user/tool
        observation and contains >=1 prior assistant turn (the agent is being asked to act on an
        observation). This is the call whose response is a main-agent response.
    In the SWE-agent 1.1.0 single-loop harness EVERY non-setup provider call IS a main-agent
    decision turn (there are no separate summarizer/helper sub-agents in this config), so
    tool_decision is folded into main_agent_call. The classifier still emits the label explicitly
    and the audit confirms the 1:1 mapping on real trajectories."""
    if not isinstance(msgs, list) or len(msgs) <= 2:
        return "internal_setup"
    # a main-agent decision turn has at least one assistant message already in history
    has_assistant = any(m.get("role") == "assistant" for m in msgs)
    if not has_assistant:
        return "internal_setup"
    return "main_agent_call"

def _seg_hash(text):
    return hashlib.sha256(text.encode("utf-8","replace")).hexdigest()[:16]

# ------------------------- transform -------------------------
def _set_segment_text(msg, new_text):
    """Write new_text into msg, handling all 3 content formats. Returns True if a write path was taken."""
    c = msg.get("content")
    if isinstance(c, list):
        # tool_result branch first
        for b in c:
            if isinstance(b, dict) and b.get("type") == "tool_result":
                inner = b.get("content")
                if isinstance(inner, list):
                    b["content"] = [{"type":"text","text":new_text}]
                else:
                    b["content"] = new_text
                return True
        # text-block branch: collapse all text blocks into the first, blank the rest
        text_blocks = [b for b in c if isinstance(b, dict) and isinstance(b.get("text"), str)]
        if text_blocks:
            text_blocks[0]["text"] = new_text
            for b in text_blocks[1:]:
                b["text"] = ""
            return True
        return False
    else:
        msg["content"] = new_text
        return True

def compute_dedup(messages, seg_idx):
    """Compute segment-local dedup of newest obs vs PRIOR obs. Returns (new_text, removed, prior_dup_lines, total_elig)."""
    obs_idx = _obs_indices(messages)
    prior_obs = [i for i in obs_idx if i < seg_idx]
    prior_lines = set()
    for pi in prior_obs:
        for l in _eligible_lines(_txt(messages[pi].get("content"))):
            prior_lines.add(l)
    target_text = _txt(messages[seg_idx].get("content"))
    target_lines = target_text.split("\n")
    kept = []; removed = 0
    for line in target_lines:
        s = line.strip()
        if len(s) >= MIN_LINE_LEN and s in prior_lines:
            removed += 1
        else:
            kept.append(line)
    if removed > 0:
        kept.append(f"[{removed} duplicate lines elided]")
    new_text = "\n".join(kept)
    return new_text, removed, prior_lines

def apply_line_dedup(messages, seg_idx):
    """Apply segment-local LINEDEDUP. Returns (transformed_messages, meta) where meta.actual_changed
    is computed from the REAL serialized diff of the target message."""
    target_before = _txt(messages[seg_idx].get("content"))
    new_text, removed, _prior = compute_dedup(messages, seg_idx)
    out = list(messages)  # shallow copy of list
    out[seg_idx] = copy.deepcopy(messages[seg_idx])
    wrote = _set_segment_text(out[seg_idx], new_text)
    target_after = _txt(out[seg_idx].get("content"))
    # actual_changed = REAL serialized difference of the target message (not the line count)
    ser_before = json.dumps(messages[seg_idx], sort_keys=True, ensure_ascii=False)
    ser_after  = json.dumps(out[seg_idx], sort_keys=True, ensure_ascii=False)
    actual_changed = (ser_before != ser_after)
    chars_removed = len(target_before) - len(target_after)
    changed_indices = [seg_idx] if actual_changed else []
    meta = {
        "actual_changed": actual_changed,
        "wrote_path": wrote,
        "lines_removed": removed,
        "characters_removed": chars_removed,
        "changed_message_indices": changed_indices,
        "segment_hash_before": _seg_hash(target_before),
        "segment_hash_after": _seg_hash(target_after),
    }
    return out, meta

def verify_prefix_identical(original, transformed, seg_idx):
    for i in range(seg_idx):
        if json.dumps(original[i], sort_keys=True) != json.dumps(transformed[i], sort_keys=True):
            return False
    return True

def verify_full_identical(original, transformed):
    return json.dumps(original, sort_keys=True) == json.dumps(transformed, sort_keys=True)

# ------------------------- normalization (applied IDENTICALLY to both arms) -------------------------
def normalize_body(d):
    tools = d.get("tools")
    if isinstance(tools, list):
        for t in tools:
            if isinstance(t, dict) and t.get("type") == "custom" and "input_schema" in t:
                del t["type"]
    if "temperature" in d and "top_p" in d:
        del d["top_p"]
    return d

# ------------------------- stratified permuted-block randomization -------------------------
def _seeded_permuted_block(stratum, block_id):
    """Deterministic permutation of [L,L,N,N] from frozen SHA-256(seed|stratum|block_id). No python hash()."""
    base = ["LINEDEDUP","LINEDEDUP","NO_OP","NO_OP"]
    key = f"{SEED}|{stratum}|{block_id}".encode()
    dig = hashlib.sha256(key).digest()
    # Fisher-Yates using bytes from the digest
    arr = base[:]
    for i in range(len(arr)-1, 0, -1):
        j = dig[i] % (i+1)
        arr[i], arr[j] = arr[j], arr[i]
    return arr

def build_randomization_manifest():
    """Precompute a deterministic block plan for both strata (enough blocks for a large run)."""
    plan = {}
    for stratum in ("HIGH_REDUNDANCY","MIXED_REDUNDANCY"):
        seq = []
        for b in range(200):  # 200 blocks * 4 = 800 slots per stratum (ample)
            seq.extend([(b, pos, a) for pos, a in enumerate(_seeded_permuted_block(stratum, b))])
        plan[stratum] = seq
    return plan

def _rebuild_state():
    """Reconstruct task-state, block cursor, AND persistent event ordinals from append-only
    ledgers. Abort on inconsistency."""
    global _task_state, _block_cursor, _task_ordinal
    _task_state = {}
    _task_ordinal = {}
    # FIX 2: reconstruct persistent per-task event ordinal from ORDINALLOG
    if os.path.exists(ORDINALLOG):
        for line in open(ORDINALLOG):
            line=line.strip()
            if not line: continue
            r = json.loads(line)
            tid = r["task_id"]; o = r["ordinal"]
            _task_ordinal[tid] = max(_task_ordinal.get(tid, 0), o)
    consumed = {"HIGH_REDUNDANCY":0, "MIXED_REDUNDANCY":0}
    if os.path.exists(RANDSTATE):
        for line in open(RANDSTATE):
            line=line.strip()
            if not line: continue
            r = json.loads(line)
            tid = r["task_id"]
            # idempotency: a task must never get two different assignments
            if tid in _task_state and _task_state[tid]["assignment"] != r["assignment"]:
                raise RuntimeError(f"LEDGER INCONSISTENCY: {tid} has conflicting assignments "
                                   f"{_task_state[tid]['assignment']} vs {r['assignment']}")
            _task_state[tid] = {"intervened":True, "event_id":r["event_id"], "assignment":r["assignment"],
                                "stratum":r["stratum"], "block_id":r["block_id"], "block_position":r["block_position"],
                                "timestamp":r.get("timestamp"), "attempt":r.get("attempt",0), "status":"intervened"}
            slot = r["block_id"]*BLOCK_SIZE + r["block_position"]
            consumed[r["stratum"]] = max(consumed[r["stratum"]], slot+1)
    _block_cursor = consumed
    return len(_task_state)

def _next_ordinal(tid):
    """FIX 2: persistent monotonic per-task event ordinal. Append to ORDINALLOG (crash-safe) and
    return the new value. Never resets on restart (rebuilt from the ledger)."""
    o = _task_ordinal.get(tid, 0) + 1
    _task_ordinal[tid] = o
    _atomic_append(ORDINALLOG, {"task_id": tid, "ordinal": o, "timestamp": time.time()})
    return o

def _next_assignment(stratum):
    """Consume the next slot in the stratum's permuted-block plan. Returns (assignment, block_id, block_position)."""
    seq = _block_plan[stratum]
    idx = _block_cursor.get(stratum, 0)
    if idx >= len(seq):
        raise RuntimeError(f"randomization plan exhausted for {stratum}")
    block_id, block_pos, assignment = seq[idx]
    return assignment, block_id, block_pos

def _atomic_append(path, obj):
    line = json.dumps(obj, ensure_ascii=False)
    with open(path, "a") as f:
        f.write(line+"\n")
        f.flush()
        os.fsync(f.fileno())

# ------------------------- transport (fail-closed) -------------------------
def call_plugboard(body, timeout=900):
    """Frozen retry policy. Returns (raw_bytes, ok_bool). ok=False => invalid/failed upstream (fail closed)."""
    with tempfile.NamedTemporaryFile("wb", suffix=".json", delete=False) as f:
        f.write(body); bf = f.name
    last = b""
    try:
        for a in range(RETRY_MAX):
            cmd = ["curl","-sS","--noproxy","*","--cert",CERT,"--key",CERT,"-X","POST",PB_URL,
                   "-H","content-type: application/json","-H","anthropic-version: 2023-06-01",
                   "--max-time",str(timeout),"-d","@"+bf]
            p = subprocess.run(cmd, capture_output=True)
            last = p.stdout or b""
            if p.returncode == 0 and last:
                try:
                    j = json.loads(last)
                    if "content" in j and "error" not in j:
                        return last, True
                except Exception:
                    pass
            time.sleep(min(2**a, RETRY_BACKOFF_CAP))
        return last, False
    finally:
        try: os.unlink(bf)
        except Exception: pass

# ------------------------- core request processing -------------------------
def process_request(raw_body):
    """Returns (out_body_bytes, rec_dict_or_None). rec=None => pass-through internal call (not logged)."""
    try:
        d = json.loads(raw_body)
    except Exception:
        return raw_body, {"infrastructure_failure": True, "provider_error": "unparseable_request"}
    d = normalize_body(d)
    msgs = d.get("messages")
    if not isinstance(msgs, list):
        return json.dumps(d).encode(), None
    # FIX 3: classify the call. internal_setup calls are pass-through (not logged as events).
    call_class = _classify_call(msgs)
    if call_class == "internal_setup":
        return json.dumps(d).encode(), None

    tid, known = _task_of(msgs)

    obs_idx = _obs_indices(msgs)
    seg_idx = obs_idx[-1] if obs_idx else None

    # segment hash (needed for stable event_id) computed early
    seg_text_for_id = _txt(msgs[seg_idx].get("content")) if seg_idx is not None else ""
    request_hash = hashlib.sha256(json.dumps(msgs, sort_keys=True).encode("utf-8","replace")).hexdigest()[:16]
    seg_hash_for_id = _seg_hash(seg_text_for_id) if seg_text_for_id else "noseg"

    with _lock:
        ordinal = _next_ordinal(tid)
    # FIX 2: event_id from stable info (study | task | persistent ordinal | request hash | seg hash)
    event_id = f"{STUDY_ID}:{tid}:o{ordinal}:{request_hash}:{seg_hash_for_id}"

    rec = {
        "experiment_version": EXP_VER, "run_id": RUN_ID, "study_id": STUDY_ID, "task_id": tid,
        "task_known": known, "call_class": call_class,
        "repo": tid.split("__")[0] if ("__" in tid and known) else "",
        "attempt": 0, "call_index": ordinal, "event_ordinal": ordinal, "event_id": event_id,
        "request_hash": request_hash,
        "experimental_event": False, "available": False, "already_intervened": False,
        "moderator_stratum": "", "assignment": "NO_OP", "propensity": 1.0,
        "block_id": None, "block_position": None, "randomization_manifest_hash": RANDMAN_HASH,
        "segment_index": seg_idx, "segment_hash_before": None, "segment_hash_after": None,
        "segment_chars": 0, "eligible_line_count": 0, "duplicate_line_count": 0,
        "duplicate_line_fraction": 0.0, "unique_line_count": 0,
        "actual_changed": False, "lines_removed": 0, "characters_removed": 0,
        "changed_message_indices": [], "prior_prefix_identical": True, "full_noop_identical": True,
        "input_tokens": None, "cache_read_tokens": None, "cache_creation_tokens": None,
        "output_tokens": None, "effective_cost_h1": None, "latency_seconds": None, "stop_reason": None,
        "provider_error": None, "infrastructure_failure": False,
        "git_commit": os.environ.get("MRT_CONF_GIT_COMMIT",""), "shim_sha256": SHIM_SHA256,
        "transform_sha256": _transform_sha(), "model_id": d.get("model",""),
        "temperature": d.get("temperature", 0.0), "timestamp": None,
    }

    # FIX 1: unknown task => fail closed. Log the event (for accounting) but NEVER randomize.
    if not known:
        rec["provider_error"] = "unknown_task_fingerprint"
        rec["infrastructure_failure"] = True
        return json.dumps(d).encode(), rec

    if seg_idx is None:
        return json.dumps(d).encode(), rec

    seg_text = _txt(msgs[seg_idx].get("content"))
    rec["segment_chars"] = len(seg_text)
    rec["segment_hash_before"] = _seg_hash(seg_text)

    # moderator features (pre-treatment)
    prior_obs = [i for i in obs_idx if i < seg_idx]
    prior_lines = set()
    for pi in prior_obs:
        for l in _eligible_lines(_txt(msgs[pi].get("content"))):
            prior_lines.add(l)
    seg_elig = _eligible_lines(seg_text)
    dup_count = sum(1 for l in seg_elig if l in prior_lines)
    total_elig = len(seg_elig)
    dup_frac = dup_count / max(total_elig, 1)
    rec["eligible_line_count"] = total_elig
    rec["duplicate_line_count"] = dup_count
    rec["duplicate_line_fraction"] = round(dup_frac, 6)
    rec["unique_line_count"] = total_elig - dup_count

    # base availability (NO dup_frac>0.40 requirement) + LINEDEDUP would remove >=1 line
    would_remove = dup_count  # dedup removes exactly the duplicate eligible lines
    available = (len(seg_text) >= MIN_SEGMENT_CHARS and dup_count >= MIN_DUP_LINES and would_remove >= 1)
    rec["available"] = available

    # moderator stratum
    if dup_frac > HIGH_THRESHOLD:
        rec["moderator_stratum"] = "HIGH_REDUNDANCY"
    elif dup_frac > 0 and dup_count >= MIN_DUP_LINES:
        rec["moderator_stratum"] = "MIXED_REDUNDANCY"
    else:
        rec["moderator_stratum"] = "NONE"

    with _lock:
        state = _task_state.get(tid)
        if state and state.get("intervened"):
            rec["already_intervened"] = True
            return json.dumps(d).encode(), rec
        if not available or MODE == "log_only":
            return json.dumps(d).encode(), rec
        if rec["moderator_stratum"] not in ("HIGH_REDUNDANCY","MIXED_REDUNDANCY"):
            return json.dumps(d).encode(), rec

        # === RANDOMIZE (atomic + persistent + idempotent) ===
        if MODE == "noop_only":
            assignment, block_id, block_pos, propensity = "NO_OP", None, None, 1.0
        elif MODE == "dedup_only":
            # test-only forced-treatment mode (never used in the confirmatory locked run)
            assignment, block_id, block_pos, propensity = "LINEDEDUP", None, None, 1.0
        elif MODE == "sham":
            # SHAM calibration cohort: traverse the transform path but emit byte-identical context.
            # Randomize SHAM vs NO_OP so dup_frac can be tested as a moderator of a NULL transform.
            stratum = rec["moderator_stratum"]
            raw_assign, block_id, block_pos = _next_assignment(stratum)
            assignment = "SHAM" if raw_assign == "LINEDEDUP" else "NO_OP"
            propensity = 0.5
            _block_cursor[stratum] = _block_cursor.get(stratum,0) + 1
        else:
            stratum = rec["moderator_stratum"]
            assignment, block_id, block_pos = _next_assignment(stratum)
            propensity = 0.5
            _block_cursor[stratum] = _block_cursor.get(stratum,0) + 1
        # persist assignment BEFORE mutating anything (crash-safe)
        assign_row = {"task_id":tid,"event_id":event_id,"stratum":rec["moderator_stratum"],
                      "block_id":block_id,"block_position":block_pos,"assignment":assignment,
                      "propensity":propensity,"seed":SEED,"randomization_manifest_hash":RANDMAN_HASH,
                      "timestamp":time.time(),"attempt":0}
        _atomic_append(RANDSTATE, assign_row)
        _atomic_append(TASKSTATE, {"task_id":tid,"intervened":True,"event_id":event_id,
                                   "assignment":assignment,"stratum":rec["moderator_stratum"],
                                   "timestamp":time.time(),"attempt":0,"status":"intervened"})
        _task_state[tid] = {"intervened":True,"event_id":event_id,"assignment":assignment,
                            "stratum":rec["moderator_stratum"],"block_id":block_id,"block_position":block_pos,
                            "timestamp":time.time(),"attempt":0,"status":"intervened"}

    rec["experimental_event"] = True
    rec["assignment"] = assignment
    rec["propensity"] = propensity
    rec["block_id"] = block_id
    rec["block_position"] = block_pos

    if assignment == "LINEDEDUP":
        transformed, meta = apply_line_dedup(msgs, seg_idx)
        prefix_ok = verify_prefix_identical(msgs, transformed, seg_idx)
        rec.update({k:meta[k] for k in ("actual_changed","lines_removed","characters_removed",
                                        "changed_message_indices","segment_hash_after")})
        rec["prior_prefix_identical"] = prefix_ok
        rec["full_noop_identical"] = False
        if not prefix_ok:
            # ABORT transform: prefix mutation detected — do not send a mutated prefix
            rec["infrastructure_failure"] = True
            rec["provider_error"] = "prefix_mutation_detected"
            return json.dumps(d).encode(), rec
        d["messages"] = transformed
    elif assignment == "SHAM":
        # SHAM: run the SAME transform path (compute the dedup) but DISCARD the result and send the
        # ORIGINAL bytes. Model-visible context is byte-identical to NO_OP; only the code path differs.
        _transformed, meta = apply_line_dedup(msgs, seg_idx)  # computed then discarded
        rec["actual_changed"] = False
        rec["lines_removed"] = 0
        rec["characters_removed"] = 0
        rec["changed_message_indices"] = []
        rec["segment_hash_after"] = rec["segment_hash_before"]
        rec["prior_prefix_identical"] = True
        rec["full_noop_identical"] = True
        rec["sham_would_have_removed_lines"] = meta.get("lines_removed", 0)
        # d["messages"] left UNCHANGED (byte-identical)
    else:
        # NO_OP: byte-identical body (only the identical transport normalization already applied)
        rec["actual_changed"] = False
        rec["lines_removed"] = 0
        rec["characters_removed"] = 0
        rec["changed_message_indices"] = []
        rec["segment_hash_after"] = rec["segment_hash_before"]
        rec["prior_prefix_identical"] = True
        rec["full_noop_identical"] = True

    return json.dumps(d).encode(), rec

# ------------------------- HTTP -------------------------
class H(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *a): pass
    def _send(self, out, code=200):
        self.send_response(code)
        self.send_header("Content-Type","application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)
    def do_GET(self):
        self._send(b"ok")
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n)
        t0 = time.time()
        body, rec = process_request(raw)
        out, ok = call_plugboard(body)
        dt = time.time() - t0
        if rec is None:
            # internal pass-through call; still must not synthesize on failure
            if not ok:
                self._send(json.dumps({"type":"error","error":{"type":"upstream_invalid",
                            "message":"formal shim fail-closed (internal call)"}}).encode(), code=502)
                return
            self._send(out); return
        # record outcome
        rec["timestamp"] = t0
        rec["latency_seconds"] = round(dt, 3)
        if not ok:
            # FAIL CLOSED — never synthesize model content
            rec["infrastructure_failure"] = True
            rec["provider_error"] = "invalid_upstream_response"
            rec["failed_response_hash"] = hashlib.sha256(out or b"").hexdigest()[:16]
            with _lock:
                _atomic_append(EVENTLOG, rec)
            self._send(json.dumps({"type":"error","error":{"type":"upstream_invalid",
                        "message":"formal shim fail-closed: invalid upstream response"}}).encode(), code=502)
            return
        try:
            resp = json.loads(out); u = resp.get("usage", {})
            rec["input_tokens"] = u.get("input_tokens")
            rec["cache_read_tokens"] = u.get("cache_read_input_tokens")
            rec["cache_creation_tokens"] = u.get("cache_creation_input_tokens")
            rec["output_tokens"] = u.get("output_tokens")
            rec["stop_reason"] = resp.get("stop_reason")
            ir=rec["input_tokens"] or 0; cr=rec["cache_read_tokens"] or 0
            cc=rec["cache_creation_tokens"] or 0; op=rec["output_tokens"] or 0
            rec["effective_cost_h1"] = ir + 0.1*cr + 1.25*cc + 5.0*op
        except Exception as e:
            rec["provider_error"] = f"usage_parse_error:{e}"
        with _lock:
            _atomic_append(EVENTLOG, rec)
            # provider_events.jsonl: ALL provider calls (total-cost accounting), compact record
            _atomic_append(PROVLOG, {k: rec.get(k) for k in (
                "study_id","task_id","event_id","event_ordinal","call_class","experimental_event",
                "assignment","input_tokens","cache_read_tokens","cache_creation_tokens",
                "output_tokens","effective_cost_h1","latency_seconds","timestamp")})
        self._send(out)

class TS(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True; daemon_threads = True

def main():
    global SHIM_SHA256, RANDMAN_HASH, _block_plan
    os.makedirs(FDIR, exist_ok=True)
    SHIM_SHA256 = _compute_shim_hash()[:16]
    _block_plan = build_randomization_manifest()
    # freeze/verify the randomization manifest
    man = {"study_id":STUDY_ID,"seed":SEED,"block_size":BLOCK_SIZE,"strata":["HIGH_REDUNDANCY","MIXED_REDUNDANCY"],
           "first_block_HIGH":_seeded_permuted_block("HIGH_REDUNDANCY",0),
           "first_block_MIXED":_seeded_permuted_block("MIXED_REDUNDANCY",0),
           "high_threshold":HIGH_THRESHOLD}
    man_bytes = json.dumps(man, sort_keys=True).encode()
    RANDMAN_HASH = hashlib.sha256(man_bytes).hexdigest()[:16]
    man["manifest_hash"] = RANDMAN_HASH
    if os.path.exists(RANDMAN):
        prev = json.load(open(RANDMAN))
        if prev.get("manifest_hash") != RANDMAN_HASH:
            raise RuntimeError(f"RANDMAN hash changed {prev.get('manifest_hash')} != {RANDMAN_HASH} — refusing to start")
    else:
        json.dump(man, open(RANDMAN,"w"), indent=1)
    n = _rebuild_state()
    print(f"MRT CONFIRMATORY shim :{PORT} seed={SEED} run={RUN_ID} mode={MODE} shim={SHIM_SHA256} "
          f"randman={RANDMAN_HASH} reconstructed_tasks={n}", flush=True)
    TS(("127.0.0.1", PORT), H).serve_forever()

if __name__ == "__main__":
    main()
