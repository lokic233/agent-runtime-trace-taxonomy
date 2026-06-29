#!/bin/bash
# run_arm.sh <method> <port> <filter_regex> <out_dir> <nworkers> — exact clone of run_model_full.sh + filter/port
set -uo pipefail
source /usr/etc/profile.d/conda.sh 2>/dev/null || source /etc/profile.d/conda.sh 2>/dev/null || true
conda activate /data/users/dengcchi/hal_work/envs/swe-agent-1.0
# CRITICAL: the inherited NO_PROXY contains [::1] which breaks litellm/httpx ("Invalid port: ':1]'").
# Clear ALL proxy env; the shim does its own mTLS egress (curl --noproxy *), agent->shim is pure localhost.
for v in http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy NO_PROXY all_proxy ALL_PROXY; do unset $v; done
export MSWEA_DOCKER_EXECUTABLE=podman
export DOCKER_HOST="unix:///run/user/$(id -u)/podman/podman.sock"
export PYTHONPATH="/data/users/dengcchi/hal_work/pyhooks:${PYTHONPATH:-}"
cd /data/users/dengcchi/hal_work/hal-harness/agents/SWE-agent-v1.0
METHOD="$1"; PORT="$2"; FILTER="$3"; OUT="$4"; NW="${5:-4}"
export ANTHROPIC_API_KEY="shim" ANTHROPIC_BASE_URL="http://127.0.0.1:$PORT"
CONFIG="config/benchmarks/250225_anthropic_filemap_simple_review.yaml"
mkdir -p "$OUT"
echo "=== ARM $METHOD port=$PORT out=$OUT nw=$NW ==="
sweagent run-batch \
  --instances.type=swe_bench --instances.subset=verified --instances.split=test \
  --instances.evaluate=False --instances.deployment.container_runtime=podman \
  --instances.deployment.docker_args='--memory=10g' \
  --instances.filter="$FILTER" \
  --config="$CONFIG" \
  --agent.model.name="anthropic/claude-opus-4-7" \
  --agent.model.api_base="http://127.0.0.1:$PORT" --agent.model.api_key="shim" \
  --agent.model.per_instance_cost_limit=0 --agent.model.per_instance_call_limit=75 \
  --agent.model.temperature=0.0 --num_workers="$NW" \
  --output_dir="$OUT"
echo "=== ARM $METHOD EXIT rc=$? ==="
