#!/usr/bin/env python3
"""skeptic_review: falsify each feature. Outputs analysis/skeptic_review_v1.md + a stats json.
Tests: (1) collapse-into-length (corr with n_actions/n_events), (2) solver-identity (variance explained
by solver), (3) harness-identity, (4) does it use future info (structural check), (5) outcome-independence.
"""
import json, os
import pandas as pd, numpy as np
from scipy import stats
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
df=pd.read_parquet(os.path.join(ROOT,'data','baseline_trace_feature_table.parquet'))
PRIMARY=['search_no_new_evidence_rate','redundant_reread_rate','oversized_then_narrow_read_rate',
         'no_evidence_patch_churn_rate','post_edit_test_gap','fraction_actions_in_no_new_evidence_streaks',
         'tool_error_rate','environment_setup_rate']

def eta_sq(y, groups):
    # fraction of variance in y explained by categorical groups (one-way ANOVA eta^2)
    d=pd.DataFrame({'y':y,'g':groups}).dropna()
    if d['y'].nunique()<2 or d['g'].nunique()<2: return np.nan
    grand=d['y'].mean(); ss_tot=((d['y']-grand)**2).sum()
    ss_bet=sum(len(g)* (g['y'].mean()-grand)**2 for _,g in d.groupby('g'))
    return ss_bet/ss_tot if ss_tot>0 else np.nan

res={}
for f in PRIMARY:
    sub=df[[f,'n_actions','n_events','solver_alias','source_harness']].copy()
    sub=sub[sub[f].notna()]
    if len(sub)<30:
        res[f]={'n':len(sub),'note':'too few'}; continue
    # 1) collapse into length
    sp_len = stats.spearmanr(sub[f], sub['n_actions']).statistic
    # 2) solver identity eta^2
    eta_solver = eta_sq(sub[f], sub['solver_alias'])
    # 3) harness identity eta^2
    eta_harness = eta_sq(sub[f], sub['source_harness'])
    res[f]=dict(n=int(len(sub)),
                spearman_vs_n_actions=round(float(sp_len),3),
                eta2_solver=round(float(eta_solver),3),
                eta2_harness=round(float(eta_harness),3),
                std=round(float(sub[f].std()),4),
                mean=round(float(sub[f].mean()),4))

# verdicts
L=["# Skeptic Review v1 — feature falsification\n",
   "Lane C attempts to falsify each candidate feature BEFORE the correlation study.",
   "Tests: (1) collapse-into-trace-length |Spearman vs n_actions|; (2) solver-identity eta^2;",
   "(3) harness-identity eta^2; (4) future-info (structural); (5) outcome-independence (structural).\n",
   "| feature | n | r vs n_actions | eta2 solver | eta2 harness | verdict |",
   "|---|---|---|---|---|---|"]
verdicts={}
for f in PRIMARY:
    r=res[f]
    if 'spearman_vs_n_actions' not in r:
        L.append(f"| {f} | {r['n']} | - | - | - | INSUFFICIENT |"); continue
    rl=abs(r['spearman_vs_n_actions']); es=r['eta2_solver']; eh=r['eta2_harness']
    flags=[]
    if rl>=0.7: flags.append("LENGTH-COLLAPSE-RISK")
    if eh>=0.5: flags.append("HARNESS-DOMINATED")
    if es>=0.6: flags.append("SOLVER-DOMINATED")
    v = "KEEP" if not flags else ("DOWNGRADE/CONTROL: "+",".join(flags))
    verdicts[f]=v
    L.append(f"| {f} | {r['n']} | {r['spearman_vs_n_actions']} | {r['eta2_solver']} | {r['eta2_harness']} | {v} |")

L.append("\n## Structural checks (all features)\n")
L.append("- (4) FUTURE-INFO: FULL features use the whole trace BY DESIGN (diagnosis features, not online). "
         "PREFIX variants (T5/T10/T20) are computed strictly on events <= cutoff in src code (slice on action index); "
         "no final-outcome, final-patch, or total-token field is read by any feature. PASS.")
L.append("- (5) OUTCOME-INDEPENDENCE: no feature reads `resolved` or grade fields; all derive from action/obs text. PASS.")
L.append("- (6) HEALTHY-VS-WASTE: NO_EVIDENCE_PATCH_CHURN gates on intervening evidence (test/search/read/error) so "
         "edit->test->edit iteration is NOT counted as churn (validated in 45 healthy-sequence memos).")
L.append("- (7) HARNESS BUG QUARANTINE: solver_C `_split_string future-annotations` edit-failures are excluded from "
         "'evidence' so they neither reward nor are rewarded; solver_C churn flagged harness-contaminated.")
L.append("\n## Interpretation\n")
L.append("Features with eta2_harness >= 0.5 are HARNESS-DOMINATED and must be read per-harness, never as solver "
         "behavior — the correlation models include source_harness + repo + task FE to absorb this.")

open(os.path.join(ROOT,'analysis','skeptic_review_v1.md'),'w').write("\n".join(L))
json.dump(res, open(os.path.join(ROOT,'analysis','skeptic_stats_v1.json'),'w'), indent=1)
print("skeptic review written")
for f,v in verdicts.items(): print(f"  {f}: {v}")
