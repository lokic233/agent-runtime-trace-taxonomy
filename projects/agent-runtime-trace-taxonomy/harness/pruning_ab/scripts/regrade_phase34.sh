#!/bin/bash
cd /data/users/dengcchi/prune_ab
source /usr/etc/profile.d/conda.sh 2>/dev/null || true
for tag in C0_identity_rep5 SHAM_rep1 SHAM_rep3 SHAM_rep4 SHAM_rep5 HYBRID1_m7_agg2_rep1 HYBRID1_m7_agg2_rep2 HYBRID1_m7_agg2_rep5; do
  [ -f results/pruning_ab/phase34/grade_$tag.json ] && { echo "[done] $tag"; continue; }
  OUT="arms/phase34_$tag"
  [ -d "$OUT" ] || { echo "[noout] $tag"; continue; }
  echo "[$(date +%H:%M)] regrade $tag"
  bash scripts/grade_tagged.sh "$OUT" "$tag" > logs/phase34/grade_$tag.log 2>&1
  n=$(python3 -c "import json,os;f='results/pruning_ab/phase34/grade_$tag.json';print(len(json.load(open(f)).get('resolved_ids',[])) if os.path.exists(f) else 'FAIL')" 2>/dev/null)
  echo "[$(date +%H:%M)] $tag -> $n"
  sleep 5
done
echo "SERIAL REGRADE DONE $(date +%H:%M)"
