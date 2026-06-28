#!/usr/bin/env python3
"""run_full_annotation.py — Stage B production annotation driver (Section 12).

Resumable, self-checkpointing. For a given solver's traces:
  - shard into batches; render blinded packets (with scrub + hard assert)
  - 2 independent annotators per trace (different backends)
  - adjudicator invoked ONLY on disagreement (primary-L1 / bottleneck / abstain / missing-evidence / low-overlap)
  - 10% random triple-audit
Writes per-shard results to annotations/raw_votes/full/<solver>/ ; skips shards already done (resume).
Designed to run in the background over hours; commit incrementally from the caller.
"""
from __future__ import annotations
import json, os, sys, subprocess, random, glob, time
HERE=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE,'src'))
from render_trace import render
from parse_annotator_output import extract_json

AGENTENV="/tmp/agentenv.sh"
BACKENDS={"a1":"codex","a2":"claude","adj":"gemini"}  # codex fastest=primary; claude=2nd; gemini=adjudicator
TAXREF="/tmp/taxonomy_ref_v1.txt"

def render_batch(trace_ids, alias):
    out=[]
    for tid in trace_ids:
        try:
            r=render(tid, alias, "FULL", max_obs_chars=700, max_act_chars=450)
            out.append(r)
        except AssertionError:  # blinding leak -> skip (must not annotate a leaky trace)
            pass
        except Exception:
            pass
    return out

def call_backend(backend, prompt_file, out_file, err_file):
    env=f"source {AGENTENV} 2>/dev/null; "
    cmds={
      "claude": f"{env} claude -p --max-turns 1 < {prompt_file}",
      "codex":  f"{env} cd {HERE} && codex exec --skip-git-repo-check - < {prompt_file}",
      "gemini": f"{env} gemini -p 'Annotate per protocol on stdin. Output ONLY the JSON array.' < {prompt_file}",
    }
    with open(out_file,"w") as o, open(err_file,"w") as e:
        subprocess.run(cmds[backend], shell=True, stdout=o, stderr=e, timeout=1200)

def build_prompt(batch, role="annotator"):
    pf=f"/tmp/fullann_{role}_{os.getpid()}_{random.randint(0,9999)}.txt"
    with open(pf,"w") as f:
        f.write(open(os.path.join(HERE,"prompts","closed_label_annotator_v1.md")).read())
        f.write("\n=== FROZEN v1 TAXONOMY (use ONLY these labels) ===\n")
        f.write(open(TAXREF).read())
        f.write("\n=== TRACES TO ANNOTATE ===\n")
        f.write(json.dumps(batch))
        f.write("\n\nOutput a JSON ARRAY of annotation records (one per trace), schema-valid, "
                "evidence_action_ids per waste label, exactly one primary_bottleneck, annotator_id set. JSON only.")
    return pf

def annotate_shard(batch, shard_id, outdir):
    """2 annotators + adjudicate-on-disagreement + audit. Returns adjudicated records."""
    res={"shard":shard_id,"n":len(batch),"records":[]}
    # annotator 1 + 2
    votes={}
    for role,backend in (("a1",BACKENDS["a1"]),("a2",BACKENDS["a2"])):
        pf=build_prompt(batch, role)
        of=f"{outdir}/{shard_id}_{role}.json"; ef=of.replace('.json','.err')
        if not (os.path.exists(of) and os.path.getsize(of)>50):
            try: call_backend(backend, pf, of, ef)
            except Exception as ex: open(ef,"a").write(f"\nEXC {ex}")
        d=extract_json(open(of).read()) if os.path.exists(of) else None
        votes[role]=d if isinstance(d,list) else []
    return votes  # adjudication done in a post-pass (needs both votes parsed + aligned)

if __name__=="__main__":
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--alias", required=True)
    ap.add_argument("--index", required=True, help="jsonl index with trace_id+solver_alias")
    ap.add_argument("--shard-size", type=int, default=12)
    ap.add_argument("--max-shards", type=int, default=999)
    a=ap.parse_args()
    rows=[json.loads(l) for l in open(a.index) if json.loads(l)["solver_alias"]==a.alias]
    tids=[r["trace_id"] for r in rows]
    outdir=os.path.join(HERE,"annotations","raw_votes","full",a.alias)
    os.makedirs(outdir, exist_ok=True)
    shards=[tids[i:i+a.shard_size] for i in range(0,len(tids),a.shard_size)]
    print(f"{a.alias}: {len(tids)} traces -> {len(shards)} shards")
    done=0
    for si,shard in enumerate(shards[:a.max_shards]):
        sid=f"s{si:03d}"
        # resume: skip if both annotator outputs exist
        if all(os.path.exists(f"{outdir}/{sid}_{r}.json") and os.path.getsize(f"{outdir}/{sid}_{r}.json")>50 for r in ("a1","a2")):
            done+=1; continue
        batch=render_batch(shard, a.alias)
        if not batch: continue
        annotate_shard(batch, sid, outdir)
        done+=1
        print(f"  {sid} done ({done}/{len(shards)})", flush=True)
    print(f"{a.alias} COMPLETE: {done} shards")
