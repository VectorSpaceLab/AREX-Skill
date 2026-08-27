# Distributed Oracle API Reference

This reference records the distributed behavior implemented in the KerasTuner
checkout, especially `keras_tuner/distribute/utils.py`,
`oracle_client.py`, and `oracle_chief.py`. It describes the protocol; it does
not replace the normal tuner/search API.

## Environment contract

| Variable | Runtime use | Operational requirement |
| --- | --- | --- |
| `KERASTUNER_ORACLE_IP` | `has_chief_oracle()` activates distributed Oracle mode; both the client channel and chief bind address use it. | Set to the chief address. `127.0.0.1` is only useful when every participant is on the same host. |
| `KERASTUNER_ORACLE_PORT` | The client connects to and the chief binds `IP:PORT`. | Set the same available TCP port everywhere. The runtime utility raises `RuntimeError` if IP is present but port is missing. |
| `KERASTUNER_TUNER_ID` | Identifies the tuner in `CreateTrial`; role detection searches this value for `chief`. | Set a deliberate non-empty ID with the correct coordination scope. The runtime utility raises `RuntimeError` if IP is present but the ID is missing. |

The three variables are a single configuration unit. `has_chief_oracle()`
returns `False` when the IP key is absent, even if port or ID keys happen to be
present. The bundled `scripts/check_distributed_env.py` treats any partial set
as an error so that a typo cannot silently fall back to local mode. It checks
completeness only and does not validate reachability or start a server.

Role detection is literal and case-sensitive:

```python
has_chief_oracle()  # complete IP/port/ID contract is present
is_chief_oracle()   # distributed mode and "chief" in TUNER_ID
```

Consequently, an ID such as `chief`, `chief-0`, or `experiment-chief-a` is
chief-side. Avoid putting `chief` in a worker ID. If no ID contains that
substring, no process starts the chief service.

## `OracleClient`

`OracleClient(oracle)` wraps an existing Oracle on a worker. Its constructor
reads all three environment variables, creates
`grpc.insecure_channel(f"{ip}:{port}")`, creates the generated
`OracleStub`, and stores the tuner ID. The channel is not TLS-authenticated.

The module constant is:

```python
TIMEOUT = 60 * 60  # 3600 seconds
```

The client calls each RPC with `wait_for_ready=True` and `timeout=TIMEOUT`:

| Method | RPC | Result/reporting behavior |
| --- | --- | --- |
| `get_space()` | `GetSpace` | Returns a reconstructed `HyperParameters`. |
| `update_space(hyperparameters)` | `UpdateSpace` | Sends only when `should_report` is true. |
| `create_trial(tuner_id)` | `CreateTrial` | Gets the next serialized `Trial`; a `STOPPED` result means Oracle-triggered exit. |
| `update_trial(trial_id, metrics, step=0)` | `UpdateTrial` | Sends metrics only when reporting is enabled. A normal single-worker client returns the updated `Trial`; a non-reporting multi-worker client returns a local `RUNNING` placeholder after refreshing the space. |
| `end_trial(trial)` | `EndTrial` | Sends the final serialized trial only when reporting is enabled. |
| `get_trial(trial_id)` | `GetTrial` | Returns a reconstructed trial. |
| `get_best_trials(num_trials=1)` | `GetBestTrials` | Returns reconstructed best trials. |

Only the Oracle attributes `objective`, `max_trials`, `allow_new_entries`, and
`tune_new_entries` are exposed locally through `__getattr__`; an unknown
attribute raises `AttributeError`. Do not assume the worker has a complete
local Oracle state.

The client starts with `multi_worker = False` and `should_report = True`.
`Tuner` may set these flags from a supplied strategy's internal distribution
properties; when reporting is disabled, only the designated reporting worker
should update/end trials. The repository comments and tests identify the
chief worker in a multi-worker cluster as the reporter. The public `Tuner`
documentation still limits supported `distribution_strategy` values to
single-worker strategies, so treat multi-worker strategy handling as an
internal compatibility path, not a supported general deployment.

## `OracleServicer` and chief server

`OracleServicer(oracle)` exposes the generated service methods:

- `GetSpace` and `UpdateSpace` delegate to the local Oracle's search space.
- `CreateTrial` delegates to `oracle.create_trial(tuner_id)` and sets
  `stop_triggered` when the returned status is `STOPPED`.
- `UpdateTrial`, `EndTrial`, `GetTrial`, and `GetBestTrials` delegate to the
  corresponding Oracle operations and serialize the response.

`start_server(oracle)`:

1. Reads `KERASTUNER_ORACLE_IP` and `KERASTUNER_ORACLE_PORT`.
2. Creates a gRPC server with a one-thread executor.
3. Registers `OracleServicer` and calls `add_insecure_port(f"{IP}:{PORT}")`.
4. Starts the server and sleeps in a loop.
5. Once a `STOPPED` trial sets `stop_triggered`, waits until both
   `oracle.ongoing_trials` and `oracle.tuner_ids` are empty, then returns.

There is no explicit `server.stop()` call in this implementation. Let the
chief process/supervisor own final process cleanup after `start_server`
returns; do not treat return from the loop as a signal to delete shared search
artifacts immediately.

## BaseTuner search behavior

`BaseTuner` sets the Oracle project directory during construction and takes the
process's `KERASTUNER_TUNER_ID`, defaulting to `tuner0` when the variable is
absent. Once the complete distributed contract is present, a non-chief
`BaseTuner` replaces its local Oracle with `OracleClient`.

`search()` then follows two distinct paths:

- Chief: saves the Oracle, starts the server, and waits for the Oracle to signal
  the end of work.
- Worker: repeatedly calls `create_trial`; retries an `IDLE` response, exits on
  `STOPPED`, runs the trial, updates metrics, and ends the trial.

A chief must be present for this protocol to make progress. A client wait can
last up to the 60-minute per-RPC timeout when the chief is slow to start, but a
wrong endpoint or permanently missing server will eventually fail rather than
wait forever.

## Project and artifact paths

For `directory=D` and `project_name=P`, `BaseTuner.project_dir` is the shared
path `D/P`. Trial artifacts live below `project_dir/trial_<trial_id>`, and the
tuner state filename includes the process's tuner ID. The Oracle itself saves
and reloads only on non-worker/chief paths; workers still need the shared
project tree for their tuner state and model/checkpoint artifacts.

Use the same, writable, mutually visible directory and project name on every
participant. Prefer an absolute path or a consistently mounted shared volume.
A local disk with the same spelling on different hosts is not shared state.
