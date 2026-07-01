# Parallelization assessment (devvm14202) — DEFERRED

User offered 5 extra nodes for parallel PlugBoard runs. Surveyed all:
- devvm14202: BEST candidate — cert + conda swe-agent env + hal-harness + podman + 96c/235G. Provisioned
  (scripts synced hash e35b6fbc, repo cloned, 35 eval images + base python images pre-pulled).
- devgpu002: cert+podman but NO hal-harness/conda env (fresh box).
- devgpu499: env+harness but NO cert.
- devvm14382: (the CPU build box, not surveyed for this).
- dengcchi-mac: not surveyed (laptop).

BLOCKER on devvm14202: SWE-agent builds a DERIVED image per task (`podman build` installing wget/gcc/make
via apt). That apt-get fails inside the build container: fwdproxy resolves ONLY to IPv6 (2401:db00:...),
and the build namespace cannot reach it (Could not resolve 'fwdproxy' / IPv6 connection failed). devgpu014
works because it has 429 pre-BUILT (<none>) derived image layers cached from the frozen study; devvm14202
would need to build them, which needs apt-over-proxy in the build namespace = a real IPv6/DNS rabbit hole.

DECISION: DEFER parallelization. The primary node devgpu014 runs reliably. Chasing IPv6-proxy-in-podman-build
violates "keep blast radius small" for a marginal speedup. Fallback if runtime becomes prohibitive: transfer
built images via `podman save | podman load` devgpu014 -> devvm14202 (heavy, ~GB, but bypasses the build).
Serial on devgpu014 is the chosen path.

## UPDATE: intra-node parallelism (the actual win)
Cross-node parallelism was the wrong lever. devgpu014 = 384 cores / 2.2TB RAM, running SERIAL 4-worker
cells at only ~30% util. Cells are API-latency-bound (~0.5 calls/sec), so concurrency is nearly free.
run_phase_parallel.sh runs MAXPAR=6 cells concurrently (distinct ports/ledgers/shims) -> ~5-6x speedup
(serial ~32hr -> ~6-7hr). BUG found+fixed live: the shim appends to its ledger, so a killed cell's partial
ledger would get fresh rows appended on re-run (corruption). Fixed: rm stale ledger/run before each non-DONE
cell. Verified: all re-launched cells have clean single-run ledgers (maxgap <=4s, no stale prefix).
LESSON (answering the user's node nudges): the bottleneck was utilization, not node count. The Mac (arm64,
no runtime, no cert) and devvm14202 (IPv6-proxy build wall) were both dead ends; the 384-core primary box
was the answer all along.

## OOM tuning: MAXPAR=6 too aggressive -> MAXPAR=3
MAXPAR=6 caused container-cgroup OOM (rc=137): the frozen --memory=10g per-container limit is fine SERIALLY
(each cell bursts into the free host) but under 6 concurrent cells x their task-containers, memory-heavy tasks
(esp. HYBRID1, which expands/rewrites context) exceed 10g and get SIGKILLed (rc=137, no DONE). Host was NOT
starved (1.4TB free) — it's the per-container cgroup. Load also hit 438 (>384 cores). FIX: MAXPAR=3 (kept the
frozen --memory=10g untouched — it's a treatment-adjacent frozen param). Result: load 438->67, cells complete.
DONE-marker resume preserved the 7 valid cells; OOM'd partials cleaned + re-run. ~3x speedup (vs 5-6x at MAXPAR=6
but without drops) = net faster since OOM'd cells don't waste work. Lesson: concurrency limited by per-container
memory, not host cores.

## Launch persistence: systemd user service (survives CLI disconnect)
The driver kept dying: nohup/setsid launches were killed when the Navi CLI session dropped, and even the
tool-framework `background:true` process died when devgpu014's CLI disconnected (~01:41, Phase D stuck 5/36).
FIX: launch via `systemd-run --user --unit=xmodel-driver /data/users/dengcchi/prune_ab/launch_driver.sh` —
a transient USER-scope systemd service owned by user@.service, independent of any SSH/CLI session. Survives
disconnects. Restart: `systemctl --user reset-failed xmodel-driver; systemd-run --user --unit=xmodel-driver ...`.
This is the durable launch method for all long autonomous runs on a CLI node.
