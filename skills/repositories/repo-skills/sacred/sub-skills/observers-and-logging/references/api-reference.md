# Observers and logging API reference

## Purpose

Read this for concise Sacred 0.8.7 API facts needed by observer, metric, info, artifact, resource, and logging tasks. For basic experiment construction and full CLI syntax, route to the sibling sub-skills named in `SKILL.md`.

## Core run-storage APIs

| API | Verified signature | Use | Notes |
|---|---|---|---|
| `Experiment.run` | `run(command_name=None, config_updates=None, named_configs=(), info=None, meta_info=None, options=None)` | Execute a command programmatically and return the completed `Run`. | `info` prepopulates the run info dict; `meta_info` is stored at start/queue time. |
| `Experiment.run_commandline` | `run_commandline(argv=None)` | Execute through Sacred's command-line parser. | Exact observer flag syntax is owned by `configuration-and-cli`. |
| `Experiment.open_resource` | `open_resource(filename, mode="r")` | Open a file during a run and emit a resource event. | Asserts that a run is active. Delegates to current `Run`. |
| `Run.open_resource` | `open_resource(filename, mode="r")` | Same as `Experiment.open_resource`, using the run object directly. | Converts the path to an absolute path before emitting the event. |
| `Experiment.add_resource` | `add_resource(filename)` | Register a file read by the run without opening it. | Asserts that a run is active. |
| `Run.add_resource` | `add_resource(filename)` | Same as `Experiment.add_resource`, using the run object directly. | Converts the path to an absolute path before emitting the event. |
| `Experiment.add_artifact` | `add_artifact(filename, name=None, metadata=None, content_type=None)` | Register an output file produced by the run. | `metadata` and `content_type` only affect MongoDB storage. |
| `Run.add_artifact` | `add_artifact(filename, name=None, metadata=None, content_type=None)` | Same as `Experiment.add_artifact`, using the run object directly. | If `name` is omitted, Sacred uses `os.path.basename(filename)`. |
| `Experiment.log_scalar` | `log_scalar(name, value, step=None)` | Enqueue a scalar metric while a run is active. | Delegates to current `Run`. |
| `Run.log_scalar` | `log_scalar(metric_name, value, step=None)` | Enqueue a scalar metric through the run object. | If `step` is omitted, the metric-specific implicit counter is used. |
| `Experiment.info` | property | Access current run's custom info dict. | Only valid during a run; equivalent to `_run.info`. |

## Observer interface events

Subclass `RunObserver` and override one or more of these methods:

| Method | Parameters | Fired when | Expected return |
|---|---|---|---|
| `queued_event` | `ex_info, command, host_info, queue_time, config, meta_info, _id` | The run is queued instead of executed. | May return a run ID if `_id` is `None`. |
| `started_event` | `ex_info, command, host_info, start_time, config, meta_info, _id` | The run starts executing. | May return a run ID if `_id` is `None`. |
| `heartbeat_event` | `info, captured_out, beat_time, result` | Heartbeat processing during and at the end of execution. | Usually `None`. |
| `completed_event` | `stop_time, result` | Main command returns normally. | Usually `None`. |
| `interrupted_event` | `interrupt_time, status` | Keyboard interrupt or Sacred interrupt occurs. | Usually `None`. |
| `failed_event` | `fail_time, fail_trace` | Any other exception aborts the run. | Usually `None`. |
| `resource_event` | `filename` | `open_resource` or `add_resource` is called. | Usually `None`. |
| `artifact_event` | `name, filename, metadata=None, content_type=None` | `add_artifact` is called. | Usually `None`. |
| `log_metrics` | `metrics_by_name, info` | Heartbeat drains scalar metrics. | Usually `None`; Mongo may mutate `info` with metric references. |
| `join` | no required arguments | Sacred waits for observers after run completion/failure. | Should block until background observer work is done. |

Observers have a `priority` attribute. Sacred sorts observers by descending priority before a run starts. The first observer that assigns an ID determines `_id` for the run and for all later observers.

## Built-in observer constructors

| Observer | Verified constructor | Main storage shape | Required optional dependencies |
|---|---|---|---|
| `FileStorageObserver` | `FileStorageObserver(basedir, resource_dir=None, source_dir=None, template=None, priority=20, copy_artifacts=True, copy_sources=True)` | Per-run directories with JSON files and copied artifacts/resources/sources. | None for basic storage; `mako` for template rendering. |
| `MongoObserver` | `MongoObserver(url=None, db_name="sacred", collection="runs", collection_prefix="", overwrite=None, priority=30, client=None, failure_dir=None, **kwargs)` | MongoDB `runs` collection, GridFS files, metrics collection. | `pymongo`, GridFS support, MongoDB service. |
| `QueuedMongoObserver` | `QueuedMongoObserver(interval=20.0, retry_interval=10.0, url=None, db_name="sacred", collection="runs", overwrite=None, priority=30, client=None, **kwargs)` | MongoDB through a retrying background queue. | Same as MongoDB. |
| `QueueObserver` | `QueueObserver(covered_observer, interval=20.0, retry_interval=10.0)` | Delegates to another observer in a background worker. | Depends on the covered observer. |
| `SqlObserver` | `SqlObserver(url, echo=False, priority=40)` | SQL tables for run, host, experiment, resources, artifacts, and sources. | `sqlalchemy`; database-specific drivers if not SQLite. |
| `TinyDbObserver` | `TinyDbObserver(path="./runs_db", overwrite=None)` | `metadata.json` plus hash-addressed files under `hashfs/`. | `tinydb`, `tinydb-serialization`, `hashfs`. |
| `TinyDbReader` | `TinyDbReader(path)` | Query/read interface for TinyDB observer output. | Same TinyDB stack; path must exist. |
| `S3Observer` | `S3Observer(bucket, basedir, resource_dir=None, source_dir=None, priority=20, region=None)` | FileStorage-like objects under an S3 bucket prefix. | `boto3`, AWS region, credentials, bucket permissions. |
| `GoogleCloudStorageObserver` | `GoogleCloudStorageObserver(bucket, basedir, resource_dir=None, source_dir=None, priority=20)` | FileStorage-like blobs under a GCS bucket prefix. | `google-cloud-storage`, application credentials, bucket permissions. |
| `SlackObserver` | `SlackObserver(webhook_url, bot_name="sacred-bot", icon=":angel:", priority=10, completed_text=None, interrupted_text=None, failed_text=None)` | Completion/interruption/failure webhook messages. | `requests`, Slack webhook URL. |
| `TelegramObserver` | `TelegramObserver(bot, chat_id, silent_completion=False, priority=10, **kwargs)` | Start/completion/interruption/failure Telegram bot messages. | `python-telegram-bot`, bot token, chat ID. |

Deprecated `.create(...)` class methods still exist on several observers for backward compatibility; prefer direct construction in new code. `SqlObserver.create_from(engine, session, priority=40)`, `TinyDbObserver.create_from(db, fs, overwrite=None, root=None)`, and `MongoObserver.create_from(...)` are useful in tests or when a managed client/session already exists.

## FileStorageObserver behavior details

| Feature | Behavior |
|---|---|
| Base directory creation | Constructing the observer does not create `basedir`; the first queued or started run creates it. |
| Auto IDs | If `_id is None`, the observer scans numeric directories and creates the next numeric ID. |
| Explicit IDs | If `_id` is supplied, the observer tries to create exactly that run directory and raises if it already exists. |
| Source snapshots | With `copy_sources=True`, source files are copied into `_sources/` using a basename plus MD5 digest. With `copy_sources=False`, source paths in `run.json` refer to the original source location. |
| Resource copies | Resource files are copied into `_resources/` using a basename plus MD5 digest unless copying is disabled for files already inside the storage base. |
| `copy_artifacts` caveat | In the implementation, this flag affects whether files already under the observer base are copied by the shared `find_or_save` path. It does not stop `artifact_event` from copying artifacts into the run directory. |
| Artifact copies | `artifact_event(name, filename, ...)` copies `filename` into the current run directory as `name` and appends `name` to `run.json` `artifacts`. |
| Reserved artifact names | `run.json`, `config.json`, `cout.txt`, and `metrics.json` are protected; attempting to save an artifact under one of these names raises `FileExistsError`. |
| Info file | `info.json` is written when the info dict is non-empty during heartbeat processing. |
| Metrics file | `metrics.json` is written after scalar metrics are drained by heartbeat processing. |
| Template rendering | If `template` is supplied or a default template exists and `mako` is installed, a `report.<ext>` file can be rendered at terminal events. Treat templates as executable Python-capable content. |

## Scalar metrics data model

Sacred queues scalar metric entries with fields:

- `name`: metric name such as `training.loss`.
- `step`: explicit integer step or the metric-specific implicit counter.
- `timestamp`: UTC time when the scalar was logged.
- `value`: scalar value, with numpy scalar conversion if numpy is available.

When observers receive metrics, Sacred linearizes entries by metric name:

```json
{
  "training.loss": {
    "steps": [0, 1],
    "values": [0.9, 0.7],
    "timestamps": ["2024-01-01T00:00:00", "2024-01-01T00:00:01"]
  }
}
```

For FileStorageObserver, this object is appended in `metrics.json`. For MongoObserver, equivalent arrays are pushed to a metrics collection keyed by run ID and metric name; the run's `info` dict receives references to those metric documents.

## TinyDbReader quick reference

After a TinyDB-observed run exists, `TinyDbReader(path)` supports:

| Method | Purpose | Selection arguments |
|---|---|---|
| `fetch_metadata(...)` | Return stored run metadata. | `indices`, `exp_name`, or a TinyDB `query`. |
| `fetch_files(...)` | Return handles for stored sources, resources, and artifacts. | `indices`, `exp_name`, or `query`. |
| `fetch_report(...)` | Return text summaries of matched runs. | `indices`, `exp_name`, or `query`. |
| `search(query)` | Thin wrapper around TinyDB search. | TinyDB query object. |

`indices=-1` selects the latest run, `indices=0` selects the oldest run, and an out-of-range index raises `ValueError`.

## Python logging APIs

- Use `_log` as a special captured-function argument to receive a Python `logging.Logger` child for that function.
- Assign `ex.logger = custom_logger` before the run to customize logger handlers and formatting.
- Programmatic log-level control uses `ex.run(options={"--loglevel": "ERROR"})`.
- Sacred's logger messages are distinct from scalar metrics. Use `_log` for human messages, `log_scalar` for numerical series, and `info` for small structured status.
