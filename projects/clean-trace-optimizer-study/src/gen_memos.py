#!/usr/bin/env python3
"""generate raw_trace_memos.jsonl from rendered audit traces — Lane A (neutral, evidence-grounded).
Deterministic marker detection + neutral descriptions + counter-interpretations.
Does NOT consult any opportunity ranking. Records observable sequences only.
"""
import glob, re, json, os
RDIR=os.environ.get('RDIR','/tmp/rendered_audit2')
OUT=os.environ['OUT']

# parse a rendered trace back into events
EV_RE=re.compile(r'^\[(\d+)\]\s+(\w+)\s+\|\s+(.*)$')
def parse(txt):
    evs=[]
    cur=None
    for line in txt.splitlines():
        m=EV_RE.match(line)
        if m:
            if cur: evs.append(cur)
            cur={'i':int(m.group(1)),'cls':m.group(2),'action':m.group(3),'thought':'','obs':''}
        elif cur is not None:
            s=line.strip()
            if s.startswith('thought:'): cur['thought']=s[8:].strip()
            elif s.startswith('obs:'): cur['obs']=s[4:].strip()
    if cur: evs.append(cur)
    return evs

def memo_for(trace_id, solver, evs):
    obs_seqs=[]; healthy=[]; harness=[]; env=[]; uncertain=[]
    # --- oversized-then-narrow read ---
    for k in range(len(evs)-1):
        if re.search(r'too large to display|abbreviated version|use .*view_range', evs[k]['obs'], re.I):
            # find a later narrow read of presumably same file
            for j in range(k+1,min(k+5,len(evs))):
                if evs[j]['cls']=='READ' and re.search(r'view_range|goto|\d+\s+\d+', evs[j]['action']):
                    obs_seqs.append(dict(start_event=evs[k]['i'],end_event=evs[j]['i'],
                        neutral_description="A read returned an oversized/abbreviated file; a later read narrowed to a line range.",
                        observable_evidence=["observation said file too large / abbreviated","subsequent read used a view_range/goto"],
                        possible_measurement="fraction of reads that are oversized and followed by a narrower re-read of the same target",
                        counterinterpretation="narrowing after an oversized read is the CORRECT recovery, not waste; only the initial unbounded read is arguably avoidable, and may be unavoidable if file size is unknown a priori"))
                    break
    # --- repeated editor failure (no replacement) ---
    fails=[e for e in evs if re.search(r'No replacement was performed|did not appear verbatim|multiple occurrences', e['obs'], re.I)]
    if len(fails)>=2:
        obs_seqs.append(dict(start_event=fails[0]['i'],end_event=fails[-1]['i'],
            neutral_description=f"{len(fails)} edit attempts reported 'no replacement performed' (old_str not matched).",
            observable_evidence=["editor observation: ERROR: No replacement was performed","repeated on consecutive edit actions"],
            possible_measurement="count of edit actions whose observation indicates the target text was not found",
            counterinterpretation="this is partly a TOOL-USE mismatch (whitespace/comment in old_str), not necessarily reasoning waste; the agent may correctly fix the old_str on the next try"))
    # --- harness split_string syntax bug (solver_C SWE-agent-1.0) ---
    if any(re.search(r'_split_string.*SyntaxError|future feature annotations', e['obs']) for e in evs):
        bad=[e for e in evs if re.search(r'future feature annotations', e['obs'])]
        harness.append(dict(start_event=bad[0]['i'],end_event=bad[-1]['i'],
            description="Edit observations show a SyntaxError from /root/commands/_split_string (future feature annotations).",
            note="HARNESS ARTIFACT: the edit tool's internal _split_string helper errored; the agent's edit content is not necessarily wrong. The agent's thought often says 'changes look good.' Edit-failure / churn features MUST exclude this pattern or they will conflate a harness bug with agent behavior."))
    # --- empty/no-expansion searches ---
    searches=[e for e in evs if e['cls']=='SEARCH']
    empties=[e for e in searches if re.search(r'No matches found|not found', e['obs'], re.I)]
    if len(empties)>=2:
        # were they reformulations that eventually found something? check if a later search expanded
        found_later=any(not re.search(r'No matches|not found', s['obs'], re.I) and s['obs'] for s in searches[searches.index(empties[-1])+1:] if True) if empties[-1] in searches else False
        obs_seqs.append(dict(start_event=empties[0]['i'],end_event=empties[-1]['i'],
            neutral_description=f"{len(empties)} searches returned no matches.",
            observable_evidence=["search observation: 'No matches found'"],
            possible_measurement="fraction of searches returning empty results / not expanding the candidate file set",
            counterinterpretation="empty results legitimately FALSIFY a hypothesis about symbol location and inform reformulation; a reformulated search that then succeeds is healthy localization, not waste"))
    # --- healthy edit->test->edit ---
    for k in range(len(evs)-2):
        win=evs[k:k+4]
        cls=[e['cls'] for e in win]
        if 'EDIT' in cls and 'TEST' in cls and cls.index('EDIT')<len(cls)-1:
            healthy.append(dict(start_event=win[0]['i'],end_event=win[-1]['i'],
                description="An edit followed by a test (and possible revision) within a short window.",
                reason_not_waste="edits interleaved with tests are evidence-driven iteration, not churn"))
            break
    # --- think no-op (OpenHands) ---
    if any(re.search(r'\[think\]|think\]: Your thought', e['obs']) for e in evs):
        env.append(dict(note="OpenHands 'think' tool produces a no-op action ('Your thought has been logged'); should be treated as PLAN/non-action, not a tool call, to avoid inflating action denominators.",
                        start_event=next(e['i'] for e in evs if re.search(r'\[think\]|think\]: Your thought', e['obs']))))
    # --- file-not-found from wrong CWD (env, not reasoning) ---
    if any(re.search(r"can't open file|No such file or directory", e['obs']) for e in evs):
        env.append(dict(note="Commands failed with 'No such file or directory' / can't open file — often a working-directory/setup issue, not reasoning waste.",
                        start_event=next(e['i'] for e in evs if re.search(r"can't open file|No such file or directory", e['obs']))))
    return dict(trace_id=trace_id, solver_alias=solver, n_events=len(evs),
                observed_sequences=obs_seqs, healthy_sequences=healthy,
                harness_artifacts=harness, environment_artifacts=env, uncertain_observations=uncertain)

n=0; mc=0
with open(OUT,'w') as out:
    for f in sorted(glob.glob(RDIR+'/*.txt')):
        base=os.path.basename(f)
        if '@' not in base: continue
        trace_id=base.replace('.txt','')
        solver=trace_id.split('@')[1]
        evs=parse(open(f).read())
        memo=memo_for(trace_id, solver, evs)
        out.write(json.dumps(memo)+'\n'); n+=1
        mc+=len(memo['observed_sequences'])+len(memo['harness_artifacts'])+len(memo['environment_artifacts'])
print(f"wrote {n} memos, {mc} total observations -> {OUT}")
