#!/bin/bash
set -uo pipefail
cd /data/users/dengcchi/prune_ab
source /usr/etc/profile.d/conda.sh 2>/dev/null
conda activate /data/users/dengcchi/hal_work/envs/swe-agent-1.0 2>/dev/null
for v in http_proxy https_proxy HTTP_PROXY HTTPS_PROXY no_proxy NO_PROXY; do unset $v; done
export MSWEA_DOCKER_EXECUTABLE=podman DOCKER_HOST="unix:///run/user/$(id -u)/podman/podman.sock"
export ANTHROPIC_API_KEY="shim" ANTHROPIC_BASE_URL="http://127.0.0.1:8912"
cd /data/users/dengcchi/hal_work/hal-harness/agents/SWE-agent-v1.0
sweagent run-batch --instances.type=swe_bench --instances.subset=verified --instances.split=test \
  --instances.evaluate=False --instances.deployment.container_runtime=podman \
  --instances.deployment.docker_args='--memory=4g' \
  --instances.filter="$1" \
  --config="config/benchmarks/250225_anthropic_filemap_simple_review.yaml" \
  --agent.model.name="anthropic/claude-opus-4-7" \
  --agent.model.api_base="http://127.0.0.1:8912" --agent.model.api_key="shim" \
  --agent.model.per_instance_cost_limit=0 --agent.model.per_instance_call_limit=75 \
  --agent.model.temperature=0.0 --num_workers="${2:-10}" \
  --output_dir="/data/users/dengcchi/prune_ab/arms/mrt_confirmatory_locked"
echo "CONFIRMATORY EXIT rc=$?"
