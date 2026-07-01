#!/usr/bin/env python3
"""Synthetic protocol tests for the MRT rescue shim. ALL must pass before paid runs."""
import sys, json, copy, hashlib
sys.path.insert(0, "/data/users/dengcchi/prune_ab/scripts")
import mrt_rescue_shim as shim

def make_obs(text):
    return {"role":"user","content":[{"type":"tool_result","tool_use_id":"t0","content":[{"type":"text","text":text}]}]}
def make_action():
    return {"role":"assistant","content":[{"type":"text","text":"s"},{"type":"tool_use","id":"t0","name":"bash","input":{"command":"x"}}]}
def make_msgs(obs_texts):
    msgs = [{"role":"system","content":"sys"},{"role":"user","content":"TASK: fix bug in repo"}]
    for t in obs_texts:
        msgs.append(make_action()); msgs.append(make_obs(t))
    return msgs

# reset state between tests
def reset():
    shim._task_state.clear(); shim._call_count.clear()
    shim.SEED = 20260701; shim.SHIM_SHA256 = "test"
    shim.FP_INDEX = {}

# --- Test 1: Ineligible event (short newest obs) ---
def test_ineligible():
    reset()
    msgs = make_msgs(["short obs here"])
    body = json.dumps({"model":"test","max_tokens":10,"messages":msgs}).encode()
    out_body, rec = shim.process_request(body)
    assert not rec["experimental_event"], "should not randomize ineligible"
    assert not rec["actual_changed"], "should not change"
    assert rec["assignment"] == "NO_OP"
    # messages unchanged
    d = json.loads(out_body)
    assert json.dumps(d["messages"]) == json.dumps(msgs)
    print("  [PASS] test_ineligible")

# --- Test 2: Eligible LINEDEDUP assignment ---
def test_eligible_linededup():
    reset()
    # prior obs with known lines
    prior = "\n".join([f"duplicate line number {i} here padding with extra words to make it longer enough for the threshold to pass definitely" for i in range(50)])
    # newest obs: >40% are exact dups of prior
    newest = "\n".join([f"duplicate line number {i} here padding with extra words to make it longer enough for the threshold to pass definitely" for i in range(30)] + 
                       [f"unique new line {i} with extra content to make the segment reach two thousand characters minimum threshold" for i in range(10)])
    msgs = make_msgs([prior, newest])
    body = json.dumps({"model":"test","max_tokens":10,"messages":msgs}).encode()
    reset(); shim.SEED = 4  # pre-verified: gives LINEDEDUP for this content
    out_body, rec = shim.process_request(body)
    assert rec["experimental_event"], "should be experimental"
    assert rec["assignment"] == "LINEDEDUP"
    assert rec["propensity"] == 0.5
    # only newest obs changed
    d = json.loads(out_body)
    assert rec["changed_message_indices"] == [5] or rec["actual_changed"]  # seg_idx=5 (sys+user+act+obs+act+obs)
    # prior prefix byte-identical
    assert rec["prior_prefix_identical"]
    # verify prior messages unchanged
    orig_msgs = make_msgs([prior, newest])
    seg = rec["segment_index"]
    for i in range(seg):
        assert json.dumps(d["messages"][i], sort_keys=True) == json.dumps(orig_msgs[i], sort_keys=True), f"msg {i} changed!"
    print(f"  [PASS] test_eligible_linededup (seed=4, removed={rec['characters_removed']}c)")

# --- Test 3: Eligible NO_OP assignment ---
def test_eligible_noop():
    reset()
    prior = "\n".join([f"duplicate line number {i} here padding with extra words to make it longer enough for the threshold to pass definitely" for i in range(50)])
    newest = "\n".join([f"duplicate line number {i} here padding with extra words to make it longer enough for the threshold to pass definitely" for i in range(30)] + 
                       [f"unique new line {i} with extra content to make the segment reach two thousand characters minimum threshold" for i in range(10)])
    msgs = make_msgs([prior, newest])
    reset(); shim.SEED = 0  # pre-verified: gives NO_OP for this content
    body = json.dumps({"model":"test","max_tokens":10,"messages":msgs}).encode()
    out_body, rec = shim.process_request(body)
    assert rec["experimental_event"]
    assert rec["assignment"] == "NO_OP"
    assert not rec["actual_changed"]
    assert rec["characters_removed"] == 0
    # ALL messages byte-identical
    d = json.loads(out_body)
    orig = make_msgs([prior, newest])
    for i in range(len(orig)):
        assert json.dumps(d["messages"][i], sort_keys=True) == json.dumps(orig[i], sort_keys=True), f"msg {i} changed on NO_OP!"
    print(f"  [PASS] test_eligible_noop (seed=0)")

# --- Test 4: Single intervention per task ---
def test_single_intervention():
    reset()
    prior = "\n".join([f"duplicate line number {i} here padding with extra words to make it longer enough for the threshold to pass definitely" for i in range(50)])
    newest1 = "\n".join([f"duplicate line number {i} here padding with extra words to make it longer enough for the threshold to pass definitely" for i in range(30)] + ["unique1 "*20])
    newest2 = "\n".join([f"duplicate line number {i} here padding with extra words to make it longer enough for the threshold to pass definitely" for i in range(30)] + ["unique2 "*20])
    # first call: eligible
    msgs1 = make_msgs([prior, newest1])
    body1 = json.dumps({"model":"test","max_tokens":10,"messages":msgs1}).encode()
    _, rec1 = shim.process_request(body1)
    assert rec1["experimental_event"], "first should be experimental"
    # second call: same task, also eligible -> should NOT randomize
    msgs2 = make_msgs([prior, newest1, newest2])
    body2 = json.dumps({"model":"test","max_tokens":10,"messages":msgs2}).encode()
    _, rec2 = shim.process_request(body2)
    assert not rec2["experimental_event"], "second should NOT be experimental"
    assert rec2["already_intervened"]
    print("  [PASS] test_single_intervention")

# --- Test 5: Stable assignment ---
def test_stable_assignment():
    reset()
    tid = "test_task"; eid = "test_task#call5"
    shim.SEED = 42
    a1, u1 = shim._randomize(tid, eid)
    a2, u2 = shim._randomize(tid, eid)
    assert a1 == a2 and u1 == u2, "assignment must be deterministic"
    print(f"  [PASS] test_stable_assignment (a={a1}, u={u1:.6f})")

# --- Test 6: Nonzero activation accounting ---
def test_activation_accounting():
    reset()
    prior = "\n".join([f"dup line {i} with enough chars to qualify" for i in range(60)])
    # newest: all lines are unique (eligible by size but 0% dup)
    newest = "\n".join([f"totally unique content line {i} long enough" for i in range(60)])
    msgs = make_msgs([prior, newest])
    body = json.dumps({"model":"test","max_tokens":10,"messages":msgs}).encode()
    _, rec = shim.process_request(body)
    # should be ineligible (0% dup)
    assert not rec["eligible"], f"should be ineligible (dup_frac={rec['duplicate_line_fraction']})"
    assert not rec["experimental_event"]
    print(f"  [PASS] test_activation_accounting (dup_frac={rec['duplicate_line_fraction']})")

if __name__ == "__main__":
    print("=== MRT RESCUE PROTOCOL TESTS ===")
    test_ineligible()
    test_eligible_linededup()
    test_eligible_noop()
    test_single_intervention()
    test_stable_assignment()
    test_activation_accounting()
    print("\n=== ALL 6 TESTS PASS ===")
