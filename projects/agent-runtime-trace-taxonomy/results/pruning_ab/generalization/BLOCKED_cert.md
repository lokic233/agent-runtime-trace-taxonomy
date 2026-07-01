# BLOCKED (2026-07-01 ~03:15 PDT) — user x509 cert wiped by host maintenance

## What happened
cli:devgpu014 had a host maintenance/reprovision event ~01:41-02:34 (CLI disconnect + credential reset).
The user x509 cert `/var/facebook/credentials/dengcchi/x509/dengcchi.pem` (used by the prune shims for
PlugBoard mTLS) was WIPED — the whole `credentials/dengcchi/` tree was reset at 02:03, agent_x509 cert is
0 bytes, no kerberos ticket, only a host `server_dc.pem` remains. PlugBoard calls fail: APIConnectionError.

## State preserved (nothing lost)
- Phase C: 30/30 DONE — Q1 cache_tax SUPPORTED both tiers (cache_tax_transport.json committed).
- Phase D: 5/36 valid DONE cells (opus47 C0 rep1-3, LINEDEDUP rep1-2), all integrity-clean (10/10 tasks).
- Phase E: not started.
- Driver STOPPED (was burning retry-backoff on doomed calls). Incomplete Phase D partial (rep3) cleaned.

## Unblock (requires the USER — cannot self-fix)
Reissue the user x509 cert on devgpu014 (kerberos/Duo interactive auth — out of scope for the agent).
Once `/var/facebook/credentials/dengcchi/x509/dengcchi.pem` is valid again, resume:
  cd .../harness/pruning_ab/generalization/scripts && source /tmp/agentenv.sh
  systemd-run --user --unit=xmodel-driver --same-dir /data/users/dengcchi/prune_ab/launch_driver.sh
The DONE markers make it resume Phase D at cell 6 (skips the 30+5 done). The scheduled handler auto-resumes
when it detects the cert is back.
