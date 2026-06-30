#!/usr/bin/env python3
import json, os, statistics as st
BASE="/data/users/dengcchi/prune_ab"
G=set(json.load(open("/tmp/golden50.json")))
fails=[]
def chk(name, cond, detail):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}: {detail}")
    if not cond: fails.append(name)

# 1. baseline C0 = 46 resolved
c0r=len(set(json.load(open(f"{BASE}/results/pruning_ab/stable/grade_C0_identity.json")).get("resolved_ids",[]))&G)
chk("C0_baseline_46", c0r==46, f"stable C0 resolved={c0r} (expect 46)")

# 2. cache tax: HYBRID cc-fraction >> C0
me=json.load(open(f"{BASE}/results/pruning_ab/mechanism_effects.json"))
hyb=me["cache_tax"]["HYBRID1_m7_agg2"]["cc_fraction_mean"]; c0cc=me["cache_tax"]["C0_identity"]["cc_fraction_mean"]
chk("cache_tax_direction", hyb>0.5 and c0cc<0.15, f"HYBRID cc-frac={hyb} C0={c0cc}")

# 3. intelligence tax: destructive coef > 0
it=me["intelligence_tax_dose_controlled"]
chk("intel_tax_destructive", it["ols_destructive_coef"]>0.2, f"destructive coef={it['ols_destructive_coef']}, dose coef={it['ols_dose_coef']}")

# 4. oracle gap > best static
pol=json.load(open(f"{BASE}/results/pruning_ab/controller_policies.json"))
c0t=pol["c0_total"]; oracle=100*(c0t-pol["oracle_posthoc"])/c0t; static=100*(c0t-pol["always_GENTLE6K"])/c0t
chk("oracle_gap_exists", oracle>static+10, f"oracle={oracle:.1f}% best_static={static:.1f}%")

# 5. controller does NOT beat static
best_dup=max(100*(c0t-pol[k])/c0t for k in pol if k.startswith("dup>"))
chk("controller_not_supported", best_dup<static, f"best dup-policy={best_dup:.1f}% < best_static={static:.1f}%")

# 6. success-CATE HYBRID ~0
sc=json.load(open(f"{BASE}/results/pruning_ab/success_cate_repeated.json"))
chk("success_cate_hyb_near0", abs(sc["success_cate_hyb_vs_c0"])<0.1, f"HYB success-CATE={sc['success_cate_hyb_vs_c0']}")

# 7. SHAM negative control validates (success-CATE ~0)
chk("sham_control_valid", abs(sc["success_cate_sham_vs_c0"])<0.1, f"SHAM success-CATE={sc['success_cate_sham_vs_c0']}")

print(f"\n{'ALL ASSERTIONS PASS' if not fails else 'FAILURES: '+str(fails)}")
json.dump({"all_pass":len(fails)==0,"fails":fails}, open(f"{BASE}/results/pruning_ab/consistency_assertions.json","w"),indent=1)
