#!/usr/bin/env python3
"""run_interaction_analysis.py — signal x intervention heterogeneity (Section 19). PENDING paired outcomes.
Pre-registered: outcome ~ CONFIG + baseline_signal + CONFIG:baseline_signal + C(task) + C(solver).
Primary interactions: SEARCH_CONSTRAINED x SEARCH_NO_NEW_EVIDENCE_RATE; PATCH_GUARD x NO_EVIDENCE_PATCH_CHURN_RATE;
VERIFY_HEAVY x POST_EDIT_TEST_GAP. Treatment effect by signal QUARTILE; token-saving/regression/improvement SEPARATELY."""
import os, json, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p=os.path.join(ROOT,"data","development_config_outcomes.jsonl")
rows=[json.loads(l) for l in open(p)] if os.path.exists(p) and os.path.getsize(p)>0 else []
emp=[r for r in rows if r.get("provenance")=="EMPIRICAL"]
print(f"PENDING: {len(emp)} EMPIRICAL paired outcomes -> no fabrication." if not emp else f"would analyze {len(emp)}")
