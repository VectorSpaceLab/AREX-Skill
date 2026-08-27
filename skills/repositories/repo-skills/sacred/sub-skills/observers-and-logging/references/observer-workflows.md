# Observer workflows

## Purpose

Read this when adding storage or notification behavior to a Sacred 0.8.7 experiment, deciding which observer fits the environment, or inspecting the files produced by a local observed run.

## Choose an observer

| Observer | Best fit | Required packages/services | Verification stance |
|---|---|---|---|
| `FileStorageObserver` | Local, no-service experiment records; temporary validation; human-inspectable JSON and copied files. | Base Sacred install and a writable filesystem directory. Optional `mako` only if rendering templates. | Verified locally by the bundled probe. |
| `MongoObserver` | Queryable central run store with GridFS for files and a separate metrics collection. | `pymongo`, `gridfs`, reachable MongoDB, and any needed authentication. | Optional; package/service must be checked in the target environment. |
| `QueuedMongoObserver` | Long runs where MongoDB may be temporarily unavailable. | Same as Mongo plus background queue semantics. | Optional; verify service and retry behavior before relying on it. |
| `SqlObserver` | SQL-backed metadata and files, including SQLite URLs for local cases. | `sqlalchemy` and a valid SQLAlchemy database URL; remote databases may need drivers and credentials. | Optional; run only after installing the required SQL stack. |
| `TinyDbObserver` + `TinyDbReader` | Local JSON database with hash-addressed files and query/readback support. | `tinydb`, `tinydb-serialization`, and `hashfs`. | Optional; import and tiny write/read checks are required before claiming support. |
| `QueueObserver` | Background, retrying wrapper around another observer. | No extra package beyond the covered observer. | Useful for flaky services, but it retries forever on persistent failures. |
| `S3Observer` | Store FileStorage-like run records in an S3 bucket prefix. | `boto3`, AWS credentials, region configuration, bucket permissions, and network access. | Optional; not verified without credentials/service access. |
| `GoogleCloudStorageObserver` | Store FileStorage-like run records in a Google Cloud Storage bucket prefix. | `google-cloud-storage`, valid Google credentials, existing bucket permissions, and network access. | Optional; not verified without credentials/service access. |
| `SlackObserver` | Send completion/interruption/failure messages to Slack. | `requests` and a Slack incoming-webhook URL. | Optional; never expose webhook URLs. |
| `TelegramObserver` | Send start/completion/interruption/failure messages to a Telegram chat. | `python-telegram-bot`, a bot token, a chat ID, and optional proxy configuration. | Optional; never expose bot tokens. |
| Neptune integration | Send run metadata to Neptune UI through the external Neptune Sacred integration. | `neptune-client`, `neptune-sacred`, project name, and API token. | External integration; verify in the target environment before claiming it works. |

## Add local file storage from Python

Use this for safe, local validation and for tasks where a future agent needs to inspect JSON files directly:

```python
from pathlib import Path
from sacred import Experiment
from sacred.observers import FileStorageObserver

ex = Experiment("observed-demo")
ex.observers.append(FileStorageObserver(Path("runs")))

@ex.main
def main(_run):
    _run.info["phase"] = "started"
    _run.log_scalar("demo.loss", 0.5, step=1)
    return 1

run = ex.run()
assert run.status == "COMPLETED"
```

Attach observers before `ex.run()` or `ex.run_commandline()`. If multiple observers are present, Sacred sorts them by descending `priority`. The first observer that sees `_id=None` chooses the run ID, then every later observer receives that ID.

## Inspect a FileStorageObserver run directory

A typical local file observer tree looks like this:

```text
runs/
  1/
    config.json      # final run configuration
    cout.txt         # captured stdout/stderr accumulated by heartbeats
    info.json        # small custom info, only created after info is non-empty
    metrics.json     # scalar metrics, only created after metrics are logged
    run.json         # status, times, host, experiment, resources, artifacts, result
    output.txt       # example artifact copied into the run directory
  _resources/
    input_<md5>.txt  # resource copy when resource copying is enabled
  _sources/
    script_<md5>.py  # source snapshot when source copying is enabled
```

Run directory names are numeric when Sacred assigns the ID itself. If a run ID is supplied explicitly, the directory name is that ID and creation fails if it already exists.

Key `run.json` fields to inspect:

- `status`: `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `INTERRUPTED`, `TIMED_OUT`, or a custom Sacred interruption status.
- `start_time`, `stop_time`, `heartbeat`: UTC timestamps serialized as strings by file-like observers.
- `config`: stored separately in `config.json`; `run.json` records status and bookkeeping.
- `experiment`: experiment name, base information, dependencies, source list, and repository information if Git collection is enabled.
- `resources`: entries for files read by the run, usually `[original_filename, stored_filename]` for file storage.
- `artifacts`: names of output files copied into the run directory by file storage.
- `meta`: initial metadata such as comments, priority, command, options, and named configs.

## Log custom info

Use `info` for small JSON-like status, curves summaries, dataset identifiers, and bookkeeping that should be visible during a running experiment:

```python
@ex.main
def main(_run):
    _run.info["dataset"] = {"name": "tiny", "rows": 3}
    ex.info["stage"] = "fit"  # same run info dict, only valid during a run
```

`ex.info` is a shortcut to the current run's info dictionary and only works while the experiment is running. For MongoDB and JSON-based observers, keep info values JSON/BSON-friendly. Numpy arrays and pandas objects receive special conversions only when those optional packages are installed.

## Log scalar metrics

Use metrics for numerical series:

```python
@ex.main
def main(_run):
    for step, value in enumerate([0.9, 0.7, 0.6]):
        _run.log_scalar("train.loss", value, step=step)
    ex.log_scalar("train.accuracy", 0.8)  # implicit step 0 for this metric
```

Facts verified for Sacred 0.8.7:

- `_run.log_scalar(metric_name, value, step=None)` and `ex.log_scalar(name, value, step=None)` enqueue scalar metric entries while a run is active.
- When `step` is omitted, Sacred keeps an independent implicit counter per metric name starting at `0`.
- Steps should form an increasing sequence for each metric. Sacred records what you provide, so out-of-order steps make later analysis confusing.
- Metrics are emitted to observers during heartbeat processing and during the final heartbeat when the run stops.
- `FileStorageObserver` writes `metrics.json` under the run directory with one object per metric name containing `steps`, `values`, and `timestamps` arrays.
- `MongoObserver` writes scalar metrics to a metrics collection and adds metric references under `info["metrics"]`.
- Cloud observers in this version contain FileStorage-like metric writers, but live cloud service behavior was not verified here.

## Track resources and artifacts

Use resources for files the experiment reads and artifacts for files the experiment creates:

```python
@ex.main
def main(_run):
    with _run.open_resource("input.txt") as handle:
        payload = handle.read()

    with open("output.txt", "w") as handle:
        handle.write(payload.upper())

    _run.add_artifact("output.txt", name="uppercase-output.txt")
```

API behavior to remember:

- `open_resource(filename, mode="r")` emits a resource event and returns an opened file handle.
- `add_resource(filename)` emits a resource event without opening the file.
- `add_artifact(filename, name=None, metadata=None, content_type=None)` emits an artifact event. If `name` is omitted, Sacred uses the basename of the file.
- Artifact `metadata` and `content_type` are honored by MongoDB storage. File storage records and copies the artifact name but does not persist those metadata fields separately.
- For file storage, artifact names must not collide with reserved files such as `run.json`, `config.json`, `cout.txt`, and `metrics.json`.

## Use Python logging inside Sacred functions

For regular messages, use Sacred's `_log` special argument. It supplies a Python `logging.Logger` child of the experiment logger:

```python
@ex.capture
def train(_log):
    _log.info("training started")
    _log.warning("using a fallback path")
```

You can set `ex.logger` to a custom logger before the run. Programmatic log-level control is available through `Experiment.run(options={"--loglevel": "ERROR"})`; exact CLI log-level flag syntax belongs in the `configuration-and-cli` sub-skill.

## Add external observers carefully

Programmatic observer snippets:

```python
from sacred.observers import MongoObserver, QueuedMongoObserver, SqlObserver
from sacred.observers import TinyDbObserver, QueueObserver, FileStorageObserver

# MongoDB, when pymongo and a reachable MongoDB are available.
ex.observers.append(MongoObserver(url="host:27017", db_name="sacred"))

# Fault-tolerant wrapper for temporary service failures.
ex.observers.append(QueuedMongoObserver(url="host:27017", db_name="sacred"))

# Local SQL example if SQLAlchemy is installed.
ex.observers.append(SqlObserver("sqlite:///runs.db"))

# Local TinyDB if optional dependencies are installed.
ex.observers.append(TinyDbObserver("runs_db"))

# Generic queue wrapper around an already-created observer.
ex.observers.append(QueueObserver(FileStorageObserver("runs")))
```

Do not instantiate cloud, chat, or Neptune observers in automated probes unless the user has explicitly provided credentials and approved network/service access. For credential-backed observers, prefer configuration files or environment variables and never paste secrets into code, logs, or generated skill content.

## Implement a custom observer

Subclass `RunObserver` when Sacred's storage backends are not enough. Implement only the events you need, but preserve the method signatures. Events are fired in this lifecycle:

1. `queued_event(...)` when a run is queued instead of executed.
2. `started_event(...)` when execution begins; this is where IDs are assigned.
3. Repeated `heartbeat_event(info, captured_out, beat_time, result)` and `log_metrics(metrics_by_name, info)` during a running experiment.
4. `resource_event(filename)` and `artifact_event(name, filename, metadata=None, content_type=None)` when files are registered.
5. One terminal event: `completed_event(stop_time, result)`, `interrupted_event(interrupt_time, status)`, or `failed_event(fail_time, fail_trace)`.
6. `join()` when Sacred waits for background observer work to finish.

Keep custom observer failures isolated where possible. Sacred does not catch startup observer failures, because a run should fail if the initial storage backend cannot create its record. During heartbeat/resource/artifact events, Sacred marks an observer as failed after an exception and warns about it at the end of the run.
