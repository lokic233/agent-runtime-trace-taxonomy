#!/usr/bin/env python3
"""FROZEN pre-treatment feature extractor for Study-2 signal-action alignment discovery.
Analysis-only. Reads sealed events.jsonl (for intervention alignment) + the recorded
trajectories (pre-treatment content: the target tool observation + all PRIOR messages, which
are byte-identical across arms because the prefix was preserved).

STRICTLY pre-treatment: uses ONLY the target segment text and messages BEFORE the intervention
response. NEVER uses: characters_removed, realized output length, future calls, post rereads,
final resolution, post-treatment cache tokens, future rework, realized H3.

Alignment is hash-verified: the target message is the one whose sha256[:16] == segment_hash_before.

Output: results/pruning_ab/mrt_confirmatory/pre_treatment_features.jsonl  (one row/intervention)
        + feature_dictionary.json (definitions, determinism, prespecified vs exploratory)
Usage: extract_pretreatment_features.py <conf_dir> <arms_dir> <out_dir>
"""
import json, sys, os, re, hashlib, glob, math

def txt(c):
    if isinstance(c,str): return c
    if isinstance(c,list): return ''.join(b.get('text','') if isinstance(b,dict) else str(b) for b in c)
    return str(c) if c is not None else ''

# ---- frozen deterministic parsers ----
RE_PATH   = re.compile(r'\b[\w./-]+\.(?:py|txt|cfg|ini|toml|rst|md|json|yaml|yml|c|h|cpp|js|ts)\b')
RE_FUNC   = re.compile(r'\bdef\s+([A-Za-z_]\w*)')
RE_CLASS  = re.compile(r'\bclass\s+([A-Za-z_]\w*)')
RE_SYMBOL = re.compile(r'\b[A-Za-z_]\w*\s*\(')            # call-like symbols
RE_ERROR  = re.compile(r'\b(?:Error|Exception|Traceback|assert|FAILED|FAIL|failed)\b')
RE_TRACE  = re.compile(r'^\s*File "', re.M)
RE_TEST   = re.compile(r'\b(?:test_\w+|\w+_test|::test)\b')
RE_SHELL  = re.compile(r'\b(?:python|pytest|pip|cd|ls|cat|grep|git|make)\b')

def line_stats(seg):
    lines=[l.strip() for l in seg.split('\n') if len(l.strip())>=12]
    seen={}; dup_lines=0
    # duplicate spans: consecutive runs of duplicated lines
    return lines

def count_removable(seg, prior_texts):
    """estimate removable lines/chars: lines (>=12 chars) in seg that appear in prior obs."""
    prior=set()
    for pt in prior_texts:
        for l in pt.split('\n'):
            s=l.strip()
            if len(s)>=12: prior.add(s)
    seg_lines=[l for l in seg.split('\n')]
    rem_lines=0; rem_chars=0; spans=0; in_span=False; longest=0; cur=0; positions=[]
    for idx,l in enumerate(seg_lines):
        s=l.strip()
        if len(s)>=12 and s in prior:
            rem_lines+=1; rem_chars+=len(l)+1; positions.append(idx)
            if not in_span: spans+=1; in_span=True; cur=0
            cur+=1; longest=max(longest,cur)
        else:
            in_span=False; cur=0
    n=len([l for l in seg_lines])
    mean_pos=(sum(positions)/len(positions)/max(n,1)) if positions else 0.0  # 0=top,1=bottom
    return dict(removable_lines=rem_lines, removable_chars=rem_chars,
                removable_tokens_est=rem_chars//4, distinct_dup_spans=spans,
                longest_dup_span=longest, dup_position_mean=mean_pos)

def extract(conf_dir, arms_dir, out_dir):
    ev=[json.loads(l) for l in open(os.path.join(conf_dir,'events.jsonl'))]
    by_task={}
    for e in ev:
        by_task.setdefault(e['task_id'],[]).append(e)
    exp={e['task_id']:e for e in ev if e.get('experimental_event')}
    rows=[]; align_fail=[]
    for tid,e in exp.items():
        tjs=glob.glob(os.path.join(arms_dir,tid,'*.traj'))
        if not tjs: align_fail.append((tid,'no_traj')); continue
        d=json.load(open(tjs[0])); hist=d.get('history',[])
        # find target message by hash
        seg_i=None
        for i,m in enumerate(hist):
            t=txt(m.get('content'))
            if hashlib.sha256(t.encode('utf-8','replace')).hexdigest()[:16]==e['segment_hash_before']:
                seg_i=i; break
        if seg_i is None: align_fail.append((tid,'hash_mismatch')); continue
        seg=txt(hist[seg_i].get('content'))
        prior=[txt(m.get('content')) for m in hist[:seg_i]]          # STRICTLY pre-intervention
        prior_tool=[txt(m.get('content')) for j,m in enumerate(hist[:seg_i]) if m.get('role')=='tool']
        prior_asst=[txt(m.get('content')) for j,m in enumerate(hist[:seg_i]) if m.get('role')=='assistant']
        prior_all=' \n'.join(prior)
        # ---- removal-opportunity (from sealed event + segment) ----
        rem=count_removable(seg, prior_tool)
        f={'task_id':tid,'repo':e['repo'],'A':1 if e['assignment']=='LINEDEDUP' else 0,
           'stratum':e['moderator_stratum'],'block_id':e['block_id'],'block_position':e['block_position'],
           # -- removal opportunity (F1)
           'segment_chars':e['segment_chars'],'duplicate_line_count':e['duplicate_line_count'],
           'duplicate_line_fraction':e['duplicate_line_fraction'],'eligible_line_count':e['eligible_line_count'],
           'unique_line_count':e['unique_line_count'],
           'removable_lines_est':rem['removable_lines'],'removable_chars_est':rem['removable_chars'],
           'removable_tokens_est':rem['removable_tokens_est'],
           'removable_fraction_est':rem['removable_lines']/max(e['eligible_line_count'],1),
           'distinct_dup_spans':rem['distinct_dup_spans'],'longest_dup_span':rem['longest_dup_span'],
           'dup_position_mean':rem['dup_position_mean'],
           # -- semantic liveness (F2) — from SEGMENT + prior plan (pre-treatment)
           'seg_n_paths':len(set(RE_PATH.findall(seg))),
           'seg_n_funcs':len(set(RE_FUNC.findall(seg))),
           'seg_n_classes':len(set(RE_CLASS.findall(seg))),
           'seg_n_errors':len(RE_ERROR.findall(seg)),
           'seg_n_traceback_lines':len(RE_TRACE.findall(seg)),
           'seg_n_tests':len(set(RE_TEST.findall(seg))),
           'seg_n_shell':len(RE_SHELL.findall(seg)),
           'seg_contains_error':int(bool(RE_ERROR.search(seg))),
           'seg_contains_traceback':int(bool(RE_TRACE.search(seg))),
           # liveness: does the most recent assistant plan reference entities in the segment?
           'seg_entities_in_last_plan':0,  # filled below
           'entity_recurrence_prevK':0,
           # -- recoverability (F3)
           'seg_from_tool_output':1,   # target is a tool observation by construction
           'seg_looks_like_file_read':int(bool(RE_PATH.search(seg)) and not bool(RE_ERROR.search(seg))),
           'seg_looks_like_test_output':int(bool(RE_TEST.search(seg)) or bool(RE_TRACE.search(seg))),
           'seg_reproducible_from_repo':int(bool(RE_PATH.search(seg)) and not bool(RE_ERROR.search(seg))),
           'seg_transient_env_state':int(bool(re.search(r'\b(?:0x[0-9a-f]{6,}|/tmp/|PID|timestamp)\b',seg))),
           # -- cache geometry (F4) — pre-treatment cache/context
           'prior_cache_read':e['cache_read_tokens'],           # this call's read = prior materialized (pre-treatment input side)
           'materialized_prefix_est':e['cache_read_tokens']+e['cache_creation_tokens'],
           'calls_so_far':e['call_index'],
           'segment_pos_in_context':seg_i/max(len(hist),1),
           # -- trajectory state (F5)
           'main_agent_call_index':e['call_index'],
           'prior_tool_calls':len(prior_tool),'prior_assistant_calls':len(prior_asst),
           'prior_total_msgs':seg_i,
           'patch_exists_prior':int(any('diff --git' in p or '+++ b/' in p for p in prior)),
           'tests_run_prior':int(any(RE_TEST.search(p) for p in prior_tool)),
           'latest_test_failed':int(bool(prior_tool and RE_ERROR.search(prior_tool[-1]))) if prior_tool else 0,
           'error_loop_count':sum(1 for p in prior_tool if RE_TRACE.search(p)),
           'seg_len_chars':len(seg),
           }
        # liveness: entities in segment that recur in the last 2 assistant plans
        last_plans=' \n'.join(prior_asst[-2:]) if prior_asst else ''
        seg_entities=set(RE_FUNC.findall(seg))|set(RE_CLASS.findall(seg))|set(RE_PATH.findall(seg))
        f['seg_entities_in_last_plan']=sum(1 for ent in seg_entities if ent in last_plans)
        f['seg_entity_live_fraction']=(f['seg_entities_in_last_plan']/max(len(seg_entities),1))
        # entity recurrence over prior K=3 tool obs
        prevK=' \n'.join(prior_tool[-3:])
        f['entity_recurrence_prevK']=sum(1 for ent in seg_entities if ent in prevK)
        # phase heuristic (frozen rule): diagnosis if no patch & tests not run; implementation if patch exists; verification if tests run after patch
        if f['patch_exists_prior']: f['phase']='implementation_or_verification'
        elif f['tests_run_prior']: f['phase']='diagnosis_with_tests'
        else: f['phase']='early_diagnosis'
        f['phase_diagnosis']=int(f['phase'] in ('early_diagnosis','diagnosis_with_tests'))
        rows.append(f)
    os.makedirs(out_dir,exist_ok=True)
    with open(os.path.join(conf_dir,'pre_treatment_features.jsonl'),'w') as fo:
        for r in rows: fo.write(json.dumps(r)+'\n')
    # dictionary
    fdict={
     'n_interventions_with_features':len(rows),'alignment_failures':align_fail,
     'extraction':'hash-verified target segment (sha256[:16]==segment_hash_before); features from segment + STRICTLY prior messages only',
     'determinism':'fully deterministic frozen regex parsers; no LLM classifier',
     'families':{
       'F1_removal_opportunity':['segment_chars','duplicate_line_count','duplicate_line_fraction','removable_lines_est','removable_chars_est','removable_tokens_est','removable_fraction_est','distinct_dup_spans','longest_dup_span','dup_position_mean'],
       'F2_semantic_liveness':['seg_n_paths','seg_n_funcs','seg_n_classes','seg_n_errors','seg_n_traceback_lines','seg_n_tests','seg_contains_error','seg_contains_traceback','seg_entities_in_last_plan','seg_entity_live_fraction','entity_recurrence_prevK'],
       'F3_recoverability':['seg_from_tool_output','seg_looks_like_file_read','seg_looks_like_test_output','seg_reproducible_from_repo','seg_transient_env_state'],
       'F4_cache_geometry':['prior_cache_read','materialized_prefix_est','calls_so_far','segment_pos_in_context'],
       'F5_trajectory_state':['main_agent_call_index','prior_tool_calls','prior_assistant_calls','patch_exists_prior','tests_run_prior','latest_test_failed','error_loop_count','phase_diagnosis'],
     },
     'prohibited_post_treatment_excluded':['characters_removed','lines_removed','output_tokens','effective_cost_h1','latency_seconds','stop_reason','resolved','h3','future calls','post rereads'],
     'prespecified':True,'note':'extractor frozen BEFORE inspecting feature-specific treatment effects'}
    json.dump(fdict, open(os.path.join(conf_dir,'feature_dictionary.json'),'w'), indent=1)
    print(f"extracted {len(rows)} feature rows; alignment failures: {len(align_fail)}")
    if align_fail: print("  failures:", align_fail[:10])

if __name__=='__main__':
    extract(sys.argv[1], sys.argv[2], sys.argv[3])
