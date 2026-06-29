#!/bin/bash
# Unified serial grading queue. Grades all ungraded cells one-at-a-time (no socket contention).
cd /data/users/dengcchi/prune_ab
source /usr/etc/profile.d/conda.sh 2>/dev/null || true

# wait until Phase 6 RUNS are done (no run_arm on 884x ports) so the socket is free
echo "[$(date +%H:%M)] waiting for Phase6 runs to finish..."
while pgrep -f 'run_arm.sh.*884' >/dev/null 2>&1; do sleep 30; done
echo "[$(date +%H:%M)] Phase6 runs done; starting serial grading"

# Phase 34 cells (re-grade the ungraded ones)
for tag in C0_identity_rep5 SHAM_rep1 SHAM_rep3 SHAM_rep4 SHAM_rep5 HYBRID1_m7_agg2_rep1 HYBRID1_m7_agg2_rep2 HYBRID1_m7_agg2_rep5; do
  [ -f results/pruning_ab/phase34/grade_$tag.json ] && continue
  [ -d "arms/phase34_$tag" ] || continue
  echo "[$(date +%H:%M)] grade phase34 $tag"
  bash scripts/grade_tagged.sh "arms/phase34_$tag" "$tag" > logs/phase34/grade_$tag.log 2>&1
  sleep 5
done

# Phase 6 arms
for tag in heldout_C0_identity heldout_HYBRID1_m7_agg2 heldout_SHAM; do
  [ -f results/pruning_ab/phase6/grade_$tag.json ] && continue
  [ -d "arms/phase6_$tag" ] || continue
  echo "[$(date +%H:%M)] grade phase6 $tag (167 tasks)"
  bash scripts/grade_tagged_p6.sh "arms/phase6_$tag" "$tag" > logs/phase6/grade_$tag.log 2>&1
  sleep 5
done
echo "[$(date +%H:%M)] GRADING QUEUE COMPLETE"
echo "phase34: $(ls results/pruning_ab/phase34/grade_*.json 2>/dev/null|wc -l)/15 | phase6: $(ls results/pruning_ab/phase6/grade_*.json 2>/dev/null|wc -l)/3"
