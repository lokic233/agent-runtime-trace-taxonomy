#!/bin/bash
# Parallel phase runner for devgpu014 (384c/2.2TB, API-latency-bound cells -> high concurrency is cheap).
# Usage: PHASE=C MAXPAR=6 bash run_phase_parallel.sh
# Reads a cellspec (model|arm|rep) list for the phase, runs up to MAXPAR concurrently, resumes via DONE markers.
set -uo pipefail
GEN=/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy/harness/pruning_ab/generalization
ANTHRO_SHIM=/data/users/dengcchi/prune_ab/scripts/prune_shim_v2.py
GPT_SHIM=/data/users/dengcchi/prune_ab/scripts/prune_shim_plugboard_openai.py
PM_DIR=/data/users/dengcchi/prune_ab/scripts
REG=$GEN/configs/litellm_gpt5_registry.json
PHASE="${PHASE:?set PHASE=C|D|E}"; MAXPAR="${MAXPAR:-6}"; TASKSET="${TASKSET:-30}"
declare -A MODELSTR=( [opus47]="anthropic/claude-opus-4-7" [sonnet46]="anthropic/claude-sonnet-4-6" [haiku45]="anthropic/claude-haiku-4-5" [gpt55]="openai/gpt-5-5" )
INT10='^(pylint-dev__pylint-4551|pytest-dev__pytest-6197|sympy__sympy-14248|sphinx-doc__sphinx-8638|sphinx-doc__sphinx-9658|pylint-dev__pylint-6386|astropy__astropy-14096|sympy__sympy-19040|sympy__sympy-13091|pylint-dev__pylint-8898)$'

# build the cell list per phase: "modelkey arm rep"
CELLS=()
case "$PHASE" in
  C) OUT=/data/users/dengcchi/prune_ab/logs/xmodel_phaseC; FILTER="$INT10"
     for mk in sonnet46 haiku45; do for arm in C0_identity SHAM HYBRID1_m7_agg2; do for rep in 1 2 3 4 5; do CELLS+=("$mk $arm $rep"); done; done; done ;;
  D) OUT=/data/users/dengcchi/prune_ab/logs/xmodel_phaseD; FILTER="$INT10"
     for mk in opus47 sonnet46 haiku45; do for arm in C0_identity LINEDEDUP_e4 GENTLE6K_stable CAP1K_stable; do for rep in 1 2 3; do CELLS+=("$mk $arm $rep"); done; done; done ;;
  E) OUT=/data/users/dengcchi/prune_ab/logs/xmodel_phaseE
     FILTER=$(python3 -c "import json;j=json.load(open('/home/dengcchi/agent-runtime-trace-taxonomy/projects/agent-runtime-trace-taxonomy/results/pruning_ab/generalization/phaseE_task_split.json'));ids=j['phaseE_first30'] if '$TASKSET'=='30' else j['golden50'];print('^('+'|'.join(ids)+')\$')")
     # SAFETY GUARD: an empty/degenerate FILTER makes sweagent run the ENTIRE benchmark subset (runaway spend).
     if [[ -z "$FILTER" || "$FILTER" == '^()$' || $(echo "$FILTER" | grep -o '|' | wc -l) -lt 20 ]]; then
       echo "FATAL: Phase E FILTER invalid ('$FILTER') — refusing to run (would spend on wrong/all tasks)."; exit 3
     fi
     for mk in sonnet46 haiku45 gpt55; do for arm in C0_identity LINEDEDUP_e4 GENTLE6K_stable CAP1K_stable; do CELLS+=("$mk $arm t$TASKSET"); done; done ;;
esac
mkdir -p "$OUT"
echo "=== PHASE $PHASE PARALLEL (MAXPAR=$MAXPAR) cells=${#CELLS[@]} $(date +%H:%M:%S) ==="

run_cell(){
  local mk="$1" arm="$2" rep="$3" port="$4"
  local model="${MODELSTR[$mk]}"
  local tag ledger out done shim extra reg
  if [[ "$rep" == t* ]]; then tag="${mk}_${arm}_${rep}"; else tag="${mk}_${arm}_rep${rep}"; fi
  ledger="$OUT/ledger_${tag}.jsonl"; out="$OUT/run_${tag}"; done="$OUT/DONE_${tag}"
  [[ -f "$done" ]] && { echo "skip $tag"; return 0; }
  # RESUME-IN-PLACE: sweagent skips instances that already have a trajectory in --output_dir (redo_existing=False).
  # So on a re-run we PRESERVE the run dir -> completed tasks are skipped, only missing tasks run. This lets a
  # cell converge across intermittent external SIGKILLs (kill interval < full-cell runtime) instead of restarting
  # from zero every time. The ledger is append-mode; analyzers dedupe per task_id (last complete run wins), so we
  # keep it too. Only a FULLY-fresh cell (no run dir yet) starts clean.
  if [[ ! -d "$out" ]]; then rm -f "$ledger"; fi
  if [[ "$mk" == "gpt55" ]]; then shim="$GPT_SHIM"; extra="PB_PM_DIR=$PM_DIR"; reg="$REG"; else shim="$ANTHRO_SHIM"; extra=""; reg=""; fi
  env PB_SHIM_PORT=$port PB_LEDGER="$ledger" TS_PRUNE_METHOD="$arm" TS_MODEL="$model" $extra python3 "$shim" > "$OUT/shim_${tag}.log" 2>&1 &
  local sh=$!; sleep 3
  if ! curl -s "http://127.0.0.1:$port" >/dev/null 2>&1; then echo "SHIM DOWN $tag"; kill $sh 2>/dev/null; return 1; fi
  TS_MODEL="$model" TS_LITELLM_REGISTRY="$reg" timeout 9000 bash "$GEN/scripts/run_arm_xmodel.sh" "$arm" "$port" "$FILTER" "$out" 4 > "$OUT/arm_${tag}.log" 2>&1
  local rc=$?; kill $sh 2>/dev/null; sleep 1
  # count distinct tasks actually in the ledger + expected tasks from the FILTER
  local ntasks exp nterm
  ntasks=$(python3 -c "import json;print(len({json.loads(l).get('task_id') for l in open('$ledger')}))" 2>/dev/null || echo 0)
  exp=$(( $(echo "$FILTER" | grep -o '|' | wc -l) + 1 ))
  # count tasks that reached a TERMINAL exit status (submitted / exit_* / etc) in the batch exit-status file
  nterm=$(python3 -c "
import yaml,sys
try:
    d=yaml.safe_load(open('$out/run_batch_exit_statuses.yaml'))
    s=d.get('instances_by_exit_status',{}) or {}
    print(sum(len(v or []) for v in s.values()))
except Exception: print(0)
" 2>/dev/null || echo 0)
  echo "  done $tag rc=$rc rows=$(wc -l < "$ledger" 2>/dev/null||echo 0) tasks=$ntasks/$exp terminal=$nterm $(date +%H:%M:%S)"
  # DONE if all expected tasks present AND (rc=0 OR all tasks reached a terminal exit status).
  # rc=0+tasks guards against OOM-truncation; the terminal-status clause accepts complete cells whose
  # only failure was a teardown SIGKILL (rc=137 AFTER all 10 tasks finished = benign, no data loss).
  if [[ "$ntasks" -ge "$exp" ]] && { [[ $rc -eq 0 ]] || [[ "$nterm" -ge "$exp" ]]; }; then
    touch "$done"; [[ $rc -ne 0 ]] && echo "  ACCEPTED $tag despite rc=$rc (all $exp tasks terminal; teardown-only kill)"
  else
    echo "  INCOMPLETE $tag (rc=$rc tasks=$ntasks/$exp terminal=$nterm) -> no DONE, will re-run"
  fi
}

port=8600; running=0
for cell in "${CELLS[@]}"; do
  read mk arm rep <<< "$cell"
  port=$((port+1))
  run_cell "$mk" "$arm" "$rep" "$port" &
  running=$((running+1))
  if [[ $running -ge $MAXPAR ]]; then wait -n 2>/dev/null || wait; running=$((running-1)); fi
done
wait
# RETRY PASS: re-attempt any cell without a DONE marker (transient OOM/timeout), up to 2 extra rounds.
for retry in 1 2 3 4 5; do
  missing=()
  for cell in "${CELLS[@]}"; do
    read mk arm rep <<< "$cell"
    if [[ "$rep" == t* ]]; then tag="${mk}_${arm}_${rep}"; else tag="${mk}_${arm}_rep${rep}"; fi
    [[ -f "$OUT/DONE_${tag}" ]] || missing+=("$cell")
  done
  [[ ${#missing[@]} -eq 0 ]] && break
  echo "=== RETRY ROUND $retry: ${#missing[@]} incomplete cells $(date +%H:%M:%S) ==="
  running=0
  for cell in "${missing[@]}"; do
    read mk arm rep <<< "$cell"
    port=$((port+1))
    run_cell "$mk" "$arm" "$rep" "$port" &
    running=$((running+1))
    if [[ $running -ge $MAXPAR ]]; then wait -n 2>/dev/null || wait; running=$((running-1)); fi
  done
  wait
done
echo "=== PHASE $PHASE PARALLEL COMPLETE $(date +%H:%M:%S) DONE=$(ls $OUT/DONE_* 2>/dev/null|wc -l) ==="
