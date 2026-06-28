#!/bin/bash
# run_annotator.sh <annotator_id> <backend> <batch_idx> — annotate one batch of pilot traces.
ANN="$1"; BACKEND="$2"; BI="$3"
PROJ="/data/users/dengcchi/agent_runtime_proj/arttx_repo/projects/agent-runtime-trace-taxonomy"
OUT="/tmp/pilot_out_r2/${ANN}_b${BI}.json"; ERR="/tmp/pilot_out_r2/${ANN}_b${BI}.err"
PFILE="/tmp/pilot_out_r2/${ANN}_b${BI}.prompt.txt"
source /tmp/agentenv.sh 2>/dev/null
{
  cat "$PROJ/prompts/closed_label_annotator_v1.md"
  echo; echo "=== FROZEN-CANDIDATE TAXONOMY (you may ONLY use these labels) ==="
  cat /tmp/taxonomy_ref_v1.txt
  echo; echo "=== TRACES TO ANNOTATE (this batch) ==="
  cat /tmp/pilot_batches/b${BI}.json
  echo
  echo "Annotate EVERY trace in this batch. Output a JSON ARRAY of annotation records, one per"
  echo "trace, each validating against the annotation schema (sample_id=BOOT/PILOT-<trace_id>,"
  echo "workload_annotation, execution_state, waste_annotation with evidence_action_ids per label,"
  echo "primary_bottleneck, candidate_interventions, annotation_metadata with annotator_id='${ANN}',"
  echo "prompt_version='v1', abstain if unclear). Cite real [i] indices. Output ONLY the JSON array."
} > "$PFILE"
cd "$PROJ"
case "$BACKEND" in
  claude)   claude -p --max-turns 1 < "$PFILE" > "$OUT" 2>"$ERR" ;;
  codex)    codex exec --skip-git-repo-check - < "$PFILE" > "$OUT" 2>"$ERR" ;;
  gemini)   gemini -p "Annotate the traces per the protocol on stdin. Output ONLY the JSON array." < "$PFILE" > "$OUT" 2>"$ERR" ;;
esac
echo "DONE ${ANN} b${BI}: $(wc -c < "$OUT") bytes"
