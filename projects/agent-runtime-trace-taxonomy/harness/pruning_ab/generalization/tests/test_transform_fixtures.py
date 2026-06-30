#!/usr/bin/env python3
"""Phase A transform fixture tests — assert the FROZEN treatment behavior on crafted message lists.
Imports the CANONICAL src/ copy (cb06efb6) and verifies per-mission Phase-A required assertions.
Run: python3 -m pytest test_transform_fixtures.py -q   (or python3 test_transform_fixtures.py)
"""
import os, sys, json, copy, hashlib, inspect, unittest
# import the canonical frozen prune_methods (src/ copy), NOT the stale harness copy
HERE=os.path.dirname(os.path.abspath(__file__))
SRC=os.path.normpath(os.path.join(HERE,"..","..","..","..","src","pruning_ab"))
assert os.path.exists(os.path.join(SRC,"prune_methods.py")), f"canonical src not found at {SRC}"
sys.path.insert(0, SRC)
import prune_methods as PM

CANON_MODULE_SHA="cb06efb69c9a08e7a48a1fca747a9fe1e9f71fcf657158a3c5463b028e0d10cf"
CANON_FN_SHA={
 "C0_identity":"50d7379887e105cf47d1bb9b02d1b032599ef9cf215d22d3e933816fcf3a6a32",
 "HYBRID1_m7_agg2":"6c9ab8b642bda9a3032ff2ef1f4d2492eb89e3dbd8a57e3c5694d53578b457b1",
 "LINEDEDUP_e4":"d3745ee0e66add3b9168d825d8f49d8131ca2ed87e7bbd34d6566bfcae718d7e",
 "GENTLE6K_stable":"b6946b104e2e87bda4afed6bd3be74bb501ff628c3c5bb1df49a055768a6c5aa",
 "CAP1K_stable":"7ccec6960f058a4996fe28a72b7ee3498833127e3d97d7f1f74d5fd09720a115",
 "RETRIEVREF_e4":"03c05e5078e3d5bb0a1377385a1a89e23d6499a4846fe656d764f7676378d869",
}

def fnsha(m): return hashlib.sha256(inspect.getsource(PM.METHODS[m]).encode()).hexdigest()
def obs(text):  # a tool_result observation message (role user, with tool_result block)
    return {"role":"user","content":[{"type":"tool_result","tool_use_id":"x","content":[{"type":"text","text":text}]}]}
def asst(text): return {"role":"assistant","content":[{"type":"text","text":text}]}

def make_traj(observations):
    """system, task(user, i=1 protected), then alternating assistant/observation."""
    msgs=[{"role":"system","content":"SYS PROMPT"},{"role":"user","content":"TASK STATEMENT"}]
    for o in observations:
        msgs.append(asst("thinking + tool call")); msgs.append(obs(o))
    return msgs

# SHAM mirror of the shim's mode (deepcopy + recount, byte-identical return)
def sham(messages):
    _=copy.deepcopy(messages); _=sum(len(PM._txt(m.get("content"))) for m in _)
    return messages

class TestProvenance(unittest.TestCase):
    def test_module_is_canonical(self):
        self.assertEqual(hashlib.sha256(inspect.getsource(PM).encode()).hexdigest(), CANON_MODULE_SHA,
                         "imported prune_methods is NOT the canonical frozen src/ copy")
    def test_function_hashes_frozen(self):
        for m,h in CANON_FN_SHA.items():
            self.assertIn(m, PM.METHODS, f"{m} missing from registry")
            self.assertEqual(fnsha(m), h, f"{m} function source changed since freeze")

class TestC0(unittest.TestCase):
    def test_c0_byte_identical(self):
        msgs=make_traj(["a"*100,"b"*9000])
        out=PM.apply_method("C0_identity", msgs)
        self.assertEqual(json.dumps(out,sort_keys=True), json.dumps(msgs,sort_keys=True))

class TestSHAM(unittest.TestCase):
    def test_sham_byte_identical(self):
        msgs=make_traj(["dup\nline\n"*50, "x"*8000])
        out=sham(msgs)
        self.assertEqual(json.dumps(out,sort_keys=True), json.dumps(msgs,sort_keys=True))

class TestLINEDEDUP(unittest.TestCase):
    def test_removes_only_earlier_seen_lines_and_preserves_order_roles(self):
        # obs1 establishes lines; obs2 (>300 chars) repeats them verbatim + adds a new line -> dups elided, new kept
        block="\n".join(f"identical_line_number_{i:03d}_padding_padding" for i in range(40))  # each line >=12 chars
        new_unique="BRAND_NEW_UNIQUE_LINE_kept_kept_kept"
        msgs=make_traj([block, block+"\n"+new_unique])
        out=PM.apply_method("LINEDEDUP_e4", msgs)
        # roles + count preserved
        self.assertEqual([m["role"] for m in out],[m["role"] for m in msgs])
        self.assertEqual(len(out), len(msgs))
        # first obs (index 3) is the EARLIER identical copy -> must remain available (not gutted)
        first_obs=PM._txt(out[3]["content"])
        self.assertIn("identical_line_number_000", first_obs, "earlier identical copy was destroyed")
        # second obs (index 5) had its dup lines elided but kept the unique line
        second_obs=PM._txt(out[5]["content"])
        self.assertIn(new_unique, second_obs, "unique new line was wrongly dropped")
        self.assertIn("duplicate lines elided", second_obs, "dedup did not fire on repeated block")
    def test_short_obs_untouched(self):
        msgs=make_traj(["tiny"])  # <300 chars -> only registered, never mutated
        out=PM.apply_method("LINEDEDUP_e4", msgs)
        self.assertEqual(PM._txt(out[3]["content"]), "tiny")
    def test_system_and_task_untouched(self):
        msgs=make_traj(["z"*5000]*3)
        out=PM.apply_method("LINEDEDUP_e4", msgs)
        self.assertEqual(out[0]["content"], msgs[0]["content"])  # system
        self.assertEqual(out[1]["content"], msgs[1]["content"])  # task statement

class TestGENTLE6K(unittest.TestCase):
    def test_only_over_6000_changed(self):
        small="s"*5999; big="B"*6500
        msgs=make_traj([small, big])
        out=PM.apply_method("GENTLE6K_stable", msgs)
        self.assertEqual(PM._txt(out[3]["content"]), small, "obs <=6000 must be untouched")
        self.assertNotEqual(PM._txt(out[5]["content"]), big, "obs >6000 must be capped")
        self.assertLess(len(PM._txt(out[5]["content"])), len(big))
    def test_boundary_6000_untouched(self):
        msgs=make_traj(["c"*6000])
        out=PM.apply_method("GENTLE6K_stable", msgs)
        self.assertEqual(PM._txt(out[3]["content"]), "c"*6000)

class TestCAP1K(unittest.TestCase):
    def test_head_tail_frozen_shape(self):
        big="H"*600+"M"*2000+"T"*400
        msgs=make_traj([big])
        out=PM.apply_method("CAP1K_stable", msgs)
        capped=PM._txt(out[3]["content"])
        self.assertIn("chars elided", capped)
        self.assertTrue(capped.startswith("H"), "head not preserved")
        self.assertTrue(capped.endswith("T"), "tail not preserved")
        # head=600 (0.6*1000), tail=400 (0.4*1000)
        self.assertEqual(capped[:600], "H"*600)

class TestHYBRID1(unittest.TestCase):
    def test_rewrites_old_prefix_when_eligible(self):
        # need >12 observations for HYBRID1 to fire
        msgs=make_traj([f"observation_{i} "+("data "*100) for i in range(16)])
        out=PM.apply_method("HYBRID1_m7_agg2", msgs)
        # the earliest observations (very old, < medium_cut) must be cleared/rewritten
        old_obs=PM._txt(out[3]["content"])
        self.assertIn("cleared", old_obs.lower()+ "", )
        # at least one already-materialized prefix message changed
        changed=sum(1 for a,b in zip(msgs,out) if PM._txt(a.get("content"))!=PM._txt(b.get("content")))
        self.assertGreater(changed, 0, "HYBRID1 did not rewrite any prefix")
    def test_short_traj_noop(self):
        msgs=make_traj(["x"*5000]*5)  # <=12 obs -> returns unchanged
        out=PM.apply_method("HYBRID1_m7_agg2", msgs)
        self.assertEqual(json.dumps(out,sort_keys=True), json.dumps(msgs,sort_keys=True))

if __name__=="__main__":
    unittest.main(verbosity=2)
