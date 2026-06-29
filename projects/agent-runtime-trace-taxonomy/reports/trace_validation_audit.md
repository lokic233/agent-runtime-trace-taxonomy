# Trace Validation Audit (double-validation of all ~3,432 traces)

**Date:** 2026-06-28 (requested by owner) · read-only sweep across all 7 downloaded sets.

## Integrity — CLEAN
| set | model | files | valid JSON | zero-byte | unparseable |
|-----|-------|------:|-----------:|----------:|------------:|
| B | opus-4.5 | 500 | 500 | 0 | 0 |
| C | sonnet-3.5 | 500 | 500 | 0 | 0 |
| E | SWE-agent-LM-32B | 500 | 500 | 0 | 0 |
| G | Skywork-32B | 500 | 500 | 0 | 0 |
| H | EntroPO-30B | 500 | 500 | 0 | 0 |
| A | opus-4.7 | **466** | 466 | 0 | 0 |
| F | opus-4.6 | **466** | 466 | 0 | 0 |

The 5 downloaded sets are byte-clean and share the IDENTICAL 500 instances (0 missing/0 extra vs reference).

## FINDING: A & F missing the SAME 34 matplotlib instances
- **Not random**: all 34 are `matplotlib__matplotlib-*`, lost to `Uncaught DockerPullError` during the
  opus-4.7/4.6 live generation runs.
- A and F miss the EXACT same 34 (A∩F identical).
- **Root cause (diagnosed, NOT transient):** rootless-podman UID-mapping failure. The matplotlib images
  carry files with UIDs (~197609) exceeding the host subuid range (dengcchi: 1879048192:**65536**).
  Pull fails: `potentially insufficient UIDs or GIDs available in user namespace ... /testbed/build/qhull-2020.2`.
- **FIX (verified):** add `ignore_chown_errors = "true"` to `~/.config/containers/storage.conf`
  [storage.options.overlay]. Image 13989 then pulled successfully. This is the reusable fix for ANY
  SWE-bench matplotlib image on a rootless-podman box with a narrow subuid range.

## Action taken
Backfilling the 34 matplotlib instances for A (opus-4.7) and F (opus-4.6) to reach full 500 each, using
the original SWE-agent-v1.0 config + the still-running opus shim (port 8731, routes by model name).
Pre-pulling all 34 images with the chown fix, then filtered run-batch on the 34 instances.

## Impact on analysis (until backfill lands)
A/F lack matplotlib → task-mix imbalance vs B/C/E/G/H (which have all 34). Per-model comparison MUST use
matched-task analysis (already planned, Section 13) so the gap cannot skew raw label frequencies. After
backfill, A/F reach 500 and the imbalance is removed.
