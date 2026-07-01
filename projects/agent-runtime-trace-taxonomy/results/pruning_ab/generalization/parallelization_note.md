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
