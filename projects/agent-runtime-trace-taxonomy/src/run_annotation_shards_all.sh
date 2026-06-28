#!/bin/bash
ANN="$1"; BACKEND="$2"
for bi in $(seq 0 9); do
  bash /tmp/run_annotator.sh "$ANN" "$BACKEND" "$bi"
done
echo "ALL DONE $ANN"
