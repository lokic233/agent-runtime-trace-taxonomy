#!/bin/bash
# annotate_driver.sh <alias> — 2 annotators over all shards of a solver. Resumable.
ALIAS="$1"
PROJ="/data/users/dengcchi/agent_runtime_proj/arttx_repo/projects/agent-runtime-trace-taxonomy"
SHARDS="/tmp/ann_shards/$ALIAS"
OUT="$PROJ/annotations/raw_votes/full/$ALIAS"; mkdir -p "$OUT"
source /tmp/agentenv.sh 2>/dev/null
ANNPROMPT="$PROJ/prompts/closed_label_annotator_v1.md"
TAXREF="/tmp/taxonomy_ref_v1.txt"
mkprompt(){ # $1=shardfile
  { cat "$ANNPROMPT"; echo; echo "=== FROZEN v1 TAXONOMY (use ONLY these labels) ==="; cat "$TAXREF"
    echo; echo "=== TRACES TO ANNOTATE ==="; cat "$1"
    echo; echo "Output a JSON ARRAY, one annotation record per trace (schema-valid, evidence_action_ids per waste label, exactly one primary_bottleneck, annotator_id set, prompt_version=v1). JSON only."; }
}
for sf in "$SHARDS"/s*.json; do
  sid=$(basename "$sf" .json)
  for role in a1 a2; do
    of="$OUT/${sid}_${role}.json"
    [ -s "$of" ] && continue   # resume
    pf="/tmp/p_${ALIAS}_${sid}_${role}.txt"; mkprompt "$sf" > "$pf"
    case "$role" in
      a1) timeout 600 bash -c "cd $PROJ && codex exec --skip-git-repo-check - < '$pf'" > "$of" 2>/dev/null ;;
      a2) timeout 600 claude -p --max-turns 1 < "$pf" > "$of" 2>/dev/null ;;
    esac
    rm -f "$pf"
  done
done
echo "DONE $ALIAS"
