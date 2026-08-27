---
name: observers-and-logging
description: "Store and inspect Sacred run metadata, artifacts, resources,
  metrics, and external observer integrations."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Sacred observers and logging

Use this sub-skill when the task is about recording, inspecting, or troubleshooting Sacred run metadata: observers, local run directories, metrics, `_run.info`, resources, artifacts, Python logging, and optional external storage/notification integrations.

## Route here when

- The user wants a local observer that writes `run.json`, `config.json`, `info.json`, `cout.txt`, `metrics.json`, artifacts, resources, and source snapshots.
- The user asks how observer events flow (`started_event`, `heartbeat_event`, terminal events, resource/artifact events, `log_metrics`) or how observer priority and run IDs work.
- The user needs to decide between `FileStorageObserver`, `MongoObserver`, `QueuedMongoObserver`, `SqlObserver`, `TinyDbObserver`/`TinyDbReader`, `QueueObserver`, S3/GCS, Slack, Telegram, or Neptune-style integrations.
- The user needs to record scalar metrics, small custom info, input resources, output artifacts, or Python logger output from a running experiment.

## Route elsewhere

- Initial experiment/ingredient construction, `@ex.main`, `ex.run`, and basic `Run` lifecycle belong in the `experiment-core` sub-skill.
- Exact command-line observer flag syntax and config-update CLI quoting belong in the `configuration-and-cli` sub-skill.
- Output capture modes, dependency/source discovery, clean-repo enforcement, seeds, and reproducibility settings belong in the `reproducibility-and-capture` sub-skill.

## Read or run these bundled files

- Read [references/observer-workflows.md](references/observer-workflows.md) when choosing an observer, adding storage to an experiment, logging metrics/info/resources/artifacts, or inspecting a local run directory.
- Read [references/api-reference.md](references/api-reference.md) when you need verified Sacred 0.8.7 signatures, observer event parameters, storage schemas, or optional observer constructor notes.
- Read [references/troubleshooting.md](references/troubleshooting.md) when an observer import fails, a storage service or credential is missing, `FileStorageObserver` cannot write, metrics are absent/out of order, or `QueueObserver` appears stuck.
- Run [scripts/sacred_file_observer_probe.py](scripts/sacred_file_observer_probe.py) to verify that the installed Sacred package can perform a tiny local observed run and write config, run metadata, info, metrics, artifact, and resource signals in a temporary directory.

## Operating rules

1. Attach observers before starting the run. Sacred sorts observers by descending `priority`; the first observer that sees `_id=None` determines the run ID.
2. Prefer `FileStorageObserver` for no-service local validation. It needs only a writable directory and is the verified path for this sub-skill.
3. Treat MongoDB, SQL, TinyDB, S3, GCS, Slack, Telegram, and Neptune integrations as optional unless the current environment explicitly proves their packages, services, and credentials.
4. Only mutate `ex.info` or `_run.info`, call `ex.log_scalar`/`_run.log_scalar`, or use `open_resource`, `add_resource`, and `add_artifact` while a run is active.
5. For long-running jobs, remember that observers receive live `info`, captured output, result, and metrics during heartbeat events; finished runs receive a final heartbeat before terminal observer events.
6. Keep large binary outputs as artifacts, small JSON-like status as `info`, input files as resources, and scalar series as metrics.
