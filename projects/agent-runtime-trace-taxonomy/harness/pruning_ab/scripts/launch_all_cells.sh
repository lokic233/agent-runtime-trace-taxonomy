#!/bin/bash
cd /data/users/dengcchi/prune_ab
LIVE=$(ss -tlnp 2>/dev/null | grep -oE ':88[0-9][0-9]' | tr -d ':' | sort -u)
fire() {
  M=$1; R=$2; P=$3
  echo "$LIVE" | grep -q "^$P$" && { echo "[up] $M rep$R $P"; return; }
  [ -f results/pruning_ab/phase34/grade_${M}_rep${R}.json ] && { echo "[graded] $M rep$R"; return; }
  pgrep -f "run_arm.sh $M $P" >/dev/null && { echo "[running] $M rep$R"; return; }
  # load gate
  while :; do L=$(cut -d' ' -f1 /proc/loadavg|cut -d. -f1); [ "$L" -lt 260 ] && break; sleep 15; done
  nohup bash scripts/run_cell.sh "$M" "$R" "$P" > logs/phase34/cell_${M}_rep${R}.log 2>&1 &
  echo "[FIRE] $M rep$R port $P"
  sleep 6
}
# SHAM rep1-5, HYBRID1 rep1-5
for R in 1 2 3 4 5; do fire SHAM $R $((8810+R)); done
for R in 1 2 3 4 5; do fire HYBRID1_m7_agg2 $R $((8820+R)); done
echo "ALL REMAINING CELLS FIRED $(date +%H:%M)"
