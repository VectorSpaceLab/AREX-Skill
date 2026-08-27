# Distributed Tuning Troubleshooting

Start with the safe checker:

```bash
python sub-skills/distributed-tuning/scripts/check_distributed_env.py
```

It reports completeness only. It does not start `OracleServicer`, connect to a
port, or prove that a filesystem is shared.

## Environment and role errors

### `RuntimeError` mentions `KERASTUNER_ORACLE_PORT`

**Cause:** `KERASTUNER_ORACLE_IP` is set but the port variable is absent.

**Fix:** Set the same non-empty `KERASTUNER_ORACLE_PORT` on the chief and every
worker, then rerun the checker. Do not paper over the error with a different
port on each process.

### `RuntimeError` mentions `KERASTUNER_TUNER_ID`

**Cause:** IP is set but the tuner ID is absent.

**Fix:** Set a deliberate ID on every process. Make the chief ID contain the
case-sensitive substring `chief`; keep worker IDs free of that substring and
unique at the independent coordination scope.

### The checker rejects a port/ID-only environment

**Cause:** The runtime utility keys distributed-mode detection off the IP key
and would otherwise silently treat port/ID-only state as local mode.

**Fix:** Treat all three variables as an atomic set. Remove all three for a
plain local search, or set all three for a distributed search.

### Every process behaves as a worker

**Cause:** No `KERASTUNER_TUNER_ID` contains `chief`, or the intended chief ID
was misspelled/capitalized differently.

**Fix:** Choose exactly one chief ID such as `chief` or `chief-0`. Verify the
actual environment immediately before constructing the tuner. Do not put
`chief` in a worker's descriptive ID.

### More than one process behaves as chief

**Cause:** More than one ID contains `chief`. Every such process tries to bind
the Oracle service.

**Fix:** Give one process a chief-containing ID and rename all other IDs. Check
for the substring, not just exact equality.

## Port and network failures

### Workers wait and then fail to reach the chief

**Likely causes:**

- the chief was not launched or exited early;
- workers use a different IP or port;
- `127.0.0.1` was used from a different host/container;
- the chief bound an address not reachable from workers;
- a firewall, security group, container network, or service policy blocks the
  TCP port; or
- another process owns the port.

**Fix:** From each worker host, verify route and TCP reachability to the
chief's address and reserved port using the environment's approved diagnostic
tools. Confirm the chief can bind that address. The KerasTuner client uses
`grpc.insecure_channel` and `wait_for_ready=True` with a 60-minute timeout; a
long wait is not proof that the endpoint is correct. Keep the endpoint on a
trusted network because this protocol is not TLS-authenticated.

### The chief starts but workers see incompatible RPC or serialization errors

**Likely cause:** Participants have different KerasTuner/protobuf generated
service versions or incompatible `grpcio` installations.

**Fix:** Use the same package checkout/version and compatible runtime
requirements on all participants. Keep `keras_tuner/protos` from the matching
installation; do not mix generated service modules from another release.

## Project state and result failures

### Workers reload empty or different state

**Cause:** `directory` or `project_name` differs, or the path is local to each
host instead of a shared writable mount.

**Fix:** Print/inspect `tuner.project_dir` on every participant and make it the
same shared path. Verify read/write visibility before starting the search.
The Oracle and trial artifacts are not synchronized merely because the path
strings match.

### The project disappears or a search restarts unexpectedly

**Cause:** A process constructed a tuner with `overwrite=True` while another
participant was using the same project. `BaseTuner` may remove an existing
project directory during construction.

**Fix:** Use `overwrite=False` for coordinated participants and perform any
intentional reset once, before launching the group. Restore from a preserved
copy if artifacts were deleted.

### Best models or checkpoints are missing on one host

**Cause:** Trial files were written to a non-shared local directory, or a
worker was stopped before its trial artifacts were flushed.

**Fix:** Use a shared writable artifact path and wait for workers to finish.
Do not remove the project directory until result inspection and model loading
are complete.

## Stalls, status, and reporting

### A worker spins on `IDLE`

`BaseTuner.search()` retries an `IDLE` response while the Oracle is calculating.
This can be normal briefly. If it persists, inspect the chief logs, ongoing
trials, and shared project state rather than starting another chief.

### A worker does not send expected metrics

`OracleClient.update_space` and `end_trial` are no-ops when `should_report` is
false. `update_trial` also avoids the RPC and returns a local `RUNNING` trial
placeholder after refreshing the search space when reporting is disabled. This
is intentional for a reporting-only chief worker in the internal multi-worker
strategy path.

The public `Tuner` contract supports only single-worker distribution strategies.
For supported single-worker distributed Oracle coordination, the normal client
starts with `should_report=True`; check that a custom integration did not
mutate it and that the worker is not accidentally treated as a non-reporting
strategy member.

### The chief exits while workers are still running

`OracleServicer` marks a stop request when `CreateTrial` returns `STOPPED`, but
`start_server` waits for both `oracle.ongoing_trials` and `oracle.tuner_ids` to
empty before returning. Do not terminate the chief process or delete the
shared directory during this drain period.

### A process hangs for about an hour

Each OracleClient RPC uses `wait_for_ready=True` and a 3600-second timeout.
This is intended to cover a slow chief startup and to prevent indefinite hangs,
not to mask a bad deployment. Check role assignment, endpoint, port access,
chief lifetime, and package compatibility before waiting for the timeout.

## Cleanup and test-only helpers

`start_server` breaks its wait loop after the stop/drain condition but does not
explicitly call `server.stop()`. Let the process supervisor finish chief
cleanup after the function returns. Preserve the project tree and logs until
all workers have exited.

`keras_tuner.test_utils.mock_distribute` is not a fix for production failures.
It uses `portpicker`, thread-local mocked environment state, and exception
collection for tests; it does not provide a real multi-host network, shared
storage, process isolation, authentication, or service lifecycle. Do not add
it to deployment requirements or import it from an application.
