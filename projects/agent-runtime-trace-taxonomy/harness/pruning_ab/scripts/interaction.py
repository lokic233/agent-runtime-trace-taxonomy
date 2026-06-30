#!/usr/bin/env python3
import json, os, statistics as st, math, random
BASE="/data/users/dengcchi/prune_ab"
feats={r["task_id"]:r for r in (json.loads(l) for l in open(f"{BASE}/results/pruning_ab/pre_treatment_features.jsonl"))}
def eff(led):
    a={}
    for l in open(f"{BASE}/{led}"):
        try:
            d=json.loads(l);t=d.get("task_id")
            if not t or str(t).startswith(("UNKNOWN","NO_")):continue
            ir=(d.get("input_tokens")or 0);cr=(d.get("cache_read_tokens")or 0);cc=(d.get("cache_creation_tokens")or 0);op=(d.get("output_tokens")or 0)
            a[t]=a.get(t,0)+ir+cr*.1+cc*1.25+op*5
        except:pass
    return a
c0=eff("logs/stable/ledger_C0_identity.jsonl");ld=eff("logs/e4/ledger_LINEDEDUP_e4.jsonl");g6=eff("logs/stable/ledger_GENTLE6K_stable.jsonl")
common=sorted(set(c0)&set(ld)&set(g6)&set(feats))
# build long-format: rows of (delta_pct, feature=dup_ratio, method_is_LINEDEDUP)
# delta = pct cost saving vs C0
rows=[]
for t in common:
    if c0[t]<=0: continue
    f=feats[t]["dup_line_ratio"]
    rows.append((100*(c0[t]-ld[t])/c0[t], f, 1))  # LINEDEDUP
    rows.append((100*(c0[t]-g6[t])/c0[t], f, 0))  # GENTLE6K
# standardize feature
fs=[r[1] for r in rows]; mf=st.mean(fs); sf=st.pstdev(fs) or 1
# design: intercept, feat, method, feat*method
X=[[1, (r[1]-mf)/sf, r[2], ((r[1]-mf)/sf)*r[2]] for r in rows]
y=[r[0] for r in rows]
n=len(y); p=4
# OLS via normal equations (manual, 4 params)
def matmul_T(X): # X^T X
    return [[sum(X[k][i]*X[k][j] for k in range(n)) for j in range(p)] for i in range(p)]
def matvec_T(X,y):
    return [sum(X[k][i]*y[k] for k in range(n)) for i in range(p)]
def solve(A,b):
    import copy; A=[row[:] for row in A]; b=b[:]
    for i in range(p):
        piv=A[i][i]
        for j in range(p): A[i][j]/=piv
        b[i]/=piv
        for k in range(p):
            if k!=i:
                f=A[k][i]
                for j in range(p): A[k][j]-=f*A[i][j]
                b[k]-=f*b[i]
    return b
beta=solve(matmul_T(X),matvec_T(X,y))
# bootstrap CI on interaction term (beta[3])
random.seed(3); b3s=[]
for _ in range(2000):
    idx=[random.randrange(n) for _ in range(n)]
    Xb=[X[i] for i in idx]; yb=[y[i] for i in idx]
    try:
        def mm(Xx): return [[sum(Xx[k][i]*Xx[k][j] for k in range(n)) for j in range(p)] for i in range(p)]
        def mv(Xx,yy): return [sum(Xx[k][i]*yy[k] for k in range(n)) for i in range(p)]
        bb=solve(mm(Xb),mv(Xb,yb)); b3s.append(bb[3])
    except: pass
b3s.sort()
print("="*70)
print("PHASE 4B: INTERACTION REGRESSION delta_cost ~ dup_ratio + method + dup_ratio*method")
print("="*70)
print(f"  n={n} (2 methods x {len(common)} tasks)")
print(f"  intercept (GENTLE6K @ mean dup) = {beta[0]:+.1f}%")
print(f"  dup_ratio (std) coef           = {beta[1]:+.1f}%  (effect of dup on GENTLE6K saving)")
print(f"  method=LINEDEDUP coef          = {beta[2]:+.1f}%  (LINEDEDUP vs GENTLE6K baseline)")
print(f"  *** INTERACTION (dup x LINEDEDUP) = {beta[3]:+.2f}%  95% CI [{b3s[50]:+.2f}, {b3s[1949]:+.2f}] ***")
sig = b3s[50]>0 or b3s[1949]<0
print(f"\n  Interaction CI {'EXCLUDES' if sig else 'INCLUDES'} zero")
print(f"  => the KEY quantity: does dup_ratio modify LINEDEDUP's effect DIFFERENTLY than GENTLE6K's?")
print(f"  => {'YES — significant differential modification' if sig else 'NO — dup_ratio affects both methods similarly (not method-specific)'}")
json.dump({"interaction_coef":round(beta[3],3),"interaction_ci":[round(b3s[50],3),round(b3s[1949],3)],
           "feat_coef":round(beta[1],3),"method_coef":round(beta[2],3),"n":n,"interaction_significant":sig},
          open(f"{BASE}/results/pruning_ab/interaction_regression.json","w"),indent=1)
print("\ninteraction_regression.json written")
