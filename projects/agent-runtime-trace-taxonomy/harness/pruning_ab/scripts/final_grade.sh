#!/bin/bash
cd /data/users/dengcchi/prune_ab
source /usr/etc/profile.d/conda.sh 2>/dev/null || true
export DOCKER_HOST="unix:///run/user/$(id -u)/podman/podman.sock"

capture() {
  # capture any completed reports sitting in cwd
  for f in prune_ab.ph34_*.json; do [ -f "$f" ] || continue; t=$(echo "$f"|sed 's/prune_ab.ph34_//;s/.json//'); cp "$f" results/pruning_ab/phase34/grade_$t.json 2>/dev/null; done
  for f in prune_ab.p6_*.json; do [ -f "$f" ] || continue; t=$(echo "$f"|sed 's/prune_ab.p6_//;s/.json//'); cp "$f" results/pruning_ab/phase6/grade_$t.json 2>/dev/null; done
}

grade_one() {  # grade ONE cell, wait for it to fully finish
  local KIND=$1 OUT=$2 TAG=$3
  echo "[$(date +%H:%M)] GRADE $TAG"
  if [ "$KIND" = p34 ]; then bash scripts/grade_tagged.sh "$OUT" "$TAG" > logs/phase34/grade_$TAG.log 2>&1
  else bash scripts/grade_tagged_p6.sh "$OUT" "$TAG" > logs/phase6/grade_$TAG.log 2>&1; fi
  capture
}

# wait for the 3 in-flight to clear
echo "[$(date +%H:%M)] waiting for in-flight gradings to clear..."
while [ "$(pgrep -f 'swebench.harness.run_evaluation'|wc -l)" -gt 0 ]; do capture; sleep 30; done
capture
echo "[$(date +%H:%M)] in-flight cleared. P34=$(ls results/pruning_ab/phase34/grade_*.json|wc -l)/15 P6=$(ls results/pruning_ab/phase6/grade_*.json|wc -l)/3"

# now grade remaining Phase34 cells SERIALLY (one fully completes before next)
for tag in SHAM_rep1 SHAM_rep3 SHAM_rep4 SHAM_rep5 HYBRID1_m7_agg2_rep1 HYBRID1_m7_agg2_rep2 HYBRID1_m7_agg2_rep5 C0_identity_rep5; do
  [ -f results/pruning_ab/phase34/grade_$tag.json ] && continue
  [ -d arms/phase34_$tag ] && grade_one p34 "arms/phase34_$tag" "$tag"
  sleep 3
done
# remaining Phase6 arms
for tag in heldout_C0_identity heldout_HYBRID1_m7_agg2 heldout_SHAM; do
  [ -f results/pruning_ab/phase6/grade_$tag.json ] && continue
  [ -d arms/phase6_$tag ] && grade_one p6 "arms/phase6_$tag" "$tag"
  sleep 3
done
capture
echo "[$(date +%H:%M)] FINAL GRADE COMPLETE P34=$(ls results/pruning_ab/phase34/grade_*.json|wc -l)/15 P6=$(ls results/pruning_ab/phase6/grade_*.json|wc -l)/3"
