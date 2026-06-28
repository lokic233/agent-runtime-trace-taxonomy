#!/bin/bash
# run_open_coder.sh <coder_id> <backend> — independent open-coding over all 60 traces.
CODER="$1"; BACKEND="$2"
PROJ="/data/users/dengcchi/agent_runtime_proj/arttx_repo/projects/agent-runtime-trace-taxonomy"
OUT="/tmp/oc_out/${CODER}.json"; ERR="/tmp/oc_out/${CODER}.err"
PFILE="/tmp/oc_out/${CODER}.prompt.txt"
source /tmp/agentenv.sh 2>/dev/null
{
  echo "You are open-coding researcher '${CODER}'. Follow this protocol EXACTLY:"
  echo
  cat "$PROJ/prompts/taxonomy_open_coder_v1.md"
  echo
  echo "You are given 60 blinded traces in 3 JSON batches. Each trace: trace_id, task_id,"
  echo "repo, solver_alias, capability_tier, issue_head, deterministic features, truncated"
  echo "action/observation transcript (event indices [i])."
  echo; echo "BATCH 0:"; cat /tmp/oc_batches/batch_0.json
  echo; echo "BATCH 1:"; cat /tmp/oc_batches/batch_1.json
  echo; echo "BATCH 2:"; cat /tmp/oc_batches/batch_2.json
  echo
  echo "Produce your output as a SINGLE valid JSON object: keys coder_id, patterns (6-12"
  echo "crisp distinguishable waste pattern objects per the schema), workload_notes,"
  echo "uncovered_patterns, needs_unavailable_info, outcome_collapse_risks,"
  echo "false_positive_examples, justified_repeat_examples. Output ONLY the JSON, no prose."
  echo "Cite real trace_ids and [i] indices as evidence."
} > "$PFILE"

cd "$PROJ"  # codex trusted-dir + git-repo check
case "$BACKEND" in
  claude)   claude -p --max-turns 1 < "$PFILE" > "$OUT" 2>"$ERR" ;;
  codex)    codex exec --skip-git-repo-check - < "$PFILE" > "$OUT" 2>"$ERR" ;;
  gemini)   gemini -p "Read the open-coding task on stdin and output ONLY the JSON object." < "$PFILE" > "$OUT" 2>"$ERR" ;;
  metacode) metacode -p < "$PFILE" > "$OUT" 2>"$ERR" ;;
esac
echo "DONE ${CODER}/${BACKEND}: $(wc -c < "$OUT") bytes out, $(wc -l < "$ERR") err lines"
