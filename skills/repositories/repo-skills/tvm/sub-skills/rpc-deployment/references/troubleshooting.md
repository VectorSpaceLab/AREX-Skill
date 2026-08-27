# RPC Troubleshooting

## Connection failures

**Symptom:** `Connection refused` or timeout.

- Confirm server/tracker process is running on the host and port you used.
- Check firewall/container/network namespace boundaries.
- Verify direct server vs tracker route; `rpc.connect` and `connect_tracker`
  are different APIs.
- Increase timeout only after confirming the endpoint is reachable.

**Symptom:** Tracker query is empty or the key is missing.

- Confirm the server registered with the same tracker and key.
- Check server logs for registration failures.
- Use explicit `--port-end` ranges so the tracker/proxy binds expected ports.

## Key and session mismatch

**Symptom:** Tracker has devices but the client cannot obtain one.

- Match the requested key exactly.
- Check queue state and whether another job holds the device.
- Record `session_timeout` and release stale sessions when possible.

## Module upload/load failures

**Symptom:** `remote.upload` succeeds but `remote.load_module` fails.

- Confirm the artifact name you load matches the uploaded basename.
- Check remote runtime supports the artifact format and dependent shared
  libraries.
- Confirm the local compile target matches the remote architecture/runtime.

**Symptom:** Module loads but execution fails.

- Check device type: `remote.cpu()` vs `remote.cuda()` or another backend.
- Validate tensor shape, dtype, and device placement.
- Confirm backend-specific runtime support on the remote device.

## Timing and performance confusion

`time_evaluator` executes on the remote and excludes most network overhead, but
module upload and session setup are outside the measured kernel time. Do not
compare first-run end-to-end latency against `time_evaluator` output without
noting the difference.

## Meta-schedule RPC runner failures

If `tune_tir(..., runner="rpc")` fails, first validate a single upload/load/run
through this RPC route. Only then tune runner timeout, repeats, or task
scheduler settings.
