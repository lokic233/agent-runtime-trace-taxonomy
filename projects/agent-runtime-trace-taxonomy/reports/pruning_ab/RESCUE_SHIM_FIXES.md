# MRT Rescue — Shim fixes that unblocked the live run (2026-07-01)

Two bugs prevented the shim from running on live SWE-agent traffic. Both are now fixed
in `scripts/mrt_rescue_shim.py` (sha256[:16]=`ae352c2efdb0769e`). 6/6 synthetic tests
still pass after these fixes.

## BUG 1 (fatal): tool normalization only ran on the experimental path

**Symptom:** every SWE-agent call crashed the batch with
`litellm ... KeyError: 'content'`. PlugBoard was returning
`{"type":"application_error","detail":"API Error: tools.0.custom.input_schema: Field required","status_code":400}`
and litellm's `extract_response_content` then indexed `completion_response["content"]`
which did not exist.

**Root cause:** SWE-agent 1.1.0 sends custom tools as
`{"type":"custom","name":...,"input_schema":{...}}`. PlugBoard's Anthropic endpoint
rejects the `type:"custom"` key alongside `input_schema`. The shim DID strip that key —
but **only inside the experimental-event branch**, after all the early `return` paths
(internal gate, seg_idx None, too-short segment, already-intervened, ineligible). So the
vast majority of calls (which take an early return) forwarded the un-normalized tools and
got a 400.

**Fix:** hoisted normalization into `_normalize_body(d)`, called once at the top of
`process_request` so **every** path (internal, ineligible, NO_OP, LINEDEDUP) gets:
- `del t["type"]` for custom tools carrying `input_schema`
- drop `top_p` when `temperature` present

After the fix: **0 bad responses** across 215 live calls (was 100% failing).

## BUG 2 (resilience): a single upstream error killed the whole batch

**Fix:** added a response guard in `do_POST`: if the PlugBoard response lacks a `content`
key, log it to `/tmp/shim_bad_resp.jsonl`, retry once, and only as a last resort synthesize
a minimal valid empty-assistant message so one transient upstream error can't crash a
multi-task batch. In the successful run this guard fired 0 times (kept for robustness).

## BUG 3 (ops): shim died on launch — two causes

1. `/tmp/launch_shim.sh` was being reaped by the tmp cleaner between write and exec
   (`No such file or directory`). Fix: launcher lives in `scripts/launch_rescue_shim.sh`.
2. Background `&` under the agent shell got SIGHUP'd on wrapper exit. Fix: `setsid ... < /dev/null &`.
3. Inherited `no_proxy` contained `[::1]` which crashes litellm/httpx on import
   (`Invalid port: ':1]'`). Fix: launcher unsets all proxy vars +
   `LITELLM_LOCAL_MODEL_COST_MAP=True`.

## Verification
- `python3 scripts/test_mrt_rescue_protocol.py` → 6/6 PASS
- Live run: 215 calls, 5 tasks, 2 protocol-conformant interventions, 0 bad responses, 0 crashes
