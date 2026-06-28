#!/usr/bin/env python3
"""compute_agreement.py — Stage A4 pilot agreement metrics + acceptance gates (Section 11).

Reads the per-annotator pilot annotation records (3 annotators x N traces) and computes:
  - Workload L1 categorical agreement (raw + Krippendorff-style alpha approx)
  - per-label binary agreement for each Waste L2 label
  - multi-label median pairwise Jaccard (waste L2 sets)
  - primary-bottleneck agreement
  - evidence overlap (Jaccard of cited action ids per shared label)
  - abstention rate, OTHER/UNKNOWN rate, taxonomy coverage
  - labels never selected, most-confused label pairs
Then checks the suggested acceptance gates and prints PASS/FAIL per gate.
"""
from __future__ import annotations
import json, sys, os, collections, itertools, statistics as st

GATES = {
    "workload_l1_agreement": 0.70,
    "primary_waste_l1_agreement": 0.70,
    "primary_l2_agreement": 0.60,
    "multilabel_median_jaccard": 0.65,
    "taxonomy_coverage": 0.95,
    "other_unknown_max": 0.05,
}

def _alpha_nominal(units):
    """Krippendorff's alpha (nominal). units = list of lists of labels (per item, raters).
    Returns alpha in [-?,1]; 1=perfect. Handles missing (None) by ignoring."""
    # observed disagreement
    items=[ [x for x in u if x is not None] for u in units ]
    items=[u for u in items if len(u)>=2]
    if not items: return None
    # value counts
    from collections import Counter
    Do_num=0; Do_den=0
    cnt=Counter()
    for u in items:
        m=len(u)
        for a,b in itertools.permutations(u,2):
            Do_num += (a!=b)
        Do_den += m*(m-1)
        for v in u: cnt[v]+=1
    Do = Do_num/Do_den if Do_den else 0
    N=sum(cnt.values())
    De_num=0
    vals=list(cnt)
    for a in vals:
        for b in vals:
            if a!=b: De_num += cnt[a]*cnt[b]
    De = De_num/(N*(N-1)) if N>1 else 0
    if De==0: return 1.0 if Do==0 else 0.0
    return 1 - Do/De

def pairwise_jaccard(sets):
    js=[]
    for a,b in itertools.combinations(sets,2):
        sa,sb=set(a),set(b)
        if not sa and not sb: js.append(1.0)
        else: js.append(len(sa&sb)/len(sa|sb) if (sa|sb) else 1.0)
    return js

def load_annotations(ann_files):
    """ann_files: {annotator_id: [record,...]}. Returns dict trace_id -> {ann: record}."""
    by_trace=collections.defaultdict(dict)
    for ann, recs in ann_files.items():
        for r in recs:
            tid=r.get("trace_id") or r.get("sample_id")
            if tid: by_trace[tid][ann]=r
    return by_trace

def compute(by_trace, all_l2_labels):
    anns=sorted({a for v in by_trace.values() for a in v})
    workload_units=[]; waste_l1_units=[]; bottleneck_units=[]
    ml_jaccards=[]; evidence_overlaps=[]
    abstains=0; total_annotations=0; other_unknown=0
    label_used=collections.Counter(); confusion=collections.Counter()
    covered_traces=0
    per_label_binary=collections.defaultdict(list)  # label -> list of agreement (1/0) across shared trace
    for tid, av in by_trace.items():
        recs=[av[a] for a in anns if a in av]
        if len(recs)<2: continue
        # workload L1
        wl=[r.get("workload_annotation",{}).get("primary_l1") for r in recs]
        workload_units.append(wl)
        # waste L1 (primary = parent of primary_bottleneck, or first l1)
        wl1=[ (r.get("waste_annotation",{}).get("l1_labels") or [None])[0] for r in recs]
        waste_l1_units.append(wl1)
        # primary bottleneck
        bn=[r.get("waste_annotation",{}).get("primary_bottleneck") for r in recs]
        bottleneck_units.append(bn)
        # multi-label jaccard on L2 sets
        l2sets=[set(r.get("waste_annotation",{}).get("l2_labels") or []) for r in recs]
        ml_jaccards += pairwise_jaccard(l2sets)
        # per-label binary agreement
        for lab in all_l2_labels:
            votes=[1 if lab in s else 0 for s in l2sets]
            if len(set(votes))==1: per_label_binary[lab].append(1)
            else: per_label_binary[lab].append(0)
        # coverage: at least one non-empty, non-OTHER label or explicit clean
        if any(l2sets) or any(r.get("waste_annotation",{}).get("primary_bottleneck") for r in recs):
            covered_traces+=1
        # evidence overlap: for labels both annotators chose, jaccard of action ids
        for a,b in itertools.combinations(recs,2):
            ea=a.get("waste_annotation",{}).get("evidence_action_ids") or {}
            eb=b.get("waste_annotation",{}).get("evidence_action_ids") or {}
            shared=set(ea)&set(eb)
            for lab in shared:
                sa,sb=set(ea[lab]),set(eb[lab])
                if sa|sb: evidence_overlaps.append(len(sa&sb)/len(sa|sb))
        # abstain / other / label usage / confusion
        for r in recs:
            total_annotations+=1
            if r.get("annotation_metadata",{}).get("abstain"): abstains+=1
            for lab in (r.get("waste_annotation",{}).get("l2_labels") or []):
                label_used[lab]+=1
                if lab in ("OTHER","UNKNOWN"): other_unknown+=1
        # confusion: disagreeing primary bottleneck pairs
        bset=[x for x in bn if x]
        for a,b in itertools.combinations(set(bset),2):
            confusion[tuple(sorted((a,b)))]+=1
    def raw_agree(units):
        ok=0;tot=0
        for u in units:
            vals=[x for x in u if x is not None]
            if len(vals)<2: continue
            tot+=1
            # majority agreement: all-equal counts as agree
            ok += 1 if len(set(vals))==1 else 0
        return ok/tot if tot else None
    n_multi = sum(1 for v in by_trace.values() if len(v)>=2)
    metrics={
        "n_traces_with_>=2_annotators": n_multi,
        "annotators": anns,
        "workload_l1_raw_agreement": raw_agree(workload_units),
        "workload_l1_alpha": _alpha_nominal(workload_units),
        "primary_waste_l1_raw_agreement": raw_agree(waste_l1_units),
        "primary_waste_l1_alpha": _alpha_nominal(waste_l1_units),
        "primary_bottleneck_raw_agreement": raw_agree(bottleneck_units),
        "primary_l2_agreement": raw_agree(bottleneck_units),  # primary bottleneck IS the primary L2
        "multilabel_median_jaccard": st.median(ml_jaccards) if ml_jaccards else None,
        "evidence_overlap_median": st.median(evidence_overlaps) if evidence_overlaps else None,
        "abstention_rate": abstains/total_annotations if total_annotations else None,
        "other_unknown_rate": other_unknown/max(sum(label_used.values()),1),
        "taxonomy_coverage": covered_traces/max(n_multi,1),
        "labels_never_selected": sorted(set(all_l2_labels)-set(label_used)),
        "label_prevalence": dict(label_used.most_common()),
        "most_confused_pairs": confusion.most_common(10),
        "per_label_binary_agreement": {k: (sum(v)/len(v) if v else None) for k,v in per_label_binary.items()},
    }
    return metrics

def metrics_cov(by_trace):
    return sum(1 for v in by_trace.values() if len(v)>=2)

def check_gates(m):
    res={}
    res["workload_l1"]      = (m["workload_l1_alpha"] or m["workload_l1_raw_agreement"] or 0) >= GATES["workload_l1_agreement"]
    res["primary_waste_l1"] = (m["primary_waste_l1_alpha"] or m["primary_waste_l1_raw_agreement"] or 0) >= GATES["primary_waste_l1_agreement"]
    res["primary_l2"]       = (m["primary_l2_agreement"] or 0) >= GATES["primary_l2_agreement"]
    res["multilabel_jaccard"]= (m["multilabel_median_jaccard"] or 0) >= GATES["multilabel_median_jaccard"]
    res["coverage"]         = (m["taxonomy_coverage"] or 0) >= GATES["taxonomy_coverage"]
    res["other_unknown"]    = (m["other_unknown_rate"] or 0) <= GATES["other_unknown_max"]
    return res

if __name__=="__main__":
    import argparse, glob, re
    ap=argparse.ArgumentParser()
    ap.add_argument("--glob", default="/tmp/pilot_out/ann*_assembled.json")
    ap.add_argument("--taxonomy", default="taxonomy/waste_taxonomy_v0.yaml")
    ap.add_argument("--out", default=None)
    a=ap.parse_args()
    import yaml
    all_l2=[x["id"] for x in yaml.safe_load(open(a.taxonomy))["l2"]]
    ann_files={}
    for f in glob.glob(a.glob):
        ann=re.search(r'(ann\d+)', os.path.basename(f)).group(1)
        try: ann_files[ann]=json.load(open(f))
        except Exception as e: print("skip",f,repr(e)[:60])
    by=load_annotations(ann_files)
    m=compute(by, all_l2)
    print(json.dumps({k:v for k,v in m.items() if k not in ('label_prevalence','per_label_binary_agreement')}, indent=2, default=str))
    print("\n=== ACCEPTANCE GATES ===")
    for g,ok in check_gates(m).items(): print(f"  {'✅' if ok else '❌'} {g}")
    if a.out: json.dump(m, open(a.out,"w"), indent=2, default=str)
