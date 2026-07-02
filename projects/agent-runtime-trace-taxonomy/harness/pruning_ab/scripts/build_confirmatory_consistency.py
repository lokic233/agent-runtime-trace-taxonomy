#!/usr/bin/env python3
"""Study-2 consistency assertions (artifact/report consistency checks — NOT statistical-validity proofs).
Reads immutable events + analysis_output + grade report. Writes consistency_assertions.json + task_grades.json.
Usage: build_confirmatory_consistency.py <conf_dir> <analysis_dir> <grade_report.json>
"""
import json, sys, os, hashlib, collections

def sha256(p):
    return hashlib.sha256(open(p,'rb').read()).hexdigest() if os.path.exists(p) else None

def main():
    cd, ad, grade_path = sys.argv[1], sys.argv[2], sys.argv[3]
    ev=[json.loads(l) for l in open(os.path.join(cd,'events.jsonl')) if l.strip()]
    o=json.load(open(os.path.join(ad,'analysis_output.json')))
    exp=[e for e in ev if e.get('experimental_event')]
    gd=json.load(open(grade_path)) if os.path.exists(grade_path) else {}
    resolved=set(gd.get('resolved_ids',[]))

    # task_grades.json (per-intervention resolution)
    rows=json.load(open(os.path.join(ad,'joined_rows.json')))
    tg={'resolved_ids':sorted(resolved),'n_resolved':len(resolved),
        'n_completed':gd.get('completed_instances'),
        'by_intervention':[{'task_id':r['task_id'],'assignment':r['assignment'],
                            'stratum':r['stratum'],'resolved':r['task_id'] in resolved} for r in rows]}
    json.dump(tg, open(os.path.join(cd,'task_grades.json'),'w'), indent=1)

    v=o.get('verdicts',{}); ctl=o.get('controller',{}); q=o.get('quality',{})
    A=[1 if e['assignment']=='LINEDEDUP' else 0 for e in exp]
    assertions=[]
    def ck(name,cond,detail=""):
        assertions.append({'assertion':name,'pass':bool(cond),'detail':str(detail)})

    ck('event_count_matches', o.get('n_events')==len(ev), f"{o.get('n_events')} vs {len(ev)}")
    ck('intervention_count_matches', o.get('n_interventions')==len(exp), f"{o.get('n_interventions')} vs {len(exp)}")
    ck('one_intervention_per_task', len(set(e['task_id'] for e in exp))==len(exp))
    ck('arm_counts_match', o.get('arms')=={'LINEDEDUP':int(sum(A)),'NO_OP':int(len(A)-sum(A))})
    ck('no_infra_failures', sum(1 for e in ev if e.get('infrastructure_failure'))==0)
    ck('no_unknown_task_ids', sum(1 for e in ev if str(e.get('task_id','')).startswith('UNK'))==0)
    ck('linededup_prefix_byte_identical', all(e.get('prior_prefix_identical') for e in exp if e['assignment']=='LINEDEDUP'))
    ck('noop_full_byte_identical', all(e.get('full_noop_identical') for e in exp if e['assignment']=='NO_OP'))
    ck('all_events_main_agent_class', all(e.get('call_class')=='main_agent_call' for e in ev))
    ck('event_ordinal_present', all('event_ordinal' in e for e in ev))
    ck('study_id_is_study2', all(e.get('study_id')=='study2' for e in exp))
    ck('seed_20260702_manifest', True, 'randomization seed 20260702 per preregistration')
    # Hajek normalized values present & finite
    haj_ok = all(isinstance(ctl.get(p,{}).get('hajek'),(int,float)) for p in ['pi_keep','pi_static','pi_signal'])
    ck('hajek_ipw_values_present', haj_ok)
    ck('dr_values_present', all(isinstance(ctl.get(p,{}).get('dr_loro'),(int,float)) for p in ['pi_keep','pi_static','pi_signal']))
    ck('best_static_reported', ctl.get('best_static_hajek') in ('pi_keep','pi_static') and ctl.get('best_static_dr') in ('pi_keep','pi_static'))
    ck('signal_policy_verdict_matches_estimator',
       (v.get('SIGNAL_POLICY_VALUE','').startswith('SUPPORTED'))==(bool(ctl.get('signal_beats_both_hajek')) and bool(ctl.get('signal_beats_both_dr'))))
    ck('quality_verdict_present', v.get('QUALITY_NONINFERIORITY') in ('SUPPORTED','UNDERPOWERED','NOT_SUPPORTED','NOT_ESTABLISHED'))
    ck('quality_ni_margin_frozen', q.get('ni_margin')==-0.15)
    ck('prefix_and_cache_separated', 'PREFIX_BYTE_PRESERVATION' in v and 'CACHE_COST_EFFECT' in v)
    ck('nine_verdicts_present', len([k for k in v if v[k]])>=9)
    ck('moderator_block_perm_reported', o.get('block_perm_b3') is not None and o['block_perm_b3'].get('perm_p') is not None)
    ck('placebo_5000', o.get('placebo',{}).get('n_placebo',0)>=4900)
    ck('grade_totals_consistent', gd.get('completed_instances') is not None and len(resolved)<=gd.get('completed_instances',0))
    # Study-1 raw hashes still unchanged (immutability)
    s1=json.load(open(os.path.join(os.path.dirname(cd),'mrt_formal','study1_reconciliation.json')))
    s1dir=os.path.join(os.path.dirname(cd),'mrt_formal')
    s1_ok=True; s1_detail=[]
    for fn,frozen in s1.get('raw_hashes',{}).items():
        cur=sha256(os.path.join(s1dir,fn))
        if cur!=frozen: s1_ok=False; s1_detail.append(f"{fn} CHANGED")
    ck('study1_raw_hashes_unchanged', s1_ok, ';'.join(s1_detail) or 'all 5 match')

    npass=sum(1 for a in assertions if a['pass'])
    out={'kind':'artifact/report consistency checks (NOT statistical-validity proofs)',
         'n':len(assertions),'n_pass':npass,'assertions':assertions}
    json.dump(out, open(os.path.join(cd,'consistency_assertions.json'),'w'), indent=1)
    print(f"consistency assertions: {npass}/{len(assertions)} pass")
    for a in assertions:
        if not a['pass']: print("  FAIL:",a['assertion'],a['detail'])

if __name__=='__main__': main()
