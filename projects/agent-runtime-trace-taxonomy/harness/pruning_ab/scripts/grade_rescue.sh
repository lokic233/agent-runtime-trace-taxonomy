#!/bin/bash
set -uo pipefail
source /usr/etc/profile.d/conda.sh 2>/dev/null || true
conda activate /data/users/dengcchi/hal_work/envs/hal 2>/dev/null || conda activate /data/users/dengcchi/hal_work/envs/swe-agent-1.0
export DOCKER_HOST="unix:///run/user/$(id -u)/podman/podman.sock"
export https_proxy=http://fwdproxy:8080 http_proxy=http://fwdproxy:8080
cd /data/users/dengcchi/prune_ab
python3 -m swebench.harness.run_evaluation \
  --dataset_name princeton-nlp/SWE-bench_Verified \
  --split test \
  --predictions_path results/pruning_ab/mrt_rescue/preds.jsonl \
  --max_workers 3 \
  --run_id mrt_rescue \
  --cache_level instance
echo "GRADE EXIT rc=$?"
