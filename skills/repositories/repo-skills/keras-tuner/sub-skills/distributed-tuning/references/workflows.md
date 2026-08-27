# Distributed Tuning Workflows

These workflows use the repository's chief/worker Oracle protocol. Replace
`search_program.py` with the application that constructs the same tuner and
search on every participant. Do not import or call
`keras_tuner.test_utils.mock_distribute` in production.

## 1. Preflight without starting a service

Run the bundled checker in the exact environment that will launch each
process:

```bash
python sub-skills/distributed-tuning/scripts/check_distributed_env.py
```

The command succeeds in ordinary local mode when all three variables are
absent, succeeds in distributed mode only when all three are non-empty, and
returns a nonzero status for a partial set. It does not import gRPC,
construct a tuner, bind a port, or make a network request.

For a distributed launch, confirm these values before proceeding:

- the IP is reachable from every worker and is the address on which the chief
  can bind;
- the TCP port is reserved for this search and permitted by host/container
  firewall rules;
- each participant can read and write the same `directory/project_name`; and
- all participants use compatible KerasTuner and protobuf/gRPC environments.

## 2. Launch one chief and workers

Choose a stable address for the chief and set the same IP and port on every
process. The chief ID must contain `chief`; worker IDs must not contain that
substring. The values below are replaceable examples: set `CHIEF_IP` to the
reachable chief address (the illustrative value `10.0.0.12` is not universal),
set `SHARED_DIR` to a writable shared mount (the illustrative `/shared/kt` is
not universal), and reserve the chosen port before running them.

```bash
# Chief process; replace these example values for your deployment.
CHIEF_IP="10.0.0.12"  # replace with <CHIEF_IP>
SHARED_DIR="/shared/kt"  # replace with <SHARED_DIR>
export KERASTUNER_ORACLE_IP="$CHIEF_IP"
export KERASTUNER_ORACLE_PORT=50051  # replace if this port is not reserved
export KERASTUNER_TUNER_ID=chief
python search_program.py --directory "$SHARED_DIR" --project-name sweep
```

Launch each worker with the same endpoint and project arguments, but a
coordination-scoped ID:

```bash
# Worker process 0; use the same replaceable IP/port/shared directory.
CHIEF_IP="10.0.0.12"  # replace with <CHIEF_IP>
SHARED_DIR="/shared/kt"  # replace with <SHARED_DIR>
export KERASTUNER_ORACLE_IP="$CHIEF_IP"
export KERASTUNER_ORACLE_PORT=50051  # replace if this port is not reserved
export KERASTUNER_TUNER_ID=worker-0
python search_program.py --directory "$SHARED_DIR" --project-name sweep

# Worker process 1 uses worker-1, and so on.
```

The application should construct the same Oracle/tuner configuration on all
participants. The environment selects the RPC role; it does not replace the
normal `Tuner` or `BaseTuner` construction. Run one chief only. A second ID
containing `chief` would also attempt to bind the service and normally collide
on the port.

Use unique IDs for independent tuner processes or groups. The test helper
comments that processes belonging to one TensorFlow multi-worker strategy may
need the same group ID, while its simple mock workers use `worker0`, `worker1`,
and so on. Follow the actual backend's grouping convention, but never reuse a
coordination ID accidentally across independent searches.

Pass the same shared `directory` and `project_name` everywhere, for example.
The illustrative `/shared/kt` path below must be replaced with a writable
shared mount visible to every participant; use a deployment-specific
`<SHARED_DIR>` rather than writing into the skill source tree:

```python
import keras_tuner as kt

shared_dir = "/shared/kt"  # replace with <SHARED_DIR>
tuner = kt.RandomSearch(
    hypermodel=build_model,
    objective="val_loss",
    max_trials=20,
    directory=shared_dir,
    project_name="sweep",
    overwrite=False,
)
tuner.search(x_train, y_train, validation_data=(x_val, y_val), epochs=1)
```

The resulting project directory is `directory/project_name`. It contains
Oracle/tuner state, trial directories, and model/checkpoint artifacts. Use a
filesystem that provides visibility and compatible locking/rename behavior to
all hosts; identical local paths do not suffice. Avoid `overwrite=True` on
workers or on multiple processes: construction may remove the existing project
directory.

The chief is the authoritative Oracle owner. Workers should not be expected
to reconstruct the entire Oracle from their local disk. They need the shared
artifact tree for the tuner state and any files their trial code writes or
later loads.

## 4. Understand the search loop and reporting

After construction:

1. The chief saves the Oracle and starts `OracleServicer`.
2. Each worker's `OracleClient` obtains the search space and requests trials.
3. An `IDLE` trial response means retry the request; it is not a completed
   trial.
4. A `RUNNING` trial is executed locally. Metrics and the final trial status
   are sent back through the client when reporting is enabled.
5. A `STOPPED` response means the Oracle has no more work for that tuner; the
   worker exits its loop.
6. The chief observes the Oracle's ongoing trials and tuner IDs before its
   server loop returns.

The client uses insecure gRPC and `wait_for_ready=True` with a 3600-second
per-request timeout. A client may therefore start before the chief and wait
through a startup race, but it cannot correct a bad IP, wrong port, blocked
firewall, or absent chief. Keep the chief alive until all workers have ended.

For an internal multi-worker strategy path, `Tuner` sets Oracle reporting
flags from the strategy's `should_checkpoint` property so only the reporting
worker sends updates. The supported public `Tuner` strategy contract remains
single-worker; do not use these flags as evidence that arbitrary multi-worker
training is supported.

## 5. Orderly completion and cleanup

Use this sequence:

1. Let the Oracle issue `STOPPED` after the configured search is exhausted or
   otherwise stopped.
2. Let every worker finish its current RPC/trial and exit its search loop.
3. Let the chief wait until `ongoing_trials` and `tuner_ids` are empty.
4. After `start_server` returns, let the chief process/supervisor terminate
   the process. The implementation does not explicitly call `server.stop()`.
5. Retain the shared project tree for result inspection, reload, or model
   loading. Delete it only after every participant has stopped and no later
   workflow needs its artifacts.

If a worker is intentionally terminated, first determine whether its trial is
still registered with the Oracle. Abruptly killing the chief can leave workers
waiting for the gRPC timeout and can prevent the drain condition from being
observed. Preserve logs and the project directory while diagnosing such a
failure.

## 6. Local protocol smoke checks versus real deployment

The distributed tests use `mock_distribute.mock_distribute(...)` to assign
thread-local environment dictionaries, create a local test port, run a chief
thread and worker threads, and re-raise thread exceptions. This is useful for
checking role detection, RPC serialization, trial status, and error handling.
It does not supply a production network, shared filesystem, process manager,
TLS, or deployment cleanup. A real smoke run must use separate processes and
the same endpoint and shared project directory that the final deployment will
use.
