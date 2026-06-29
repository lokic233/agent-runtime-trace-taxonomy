#!/usr/bin/env python3
"""render_sample_traces.py — render sampled traces to compact, neutral text for manual audit.
Reads a sample jsonl (subset for this node), writes one .txt per trace with numbered
events: [idx] CLASS | action | -> obs(120c). NO opportunity labels, NO model names.
"""
import json, os, sys, argparse
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE)
import clean_loader as CL, clean_classify as CC

def render(path, solver, trace_id):
    steps=CL.load_file(path)
    lines=[f"TRACE {trace_id} (solver={solver})  [neutral render — no labels]",""]
    ai=0
    for s in steps:
        a=s['action_text']
        if not a and not s['thought']: continue
        cls,ev=CC.classify(a,s.get('raw_tool'),a)
        obs=(s['observation_text'] or '').replace('\n',' ')[:140]
        th=(s['thought'] or '').replace('\n',' ')[:80]
        lines.append(f"[{ai}] {cls:10s} | {a[:90]!r}")
        if th: lines.append(f"      thought: {th!r}")
        lines.append(f"      obs: {obs!r}")
        ai+=1
    return "\n".join(lines)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--sample',required=True)
    ap.add_argument('--solvers',required=True, help='comma list this node has, e.g. solver_B,solver_C')
    ap.add_argument('--outdir',required=True)
    a=ap.parse_args()
    want=set(a.solvers.split(','))
    os.makedirs(a.outdir,exist_ok=True)
    n=0
    for line in open(a.sample):
        r=json.loads(line)
        if r['solver_alias'] not in want: continue
        try:
            txt=render(r['source_path'], r['solver_alias'], r['trace_id'])
            open(os.path.join(a.outdir, r['trace_id'].replace('/','_')+'.txt'),'w').write(txt)
            n+=1
        except Exception as e:
            open(os.path.join(a.outdir, r['trace_id'].replace('/','_')+'.ERR.txt'),'w').write(f"{type(e).__name__}: {e}")
    print(f"rendered {n} traces -> {a.outdir}")

if __name__=='__main__': main()
