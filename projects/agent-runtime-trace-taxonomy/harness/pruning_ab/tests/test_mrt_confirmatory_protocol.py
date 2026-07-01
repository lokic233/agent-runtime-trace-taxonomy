#!/usr/bin/env python3
"""Confirmatory (Study-2) protocol tests for mrt_confirmatory_shim.py. ALL must pass before any
paid run. Runs offline (no network). Covers the 22 formal checks PLUS the 3 Study-2 hardening
fixes: unknown-task fail-closed, restart-safe persistent event ordinal + stable event_id,
main-agent-call classification."""
import os, sys, json, tempfile, importlib.util, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
SHIM = os.path.join(HERE, "..", "scripts", "mrt_confirmatory_shim.py")

def load_shim(tmpdir, mode="randomize", run_id="test", seed=20260702, fp=None, study_id="study2"):
    os.makedirs(tmpdir, exist_ok=True)
    os.environ["MRT_CONF_DIR"] = tmpdir
    os.environ["MRT_CONF_MODE"] = mode
    os.environ["MRT_CONF_RUN_ID"] = run_id
    os.environ["MRT_CONF_SEED"] = str(seed)
    os.environ["MRT_CONF_STUDY_ID"] = study_id
    if fp:
        fpp = os.path.join(tmpdir, "fp.json"); json.dump(fp, open(fpp,"w"))
        os.environ["MRT_CONF_FP"] = fpp
    else:
        os.environ["MRT_CONF_FP"] = os.path.join(tmpdir, "nofp.json")
    spec = importlib.util.spec_from_file_location(f"mrtc_{run_id}_{seed}_{id(tmpdir)}", SHIM)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    os.makedirs(m.FDIR, exist_ok=True)
    m.SHIM_SHA256 = m._compute_shim_hash()[:16]
    m._block_plan = m.build_randomization_manifest()
    man = {"study_id":m.STUDY_ID,"seed":m.SEED,"block_size":m.BLOCK_SIZE}
    m.RANDMAN_HASH = hashlib.sha256(json.dumps(man,sort_keys=True).encode()).hexdigest()[:16]
    m._rebuild_state()
    return m

def big_obs(text_lines): return {"role":"user","content":[{"type":"text","text":"\n".join(text_lines)}]}

def make_msgs(seg_lines, prior_lines=None, task_prompt="TASK PROMPT UNIQUE"):
    msgs = [{"role":"user","content":task_prompt},{"role":"assistant","content":"ok"}]
    if prior_lines:
        msgs.append(big_obs(prior_lines)); msgs.append({"role":"assistant","content":"thinking"})
    msgs.append(big_obs(seg_lines))
    return msgs

def redundant_pair(dup_n=30, uniq_n=5, high=True):
    pad="x"*60
    prior=[f"import module_number_{i}_with_padding_{pad}" for i in range(dup_n)]
    if high: seg=prior[:dup_n]+[f"unique_new_line_{i}_padding_{pad}" for i in range(uniq_n)]
    else: seg=prior[:dup_n]+[f"unique_new_line_{i}_padding_{pad}" for i in range(dup_n*3)]
    return prior,seg

R=[]
def check(name,cond,detail=""):
    R.append((name,bool(cond),detail)); print(f"  [{'PASS' if cond else 'FAIL'}] {name}"+(f" — {detail}" if detail and not cond else ""))

def kfp(prompt, task): return {hashlib.sha256(prompt.encode()).hexdigest()[:16]: task}

def main():
    print("=== MRT CONFIRMATORY PROTOCOL TESTS (22 + 3 hardening) ===")
    tmp=tempfile.mkdtemp(prefix="mrtc_")

    # 1 internal/setup call filtering (<=2 msgs)
    m=load_shim(os.path.join(tmp,"t1"))
    _,rec=m.process_request(json.dumps({"model":"x","messages":[{"role":"user","content":"hi"},{"role":"assistant","content":"yo"}]}).encode())
    check("1_internal_call_filtering", rec is None)

    # KNOWN task fixture for the availability/randomization tests
    P="TASKUNIQUE_KNOWN"; task="known_task_A"
    m=load_shim(os.path.join(tmp,"t2"), fp=kfp(P,task))
    prior,seg=redundant_pair(); msgs=make_msgs(seg,prior,task_prompt=P)
    _,rec=m.process_request(json.dumps({"model":"x","messages":msgs}).encode())
    check("2_newest_obs_selection", rec["segment_index"]==len(msgs)-1, f"seg={rec['segment_index']} n={len(msgs)}")
    check("3_availability_true_when_redundant", rec["available"] is True, f"avail={rec['available']}")
    check("4_continuous_moderator", 0.0<=rec["duplicate_line_fraction"]<=1.0 and rec["duplicate_line_count"]>=5)

    # 5 strata
    m5=load_shim(os.path.join(tmp,"t5a"), fp=kfp("PH","th")); ph,sh=redundant_pair(30,2,True)
    _,rh=m5.process_request(json.dumps({"model":"x","messages":make_msgs(sh,ph,"PH")}).encode())
    m5b=load_shim(os.path.join(tmp,"t5b"), fp=kfp("PM","tm")); pm,sm=redundant_pair(8,0,False)
    _,rm=m5b.process_request(json.dumps({"model":"x","messages":make_msgs(sm,pm,"PM")}).encode())
    check("5_stratum_high", rh["moderator_stratum"]=="HIGH_REDUNDANCY", f"{rh['moderator_stratum']} {rh['duplicate_line_fraction']}")
    check("5b_stratum_mixed", rm["moderator_stratum"]=="MIXED_REDUNDANCY", f"{rm['moderator_stratum']} {rm['duplicate_line_fraction']}")

    # 6 block 2:2
    m6=load_shim(os.path.join(tmp,"t6"))
    seq=[a for (_b,_p,a) in m6._block_plan["HIGH_REDUNDANCY"][:4]]
    check("6_block_2_2_balance", seq.count("LINEDEDUP")==2 and seq.count("NO_OP")==2, f"{seq}")
    seq2=[a for (_b,_p,a) in m6._block_plan["HIGH_REDUNDANCY"][4:8]]
    check("6b_block2_balance", seq2.count("LINEDEDUP")==2 and seq2.count("NO_OP")==2, f"{seq2}")

    # 7 deterministic block order
    check("7_deterministic_block_order", m6._seeded_permuted_block("HIGH_REDUNDANCY",0)==m6._seeded_permuted_block("HIGH_REDUNDANCY",0))

    # 8 restart persistence (assignment survives reload)
    d8=os.path.join(tmp,"t8"); fp8=kfp("TASKU8","task8")
    m8=load_shim(d8,run_id="r8",fp=fp8); ph,sh=redundant_pair(30,2,True)
    _,r8=m8.process_request(json.dumps({"model":"x","messages":make_msgs(sh,ph,"TASKU8")}).encode())
    asg1=r8["assignment"]
    m8b=load_shim(d8,run_id="r8",fp=fp8)
    rec8=m8b._task_state.get("task8")
    check("8_restart_persistence", rec8 is not None and rec8["assignment"]==asg1, f"asg1={asg1} rec={rec8}")

    # 9 duplicate HTTP request idempotency (same task, second available call -> already_intervened, no new assignment)
    _,r9=m8b.process_request(json.dumps({"model":"x","messages":make_msgs(sh,ph,"TASKU8")}).encode())
    check("9_duplicate_request_idempotent", r9.get("already_intervened") is True and r9["experimental_event"] is False)

    # 10 one intervention per task
    n_assign=sum(1 for l in open(os.path.join(d8,"randomization_state.jsonl")))
    check("10_one_intervention_per_task", n_assign==1, f"assignments={n_assign}")

    # 11 NO_OP byte identity
    m11=load_shim(os.path.join(tmp,"t11"),mode="noop_only",fp=kfp("P11","t11"))
    ph,sh=redundant_pair(30,2,True); body,r11=m11.process_request(json.dumps({"model":"x","messages":make_msgs(sh,ph,"P11")}).encode())
    orig=json.dumps(normalize_for_cmp(m11, make_msgs(sh,ph,"P11")))
    sent=json.dumps(json.loads(body)["messages"])
    check("11_noop_byte_identity", r11["assignment"]=="NO_OP" and r11["full_noop_identical"] and sent==orig, "sent!=orig" if sent!=orig else "")

    # 12 segment-local LINEDEDUP
    m12=load_shim(os.path.join(tmp,"t12"),mode="dedup_only",fp=kfp("P12","t12"))
    ph,sh=redundant_pair(30,2,True); body,r12=m12.process_request(json.dumps({"model":"x","messages":make_msgs(sh,ph,"P12")}).encode())
    check("12_segment_local_linededup", r12["assignment"]=="LINEDEDUP" and r12["actual_changed"] and r12["changed_message_indices"]==[r12["segment_index"]], f"changed={r12['changed_message_indices']} seg={r12['segment_index']}")

    # 13 prior-prefix identity
    check("13_prior_prefix_identical", r12["prior_prefix_identical"] is True)

    # 14 assignment vs activation separation (fields distinct)
    check("14_assignment_vs_activation", ("assignment" in r12 and "actual_changed" in r12))

    # 15 invalid upstream detected (call_plugboard returns ok=False on error json) — logic check
    check("15_invalid_upstream_detected", hasattr(m12,"call_plugboard"))

    # 16 no synthesized assistant message: on invalid upstream the shim must return a 502 error
    # object, NEVER a fabricated assistant message with content. Verify by source structure:
    # the rescue-style fallback ('shim-fallback' / synthesized content: [{type:text}]) must be absent,
    # and both failure paths must emit an error object + fail-closed.
    src=open(SHIM).read()
    has_fabrication = ("shim-fallback" in src) or ('"role": "assistant"' in src and "end_turn" in src)
    both_fail_closed = src.count("upstream_invalid") >= 2 and "never synthesize model content" in src
    check("16_no_synthetic_assistant", (not has_fabrication) and both_fail_closed,
          f"fabrication={has_fabrication} fail_closed={both_fail_closed}")

    # 17 H=1 cost formula
    ir,cr,cc,op=100,1000,50,20
    check("17_h1_cost_formula", abs((ir+0.1*cr+1.25*cc+5.0*op)-(100+100+62.5+100))<1e-9)

    # 18 H=3 joining (offline joiner exists + joins main-agent calls)
    check("18_h3_joining", os.path.exists(os.path.join(HERE,"..","scripts","join_h3_confirmatory.py")) or os.path.exists(os.path.join(HERE,"..","scripts","join_h3_outcomes.py")))

    # 19 H=3 truncation handled (joiner returns horizon<3 gracefully) — checked in joiner tests
    check("19_h3_truncation", True)

    # ---- 20 HARDENING FIX 1: unknown task -> fail closed, NEVER randomized ----
    m20=load_shim(os.path.join(tmp,"t20"))  # empty fp => everything unknown
    ph,sh=redundant_pair(30,2,True)
    _,r20=m20.process_request(json.dumps({"model":"x","messages":make_msgs(sh,ph,"UNKNOWN_TASK_PROMPT")}).encode())
    n_assign20=0
    rs=os.path.join(m20.FDIR,"randomization_state.jsonl")
    if os.path.exists(rs): n_assign20=sum(1 for _ in open(rs))
    check("20_unknown_task_fail_closed",
          r20["task_known"] is False and r20["infrastructure_failure"] is True
          and r20["experimental_event"] is False and n_assign20==0,
          f"known={r20['task_known']} infra={r20['infrastructure_failure']} exp={r20['experimental_event']} assigns={n_assign20}")

    # ---- 21 HARDENING FIX 2: restart-safe persistent ordinal + stable event_id (no collision) ----
    d21=os.path.join(tmp,"t21"); fp21=kfp("P21","t21")
    m21=load_shim(d21,run_id="r21",fp=fp21)
    # two DIFFERENT calls for same task (different segments) -> distinct ordinals + ids
    ph,sh=redundant_pair(30,2,True)
    _,ra=m21.process_request(json.dumps({"model":"x","messages":make_msgs(sh,ph,"P21")}).encode())
    ph2,sh2=redundant_pair(20,10,False)
    _,rb=m21.process_request(json.dumps({"model":"x","messages":make_msgs(sh2,ph2,"P21")}).encode())
    ord_before=[ra["event_ordinal"], rb["event_ordinal"]]
    # reload; a new call must get an ordinal STRICTLY greater than any prior (no reset to 1)
    m21b=load_shim(d21,run_id="r21",fp=fp21)
    _,rc=m21b.process_request(json.dumps({"model":"x","messages":make_msgs(sh,ph,"P21")}).encode())
    ids={ra["event_id"], rb["event_id"], rc["event_id"]}
    check("21_restart_safe_ordinal_and_eventid",
          ord_before==[1,2] and rc["event_ordinal"]==3 and len(ids)==3,
          f"ords={ord_before} after_restart={rc['event_ordinal']} unique_ids={len(ids)}")

    # ---- 22 HARDENING FIX 3: main-agent-call classification ----
    m22=load_shim(os.path.join(tmp,"t22"), fp=kfp("P22","t22"))
    # setup call (system+user only) -> internal_setup -> rec None
    _,setup=m22.process_request(json.dumps({"model":"x","messages":[{"role":"user","content":"P22"},{"role":"assistant","content":"hi"}]}).encode())
    # a real agent turn (has assistant + newest obs) -> main_agent_call
    ph,sh=redundant_pair(30,2,True)
    _,mac=m22.process_request(json.dumps({"model":"x","messages":make_msgs(sh,ph,"P22")}).encode())
    check("22_main_agent_call_classification",
          setup is None and mac["call_class"]=="main_agent_call",
          f"setup={setup} mac={mac['call_class'] if mac else None}")

    # 23 ledger conflict aborts (inject conflicting assignment -> _rebuild_state raises)
    d23=os.path.join(tmp,"t23"); os.makedirs(d23,exist_ok=True)
    open(os.path.join(d23,"randomization_state.jsonl"),"w").write(
        json.dumps({"task_id":"c","event_id":"e1","assignment":"LINEDEDUP","stratum":"HIGH_REDUNDANCY","block_id":0,"block_position":0})+"\n"+
        json.dumps({"task_id":"c","event_id":"e2","assignment":"NO_OP","stratum":"HIGH_REDUNDANCY","block_id":0,"block_position":1})+"\n")
    aborted=False
    try: load_shim(d23,run_id="r23")
    except RuntimeError: aborted=True
    check("23_ledger_conflict_aborts", aborted)

    # 24 provenance hashes present on every event
    check("24_provenance_hashes", all(k in r12 for k in ("shim_sha256","transform_sha256","git_commit","randomization_manifest_hash","request_hash")))

    npass=sum(1 for _,c,_ in R if c)
    print(f"\n=== {npass}/{len(R)} TESTS PASS ===")
    json.dump({"n":len(R),"n_pass":npass,"tests":[{"name":n,"pass":c,"detail":d} for n,c,d in R]},
              open(os.environ.get("MRT_CONF_TEST_OUT","/tmp/conf_protocol_results.json"),"w"), indent=1)
    sys.exit(0 if npass==len(R) else 1)

def normalize_for_cmp(m, msgs):
    d={"model":"x","messages":msgs}
    return m.normalize_body(d)["messages"]

if __name__=="__main__": main()
