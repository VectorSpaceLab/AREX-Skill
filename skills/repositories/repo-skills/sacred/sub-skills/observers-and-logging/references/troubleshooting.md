# Observer and logging troubleshooting

## Purpose

Read this when Sacred observer setup, run storage, metrics, resources, artifacts, notifications, or local file inspection does not behave as expected.

## Fast local diagnosis

1. If the task can be reduced to local file storage, run `scripts/sacred_file_observer_probe.py` from the nearest sub-skill directory. It creates a temporary run and asserts `run.json`, `config.json`, `info.json`, `metrics.json`, an artifact file, and a copied resource.
2. If the probe cannot import Sacred, fix the installed package environment first. Modern setuptools can warn about or remove `pkg_resources`; Sacred 0.8.7 imports `pkg_resources`, so a compatible setuptools version may be required.
3. If the local probe passes but an external observer fails, treat the problem as an optional dependency, credential, network, database, cloud, or service issue rather than a core Sacred failure.

## Missing optional packages

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'pymongo'` or GridFS import errors | Mongo observer dependencies are missing. | Install `pymongo` in the target environment, then verify a MongoDB service is reachable. |
| `ModuleNotFoundError: No module named 'sqlalchemy'` | SQL observer dependency is missing. | Install `sqlalchemy` and any dialect driver needed by the SQLAlchemy URL. SQLite requires fewer external pieces than remote databases. |
| `ModuleNotFoundError` for `tinydb`, `tinydb_serialization`, or `hashfs` | TinyDB observer stack is incomplete. | Install all three packages together before using `TinyDbObserver` or `TinyDbReader`. |
| `ModuleNotFoundError: No module named 'boto3'` | S3 observer dependency is missing. | Install `boto3`, then separately verify region, credentials, bucket name, and permissions. |
| `ModuleNotFoundError` for `google.cloud.storage` | GCS observer dependency is missing. | Install `google-cloud-storage`, then separately verify application credentials and bucket access. |
| Slack observer imports but messages are not sent | `requests` may be missing, webhook URL may be invalid, or network access may be blocked. | Verify `requests`, use a secret-managed webhook URL, and test only with user approval. |
| Telegram observer import or send fails | `python-telegram-bot` is missing or the bot/chat/proxy config is invalid. | Verify the package, bot token, chat ID, and proxy settings. Do not print tokens. |
| Neptune observer import fails | External Neptune Sacred integration is not installed. | Install the Neptune packages only when the user wants that integration and has credentials. |
| `mako` import/template failures | FileStorage template rendering dependency is missing or template path is wrong. | Install `mako` only if report rendering is needed; otherwise omit the template. Treat templates as Python-capable content. |

Do not claim optional observer support was verified just because the Sacred base package imports. Each optional observer needs its package and, for services, a live service/credential check.

## Missing services, credentials, or network

| Observer | Required external state | Common symptoms | What to check |
|---|---|---|---|
| MongoDB | Reachable MongoDB server, authentication if enabled, writable database/collection, optional failure directory. | Connection timeout, authentication error, `AutoReconnect`, `ConnectionFailure`, or final-save warning. | Host/port or URI, credentials, database name, collection prefix, firewall, retry/failure directory policy. |
| Queued Mongo | Same as MongoDB plus background queue. | Run finishes but observer keeps retrying or `join()` waits. | Whether failures are temporary; if credentials/URI are wrong, the queue may retry forever. |
| SQL | SQLAlchemy URL, database driver, writable schema, DB permissions. | URL parsing errors, driver imports, permission errors, locked SQLite database. | Validate URL outside the experiment with a tiny connection before long runs. |
| S3 | `boto3`, AWS credentials, region, bucket permissions, valid bucket name, network. | Region error, credential error, invalid bucket name, `FileExistsError` for existing prefix/run ID. | Bucket naming rules, region config, object write permissions, whether run ID directory already exists. |
| GCS | Google credentials, bucket permissions, installed Google client, network. | `ConnectionError` mentioning application credentials, invalid bucket name, permissions. | Credential environment, bucket name without `gs://`, object write/list permissions. |
| Slack | Webhook URL, network, `requests`. | No message, HTTP/network failure, leaked/invalid webhook. | Store webhook in a secret-managed config; never log it. |
| Telegram | Bot token, chat ID, user has initiated chat, optional proxy. | Send failures logged by observer, invalid token/chat errors. | Token/chat config and proxy URL format. Never log tokens. |
| Neptune | Project, API token, external integration package, network. | Import or authentication errors. | Package, project name, API token from secret storage. |

If a task asks for cloud/chat/Neptune verification but credentials are absent, stop and ask for explicit user-provided credentials or approval. Do not fabricate a successful verification.

## FileStorageObserver path collisions and permissions

| Symptom | Likely cause | Recovery |
|---|---|---|
| `PermissionError` while starting the run | `basedir`, `resource_dir`, or `source_dir` is not writable. | Choose a writable directory; create parent directories with correct permissions before the run. |
| `FileExistsError` when using an explicit run ID | The requested run directory already exists. | Use a new ID, remove/archive the old run directory only with user approval, or let Sacred auto-assign numeric IDs. |
| `FileExistsError` after many auto-ID attempts | Filesystem listing/creation is inconsistent or another process is racing for IDs. | Use a single writer per storage directory, or provide unique explicit IDs. |
| Artifact save raises about reserved filenames | Artifact name is `run.json`, `config.json`, `cout.txt`, or `metrics.json`. | Choose a different artifact `name`, such as `model.pkl` or `summary.json`. |
| Expected `_sources/` is absent | `copy_sources=False`, no detected source file, or source collection disabled. | Enable `copy_sources=True` if source snapshots are required. If source paths must remain private, keep it disabled and document that choice. |
| Expected `_resources/` copy is absent | Resource file is already inside the storage base and copying was disabled for that case. | Use `copy_artifacts=True` for file-storage resource copies, or keep a stable external resource path. |
| Artifact is not under `_resources/` | Artifacts are copied into the run directory, not the `_resources/` directory. | Inspect `run.json` `artifacts` and look for the artifact name directly under the run directory. |
| `info.json` is missing | `_run.info`/`ex.info` stayed empty or no heartbeat/final heartbeat processed it. | Add info during the active run and wait for run completion or a heartbeat. |
| `metrics.json` is missing | No scalar metrics were logged, metrics were drained manually, or no heartbeat/final heartbeat processed them. | Use `_run.log_scalar` or `ex.log_scalar` during the run and inspect after completion. |

## `copy_sources` and `copy_artifacts` choices

- Use `copy_sources=True` when reproducibility and source snapshots matter. Disable it when source files are private, huge, or not meaningful for the run record.
- Use `copy_sources=False` only after accepting that `run.json` may point to source paths that are not portable outside the original machine.
- The `copy_artifacts` parameter name is easy to misread. In the FileStorageObserver implementation it controls whether files already under the observer base are copied by the shared resource/source save path. It does not disable normal artifact copying into the run directory.
- If a resource or artifact is large, decide intentionally whether copying it into run storage is acceptable. For huge model checkpoints, prefer storing a small manifest artifact plus a stable external URI only when that URI is permitted to be part of the run record.

## QueueObserver retry semantics

| Symptom | Explanation | Recovery |
|---|---|---|
| Run appears stuck at shutdown with a queued observer | Sacred calls `join()` on observers. `QueueObserver.join()` waits for the background queue to drain. | Inspect the covered observer error. A permanent failure can prevent the queue from draining. |
| Queue keeps retrying indefinitely | `QueueObserver` requeues failed events and has no final-failure declaration. | Use it only for temporary outages. Fix permanent credential/schema/path errors rather than waiting. |
| `started_event` still fails immediately | `QueueObserver.started_event` calls the covered observer's `started_event` synchronously because the run needs an ID and initial record. | The storage backend must be available enough to create the initial run record. |
| Metrics queueing looks different for Mongo | `QueuedMongoObserver` wraps a queue-compatible Mongo observer whose `log_metrics` handles one metric name at a time. | Verify metrics after `join()` or after the run fully completes. |

For long jobs with external services, choose retry intervals that match expected outages. Do not use the queue to hide bad credentials, schema errors, invalid bucket names, or missing packages.

## Metrics are absent, duplicated, or out of order

| Symptom | Likely cause | Recovery |
|---|---|---|
| No metric appears while the run is still executing | Heartbeat has not fired yet. Default heartbeat interval is 10 seconds. | Wait for a heartbeat, lower the beat interval through the appropriate run option, or inspect after completion. |
| Metrics appear only after completion | Sacred emits a final heartbeat when the run stops. Short runs often flush metrics only then. | This is expected for short runs. |
| Steps are `[0, 1, ...]` despite not passing `step` | Implicit metric-specific counter is being used. | Pass explicit integer `step` values if steps should represent epochs/iterations. |
| Steps are non-monotonic | Caller supplied out-of-order explicit steps. | Sort or validate step generation in user code; Sacred stores the sequence as logged. |
| Two metrics both start at step `0` | Implicit counters are independent per metric name. | Expected behavior. Use explicit steps if comparing series by global iteration. |
| FileStorage `metrics.json` has arrays of different lengths | Corrupt or partially written file, custom observer mutation, or manual edit. | Rerun a minimal probe, then inspect whether a custom observer or post-process edited the file. |
| Mongo run `info` contains metric references | MongoObserver stores series in a metrics collection and appends references to `info["metrics"]`. | Query the metrics collection by run ID and metric name instead of expecting full series inside the run document. |

Use `log_scalar` only for numeric scalar series. Store nested objects, strings, and summaries in `info` or artifacts instead.

## Info serialization and BSON/JSON compatibility

| Symptom | Likely cause | Recovery |
|---|---|---|
| Mongo observer complains that a run contained an unserializable entry | `info`, `result`, or another stored field is not BSON-encodable. | Convert objects to JSON/BSON-friendly values before storing, or serialize them into an artifact file. |
| Mongo key starts with `$` or contains `.` and is altered | MongoDB key restrictions force key rewriting. | Use safe key names in `info`, such as `train_loss` instead of `train.loss` for dict keys. Metric names can still contain dots because they are stored as values. |
| JSON file contains unexpected nested lists/dicts for arrays/dataframes | Optional numpy/pandas conversion serialized rich objects. | Prefer explicit `.tolist()` or a small artifact file when precision/schema matters. |
| `ex.info` fails outside a run | `Experiment.info` delegates to the current run. | Use `info` during `ex.run(info={...})` setup, or write to `_run.info` inside the main/captured function. |

## Artifact and resource mistakes

| Symptom | Likely cause | Recovery |
|---|---|---|
| `FileNotFoundError` when adding an artifact/resource | Path does not exist at call time or current working directory differs from what the code expects. | Create the file before `add_artifact`; use explicit paths or paths derived from a known working directory. |
| Resource event fires but the file is later changed | Resources are logged when `open_resource`/`add_resource` is called. | Register the stable input file before mutation, and use artifacts for outputs. |
| Artifact metadata not visible in file storage | FileStorageObserver ignores artifact `metadata` and `content_type` beyond accepting the event signature. | Use MongoDB when metadata/content-type query is required, or include a metadata JSON artifact beside the main artifact. |
| Large artifacts slow or bloat storage | Observer copies the file. | Store a summary artifact or obtain user approval before copying large outputs. |

## Logging confusion

| Symptom | Likely cause | Recovery |
|---|---|---|
| `_log` messages are missing or too verbose | Logger level/handlers are configured differently from expectations. | Use `ex.logger` for custom handlers and programmatic `options={"--loglevel": "..."}` for run-level control. |
| User expects `_log.warning` to create metrics | Python logging and Sacred metrics are separate systems. | Use `_log` for human-readable messages, `_run.log_scalar`/`ex.log_scalar` for numerical series, and `info` for structured status. |
| `cout.txt` is enormous | Captured stdout/stderr or logging output is too verbose for observer storage. | Reduce logging verbosity, change capture behavior through the reproducibility/capture route, or apply a captured-output filter. |

## When to stop and ask

Stop for user input instead of proceeding when:

- The requested observer requires credentials, webhooks, API tokens, cloud projects, remote database access, or network calls not already approved.
- The only recovery path would delete or overwrite an existing run directory, bucket prefix, database record, or artifact.
- A permanent queue failure is suspected but the user has not approved disabling the observer or changing credentials.
- The task requires proving optional observer behavior that cannot be verified with installed packages and available services.
