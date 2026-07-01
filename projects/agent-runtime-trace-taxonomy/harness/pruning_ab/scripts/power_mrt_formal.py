#!/usr/bin/env python3
"""Power simulation for the formal MRT interaction test.
Uses H=1 variance from pre-experiment C0/rescue data (NOT new treatment effects).
Simulates the preregistered interaction regression and reports power vs N.

Model: Y_i = b0 + b1*A + b2*S + b3*A*S + eps, S = centered dup_frac, A in {0,1}.
Primary parameter: b3 (does redundancy modify the LINEDEDUP effect).
"""
import json, math, random, statistics, sys

def simulate(n_events, b1, b3, sd, seed=1, n_sims=2000, alpha=0.05,
             high_frac=0.5, s_center=0.5):
    """Return power = P(reject H0: b3=0) via OLS t-test, at given N and true b3."""
    rng = random.Random(seed)
    rejections = 0
    b3_ests = []
    for _ in range(n_sims):
        A=[]; S=[]; Y=[]
        for i in range(n_events):
            a = i % 2  # balanced by block
            # dup_frac: mixture of HIGH (~0.7) and MIXED (~0.2)
            if rng.random() < high_frac:
                s_raw = min(1.0, max(0.41, rng.gauss(0.75, 0.15)))
            else:
                s_raw = min(0.40, max(0.05, rng.gauss(0.22, 0.10)))
            s = s_raw - s_center
            y = 5700 + b1*a + (-500)*s + b3*a*s + rng.gauss(0, sd)
            A.append(a); S.append(s); Y.append(y)
        # OLS with design [1, A, S, A*S]
        import itertools
        X = [[1.0, A[i], S[i], A[i]*S[i]] for i in range(n_events)]
        beta, se = ols(X, Y)
        if beta is None: continue
        t = beta[3]/se[3] if se[3]>0 else 0
        # two-sided
        if abs(t) > 1.96:
            rejections += 1
        b3_ests.append(beta[3])
    return rejections/max(n_sims,1), (statistics.mean(b3_ests) if b3_ests else None)

def ols(X, Y):
    """Plain OLS via normal equations. Returns (beta, se) or (None,None) if singular."""
    k=len(X[0]); n=len(X)
    # XtX
    XtX=[[sum(X[i][a]*X[i][b] for i in range(n)) for b in range(k)] for a in range(k)]
    XtY=[sum(X[i][a]*Y[i] for i in range(n)) for a in range(k)]
    inv=matinv(XtX)
    if inv is None: return None,None
    beta=[sum(inv[a][b]*XtY[b] for b in range(k)) for a in range(k)]
    # residual variance
    resid=[Y[i]-sum(X[i][a]*beta[a] for a in range(k)) for i in range(n)]
    dof=max(n-k,1)
    s2=sum(r*r for r in resid)/dof
    se=[math.sqrt(max(s2*inv[a][a],0)) for a in range(k)]
    return beta, se

def matinv(M):
    n=len(M)
    A=[row[:]+[1.0 if i==j else 0.0 for j in range(n)] for i,row in enumerate(M)]
    for col in range(n):
        piv=max(range(col,n), key=lambda r: abs(A[r][col]))
        if abs(A[piv][col])<1e-12: return None
        A[col],A[piv]=A[piv],A[col]
        d=A[col][col]
        A[col]=[x/d for x in A[col]]
        for r in range(n):
            if r!=col:
                f=A[r][col]
                A[r]=[A[r][j]-f*A[col][j] for j in range(2*n)]
    return [row[n:] for row in A]

def ate_power(n_events, b1, sd, seed=1, n_sims=2000):
    rng=random.Random(seed); rej=0
    for _ in range(n_sims):
        A=[i%2 for i in range(n_events)]
        Y=[5700+b1*A[i]+rng.gauss(0,sd) for i in range(n_events)]
        g1=[Y[i] for i in range(n_events) if A[i]==1]; g0=[Y[i] for i in range(n_events) if A[i]==0]
        if len(g1)<2 or len(g0)<2: continue
        m1,m0=statistics.mean(g1),statistics.mean(g0)
        v1,v0=statistics.variance(g1),statistics.variance(g0)
        se=math.sqrt(v1/len(g1)+v0/len(g0))
        if se>0 and abs((m1-m0)/se)>1.96: rej+=1
    return rej/n_sims

if __name__=="__main__":
    var=json.load(open('/tmp/variance_est.json'))
    sd=var["mid_traj_h1_sd"] or 2100
    print(f"Using H=1 SD={sd:.0f} (from C0 mid-trajectory ledger)")
    # Minimum practically-relevant effects (frozen):
    #  - MDE ATE (b1): 10% of mean cost ~ 570 eff-cost units
    #  - MDE interaction (b3): a moderator that flips LINEDEDUP from +5% harm at S=0 to -5% help
    #    across the dup_frac range (~0.7 span) => b3 ~ -1600 per unit dup_frac
    B1_MDE=-570.0     # LINEDEDUP saves ~10% on average
    B3_MDE=-2000.0    # redundancy strongly moderates
    B3_MOD=-1000.0    # moderate moderator
    out={"sd_used":sd,"b1_mde":B1_MDE,"b3_mde":B3_MDE,"alpha":0.05,"n_sims":2000,"curves":{}}
    print("\nN_events | power(b3=-2000 strong) | power(b3=-1000 moderate) | power(b1 ATE=-570)")
    for n in [20,30,40,60,80,120,160,200]:
        p_strong,_=simulate(n, B1_MDE, B3_MDE, sd, seed=n)
        p_mod,_=simulate(n, B1_MDE, B3_MOD, sd, seed=n+1)
        # ATE power: reject b1 — reuse simulate but test b1 via separate call
        p_ate=ate_power(n, B1_MDE, sd, seed=n+2)
        out["curves"][n]={"power_b3_strong":round(p_strong,3),"power_b3_moderate":round(p_mod,3),"power_ate":round(p_ate,3)}
        print(f"  {n:4d}   |   {p_strong:.2f}   |   {p_mod:.2f}   |   {p_ate:.2f}")
    json.dump(out, open('results/pruning_ab/mrt_formal/power_analysis.json','w'), indent=1)
    print("\nsaved power_analysis.json")

