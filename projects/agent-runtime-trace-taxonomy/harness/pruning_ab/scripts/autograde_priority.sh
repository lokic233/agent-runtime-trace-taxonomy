#!/bin/bash
cd /data/users/dengcchi/prune_ab
# priority: C0 (baseline, needed for pairing) + the 3 gentle win-candidates
for round in $(seq 1 20); do
  for m in C0_identity GENTLE6K_stable GENTLE4K_stable SMARTGENTLE_stable CAP1K_stable CAP800_stable CAP500_stable SMART_stable COMBOSC_stable; do
    [ -f results/pruning_ab/stable/grade_$m.json ] && continue
    n=$(ls arms/stable_$m/*/*.pred 2>/dev/null|wc -l)
    [ "$n" -lt 44 ] && continue
    # only grade if <2 evals running (avoid thrash)
    while [ "$(pgrep -f 'swebench.harness.run_evaluation'|wc -l)" -ge 2 ]; do sleep 20; done
    echo "[$(date +%H:%M)] autograde $m ($n preds)" >> logs/autograde.log
    bash scripts/grade_stable.sh "arms/stable_$m" "$m" >> logs/autograde.log 2>&1
  done
  # done?
  g=$(ls results/pruning_ab/stable/grade_*.json 2>/dev/null|wc -l)
  [ "$g" -ge 9 ] && { echo "[$(date +%H:%M)] ALL 9 GRADED" >> logs/autograde.log; break; }
  sleep 60
done
