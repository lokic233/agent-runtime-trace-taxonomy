#!/bin/bash
# Autonomous driver (user GO=1 approved): wait for smoke to PASS gates, then run paid phases C->D->E
# sequentially, running each analyzer after its phase. Per-phase + per-cell resume markers. Logs everything.
# Honors the money gate: only runs because the user said "go". Checkpoints between phases.
set -uo pipefail
GEN=/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy/harness/pruning_ab/generalization
ROOT=/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy
SMOKE=/data/users/dengcchi/prune_ab/logs/xmodel_smoke
DRIVE_LOG=/data/users/dengcchi/prune_ab/logs/DRIVE_ALL.log
log(){ echo "=== [$(date +%H:%M:%S)] $*" | tee -a "$DRIVE_LOG"; }

# --- Stage 0: wait for smoke to finish (18 DONE) + relaunch gpt55 if the old-script cells failed ---
log "STAGE 0: waiting for Phase B smoke to complete (18/18)"
for i in $(seq 1 240); do   # up to ~4h
  done=$(ls $SMOKE/DONE_* 2>/dev/null | wc -l)
  running=$(pgrep -f run_smoke.sh | wc -l)
  if [[ "$done" -ge 18 ]]; then log "smoke 18/18 DONE"; break; fi
  if [[ "$running" -eq 0 ]]; then
    # orchestrator stopped with <18 -> gpt55 cells likely failed on old script; relaunch fixed
    log "smoke orchestrator stopped at $done/18 -> relaunching fixed orchestrator for remaining cells"
    cd "$ROOT"; source /tmp/agentenv.sh 2>/dev/null
    nohup bash "$GEN/scripts/run_smoke.sh" >> "$SMOKE/SMOKE_MAIN3.log" 2>&1 &
    sleep 30
  fi
  sleep 60
done
# run smoke gates
cd "$ROOT"; python3 "$GEN/analysis/smoke_gates.py" 2>&1 | tee -a "$DRIVE_LOG"
PASS=$(python3 -c "import json;print(json.load(open('$ROOT/results/pruning_ab/generalization/smoke_gates.json'))['all_gates_pass'])" 2>/dev/null)
log "smoke gates all_pass=$PASS"
if [[ "$PASS" != "True" ]]; then log "SMOKE GATES FAILED -> STOPPING (will not spend on C/D/E). Inspect smoke_gates.json."; exit 1; fi

# --- Stage 1: Phase C (cache tax, Sonnet+Haiku) ---
log "STAGE 1: Phase C cache-tax transport"
DRY_RUN=0 bash "$GEN/scripts/run_phaseC.sh" 2>&1 | tee -a "$DRIVE_LOG"
python3 "$GEN/analysis/analyze_cache_tax.py" 2>&1 | tee -a "$DRIVE_LOG"
log "Phase C complete + analyzed"

# --- Stage 2: Phase D (intelligence tax, Opus+Sonnet+Haiku) ---
log "STAGE 2: Phase D intelligence-tax scaling"
DRY_RUN=0 bash "$GEN/scripts/run_phaseD.sh" 2>&1 | tee -a "$DRIVE_LOG"
python3 "$GEN/analysis/analyze_intelligence_tax.py" 2>&1 | tee -a "$DRIVE_LOG"
log "Phase D complete + analyzed"

# --- Stage 3: Phase E30 (static policy, Sonnet+Haiku+gpt-5-5, 30 tasks) ---
log "STAGE 3: Phase E static-policy transport (30 tasks)"
DRY_RUN=0 TASKSET=30 bash "$GEN/scripts/run_phaseE.sh" 2>&1 | tee -a "$DRIVE_LOG"
python3 "$GEN/analysis/analyze_static_policy.py" 2>&1 | tee -a "$DRIVE_LOG"
log "Phase E30 complete + analyzed"

# consistency assertions over everything
python3 "$GEN/analysis/consistency_assertions.py" 2>&1 | tee -a "$DRIVE_LOG"
log "ALL PHASES (C,D,E30) COMPLETE. E50 expansion is a separate gated step after E30 review."
