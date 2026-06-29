#!/usr/bin/env python3
"""analyze_arms.py — tiered kill-switch + loss-rate certification for the pruning A/B.

Per method arm vs C0 baseline (SAME tasks, re-run + graded):
  - resolution: did the candidate re-resolve a task C0 resolved? (paired)
  - regression_event = C0_resolved AND NOT candidate_resolved
  - token_saving: true prompt tokens (input+cache_read+cache_creation), paired per task
  - loss-rate one-sided 95% UPPER BOUND (Wilson) on P(regress | C0 resolved)

KILL TIERS:
  SCREEN (n~10): KILL if regressions>=2 (gross fail) OR median token_saving<=0.
                 Marginal (0-1 regression, saving>0) -> PROCEED to full 50.
  FULL  (n~50):  CERTIFY non-regression if loss_UB <= delta (default 6%); else REGIONAL/UNSAFE.
"""
import json, glob, os, sys, math, statistics as st
ROOT="/data/users/dengcchi"; PROOT=f"{ROOT}/prune_ab"

def wilson_upper(k, n, z=1.645):  # one-sided 95%
    if n==0: return 1.0
    p=k/n; d=1+z*z/n
    c=(p+z*z/(2*n))/d; m=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return min(1.0, c+m)

def resolved_set(arm):
    """graded resolved instance ids for an arm (from its grade json), else fall back to submission."""
    gj=glob.glob(f"{PROOT}/results/grade_{arm}.json")
    if gj:
        d=json.load(open(gj[0]))
        rs=d.get("resolved_ids") or d.get("resolved_instances") or []
        return set(rs)
    # fallback: submission-as-proxy (screen pre-grade)
    out=set()
    for tj in glob.glob(f"{PROOT}/arms/*_{arm}/*/*.traj"):
        tid=os.path.basename(tj).replace(".traj","")
        try:
            d=json.load(open(tj)); sub=(d.get("info",{}) or {}).get("submission")
            if sub and sub.strip(): out.add(tid)
        except: pass
    return out

def prompt_tokens_by_task(arm):
    """best-effort per-task prompt tokens; ledger isn't task-tagged so return arm total+calls."""
    f=f"{PROOT}/logs/ledger_{arm}.jsonl"
    tp=n=0
    if os.path.exists(f):
        for l in open(f):
            try:
                d=json.loads(l); p=(d.get("input")or 0)+(d.get("cache_read")or 0)+(d.get("cache_creation")or 0)
                if p>0: tp+=p; n+=1
            except: pass
    return tp,n

def analyze(arms, phase="screen", delta=0.06):
    base=resolved_set("C0_identity"); btp,bn=prompt_tokens_by_task("C0_identity")
    print(f"=== {phase.upper()} ANALYSIS === C0 resolved={len(base)} | baseline prompt-tok/call={btp//max(bn,1):,}")
    verdicts={}
    for m in arms:
        if m=="C0_identity": continue
        rs=resolved_set(m); tp,n=prompt_tokens_by_task(m)
        # paired: tasks C0 resolved AND this arm attempted
        # (use base as denominator; regression = in base, not in rs, but only count tasks the arm ran)
        ran=set(os.path.basename(os.path.dirname(t)) for t in glob.glob(f"{PROOT}/arms/{phase}_{m}/*/*.traj"))
        denom=base & ran
        regress=[t for t in denom if t not in rs]
        loss_ub=wilson_upper(len(regress), len(denom)) if denom else 1.0
        # token saving: per-call avg (paired-by-task needs task-tagged ledger; approx for now)
        sav=100*(btp/max(bn,1)-tp/max(n,1))/(btp/max(bn,1)) if bn and n else None
        if phase=="screen":
            kill = (len(regress)>=2) or (sav is not None and sav<=0)
            status="KILL" if kill else ("PROCEED_TO_FULL" if (sav and sav>0) else "WEAK")
        else:
            cert = (loss_ub<=delta) and (sav is not None and sav>0)
            status="GLOBAL_SAFE" if cert else ("UNSAFE" if regress else "INCONCLUSIVE")
        verdicts[m]={"resolved":len(rs),"paired_denom":len(denom),"regressions":len(regress),
                     "regress_ids":regress[:6],"loss_ub_95":round(loss_ub,3),
                     "token_saving_pct":round(sav,1) if sav is not None else None,"status":status}
        print(f"  {m:22s} denom={len(denom):2d} regress={len(regress)} loss_UB={loss_ub:.2f} tok_save={verdicts[m]['token_saving_pct']}% -> {status}")
    os.makedirs(f"{PROOT}/results",exist_ok=True)
    json.dump(verdicts, open(f"{PROOT}/results/{phase}_verdicts.json","w"), indent=2)
    return verdicts

if __name__=="__main__":
    phase=sys.argv[1] if len(sys.argv)>1 else "screen"
    arms=[l.split()[0] for l in open(f"{PROOT}/scripts/arms.txt") if l.strip()]
    analyze(arms, phase)

def pareto_rank(verdicts, delta_tiers=[0.0, 0.06, 0.15, 0.30]):
    """Rank all methods by saving (desc), annotate with risk tier based on loss_UB.
    Risk tiers: STRICT (0 regression), LOW (UB<6%), MEDIUM (UB<15%), HIGH (UB<30%), UNSAFE."""
    rows=[]
    for m,v in verdicts.items():
        tier = "STRICT" if v["regressions"]==0 else (
               "LOW" if v.get("loss_ub_95",1)<=0.06 else
               "MEDIUM" if v.get("loss_ub_95",1)<=0.15 else
               "HIGH" if v.get("loss_ub_95",1)<=0.30 else "UNSAFE")
        rows.append({**v, "method":m, "risk_tier":tier, "saving":v.get("token_saving_pct") or 0})
    rows.sort(key=lambda r:-r["saving"])
    return rows

if __name__=="__main__" and "pareto" in sys.argv:
    phase=sys.argv[2] if len(sys.argv)>2 else "full"
    arms=[l.split()[0] for l in open(f"{PROOT}/scripts/arms.txt") if l.strip()]
    verdicts=analyze(arms, phase)
    ranked=pareto_rank(verdicts)
    print(f"\n=== PARETO RANKING (saving desc, with risk tier) ===")
    print(f"{'rank':>4s} {'method':22s} {'saving':>7s} {'regress':>8s} {'loss_UB':>8s} {'risk_tier':>10s}")
    for i,r in enumerate(ranked,1):
        print(f"{i:4d} {r['method']:22s} {r['saving']:+6.1f}% {r['regressions']:8d} {r.get('loss_ub_95',1):8.3f} {r['risk_tier']:>10s}")

def final_table(verdicts):
    """The deliverable table: saving% + regressions + saving/regression ratio."""
    rows=[]
    for m,v in verdicts.items():
        sav=v.get("token_saving_pct") or 0
        reg=v.get("regressions",0)
        ratio = "∞ (0 regress)" if reg==0 else (round(sav/reg,1) if reg>0 else 0)
        rows.append({"method":m,"saving_pct":sav,"regressions":reg,"ratio":ratio,
                     "loss_ub":v.get("loss_ub_95"), "risk_tier":v.get("risk_tier","?")})
    rows.sort(key=lambda r:(-r["saving_pct"] if r["regressions"]==0 else -r["saving_pct"]/max(r["regressions"],0.01)))
    print(f"\n{'method':26s}{'saving%':>9s}{'regress':>9s}{'saving/regress':>16s}{'loss_UB':>9s}{'tier':>10s}")
    print("─"*79)
    for r in rows:
        print(f"  {r['method']:24s}{r['saving_pct']:+8.1f}%{r['regressions']:9d}{str(r['ratio']):>16s}{r['loss_ub'] or 0:9.3f}{r['risk_tier']:>10s}")
    return rows
