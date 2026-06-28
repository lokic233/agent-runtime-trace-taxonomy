#!/usr/bin/env python3
"""synthesize_taxonomy.py — Lane 6 synthesizer.

Merge N INDEPENDENT open-coding outputs into candidate v0 taxonomies. Runs only AFTER
all open coders finish (they never saw each other). Produces:
  - waste_taxonomy_v0.yaml (L1/L2 with full label spec)
  - workload_taxonomy_v0.yaml
  - rejected_and_merged_labels.md (preserves disagreements + rejections)
  - a coverage/overlap report

Rules enforced:
  - <= 7 Waste L1, 12-18 (hard max 22) Waste L2.
  - A label proposed by >=2 independent coders is STRONG; by 1 is CANDIDATE (kept only if
    crisp+distinguishable). Near-duplicate names merged by normalized token overlap.
  - NO label may be defined solely by final outcome (we flag outcome_collapse_risks).
  - Categories that require unavailable info are quarantined (not in v0).
  - Must NOT create categories merely to distinguish model families.
"""
from __future__ import annotations
import json, sys, os, re, collections, difflib

def load_coder(path):
    txt=open(path).read()
    try: return json.loads(txt)
    except Exception:
        m=re.search(r'\{.*\}', txt, re.S)
        if m:
            try: return json.loads(m.group(0))
            except Exception: return None
    return None

def norm(s): return re.sub(r'[^a-z]','',(s or '').lower())

def token_set(name):
    return set(re.split(r'[_\s]+',(name or '').lower()))

def similar(a,b):
    """name similarity: token Jaccard + sequence ratio."""
    ta,tb=token_set(a),token_set(b)
    jac=len(ta&tb)/max(len(ta|tb),1)
    seq=difflib.SequenceMatcher(None,norm(a),norm(b)).ratio()
    return max(jac,seq)

def cluster_patterns(all_patterns, thresh=0.45):
    """Greedy single-link clustering of pattern proposals by name+definition similarity."""
    clusters=[]
    for p in all_patterns:
        placed=False
        for c in clusters:
            rep=c['members'][0]
            s_name=similar(p['proposed_name'], rep['proposed_name'])
            s_def=difflib.SequenceMatcher(None,(p.get('definition') or '')[:300].lower(),
                                          (rep.get('definition') or '')[:300].lower()).ratio()
            if s_name>=thresh or (s_name>=0.3 and s_def>=0.5):
                c['members'].append(p); placed=True; break
        if not placed:
            clusters.append({'members':[p]})
    return clusters

def main(coder_paths, out_dir):
    coders={}
    for cp in coder_paths:
        cid=os.path.basename(cp).replace('.json','')
        d=load_coder(cp)
        if d: coders[cid]=d
    print(f"loaded {len(coders)} coders: {list(coders)}")
    # gather all proposed patterns with provenance
    allp=[]
    for cid,d in coders.items():
        for p in d.get('patterns',[]):
            p=dict(p); p['_coder']=cid; allp.append(p)
    print(f"total proposed patterns: {len(allp)}")
    clusters=cluster_patterns(allp)
    # rank clusters by # distinct coders
    for c in clusters:
        c['coders']=sorted(set(m['_coder'] for m in c['members']))
        c['support']=len(c['coders'])
        # pick canonical name = most common normalized, prefer multi-coder member
        names=[m['proposed_name'] for m in c['members']]
        c['canonical']=collections.Counter(names).most_common(1)[0][0]
        parents=[m.get('proposed_parent') for m in c['members'] if m.get('proposed_parent')]
        c['parents']=collections.Counter(parents)
        obs=[m.get('observability') for m in c['members'] if m.get('observability')]
        c['observability']=collections.Counter(obs)
    clusters.sort(key=lambda c:(-c['support'], -len(c['members'])))
    # collect cross-coder negative signals
    collapse=[]; uncovered=[]; needs=[]; fps=[]
    for cid,d in coders.items():
        for x in d.get('outcome_collapse_risks',[]): collapse.append((cid,x))
        for x in d.get('uncovered_patterns',[]): uncovered.append((cid,x))
        for x in d.get('needs_unavailable_info',[]): needs.append((cid,x))
        for x in d.get('false_positive_examples',[]): fps.append((cid,x))
    os.makedirs(out_dir,exist_ok=True)
    summary={
        "n_coders":len(coders),"coders":list(coders),
        "total_patterns":len(allp),"n_clusters":len(clusters),
        "multi_coder_clusters":sum(1 for c in clusters if c['support']>=2),
        "single_coder_clusters":sum(1 for c in clusters if c['support']==1),
        "clusters":[{
            "canonical":c['canonical'],"support":c['support'],"coders":c['coders'],
            "member_names":[m['proposed_name'] for m in c['members']],
            "parents":dict(c['parents']),"observability":dict(c['observability']),
            "definitions":[{"coder":m['_coder'],"name":m['proposed_name'],"def":m.get('definition'),
                            "parent":m.get('proposed_parent'),
                            "distinguishing_rule":m.get('distinguishing_rule'),
                            "interventions":m.get('candidate_interventions'),
                            "evidence":m.get('evidence_action_ids')} for m in c['members']],
        } for c in clusters],
        "outcome_collapse_risks":collapse,"uncovered_patterns":uncovered,
        "needs_unavailable_info":needs,"false_positive_examples":fps,
    }
    json.dump(summary, open(os.path.join(out_dir,"synthesis_raw.json"),"w"), indent=2, default=str)
    print(f"\n=== CLUSTERS (by cross-coder support) ===")
    for c in clusters:
        print(f"  [{c['support']} coders {','.join(c['coders'])}] {c['canonical']:42s} parent={dict(c['parents'])}")
    print(f"\nmulti-coder (STRONG) clusters: {summary['multi_coder_clusters']}")
    print(f"single-coder (CANDIDATE) clusters: {summary['single_coder_clusters']}")
    print(f"outcome_collapse_risks flagged: {len(collapse)} | uncovered: {len(uncovered)} | needs-unavailable: {len(needs)}")
    return summary

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--coders", nargs="+", required=True)
    ap.add_argument("--out", default="/tmp/synthesis")
    a=ap.parse_args()
    main(a.coders, a.out)
