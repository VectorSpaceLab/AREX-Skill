# CLI and Storage Troubleshooting

## Install and Entry-Point Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `optuna: command not found` | Console script is not on `PATH` or Optuna is not installed in the active environment. | Activate/install into the intended environment, then check `python -c "import optuna; print(optuna.__version__)"` and `optuna --version`. |
| `python -m optuna` fails | Optuna does not provide a package `__main__` entry point. | Use the `optuna` console script. |
| `ModuleNotFoundError: optuna` in scripts | Script is running under a different Python than the installed package. | Run scripts with the Python environment where Optuna is installed. |
| Missing `pandas`, `plotly`, `grpc`, `redis`, or database driver imports | Optional integrations are not installed by the base package. | Install only the needed optional dependency/driver for that workflow; simple CLI and SQLite smoke tests do not need these extras. |

## Storage URL and Class Errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Storage URL is not specified.` | Command needs persistent storage and neither `--storage` nor `OPTUNA_STORAGE` was set. | Pass `--storage sqlite:///example.db` or set `OPTUNA_STORAGE`. |
| `Failed to guess storage class from storage_url` | The value is neither a Redis URL, an existing file path, nor a valid SQLAlchemy URL. | Use a valid URL/path or pass `--storage-class RDBStorage`, `JournalFileBackend`, or `JournalRedisBackend`. |
| `Invalid choice` for `--storage-class` | Unsupported class name or wrong spelling. | Use `RDBStorage`, `JournalFileBackend`, or `JournalRedisBackend`; deprecated aliases may work but should not be new defaults. |
| SQLAlchemy URL/driver error | RDB URL is malformed or the database driver is missing. | Check SQLAlchemy URL syntax and install the driver such as `psycopg2`, `pymysql`, or the project-approved equivalent. |
| Journal file is treated as RDB URL | The file does not exist yet and no storage class hint was provided. | Create the file first or pass `--storage-class JournalFileBackend`. |

## Study and Trial Misuse

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ask` says implicit study creation was dropped | The study was not created before `ask`. | Run `optuna create-study --study-name ...` first, then `ask`. |
| Duplicate study-name failure | A study with the same name already exists. | Use `create-study --skip-if-exists` or Python `create_study(..., load_if_exists=True)`. |
| `--sampler-kwargs` without `--sampler` fails | CLI cannot choose which sampler constructor to call. | Pass both, for example `--sampler TPESampler --sampler-kwargs '{"seed":0}'`. |
| `tell` fails for a completed trial | The trial is already finished. | Use `--skip-if-finished` if idempotent reporting is intended. |
| `best-trial` fails on multi-objective study | Multi-objective studies have Pareto-front trials, not one scalar best trial. | Use `best-trials`. |
| `tell --values` count mismatch | Multi-objective study directions do not match the number of values. | Pass exactly one value per direction. |

## Search-Space JSON Problems

The CLI `ask --search-space` expects a JSON object whose keys are parameter names and whose values are distribution JSON objects, for example:

```json
{
  "x": {
    "name": "FloatDistribution",
    "attributes": {"low": -10.0, "high": 10.0, "step": null, "log": false}
  }
}
```

Fixes:

- Use valid shell quoting; single-quote JSON in POSIX shells to avoid escaping every double quote.
- Generate distribution JSON from Python when uncertain: `optuna.distributions.distribution_to_json(optuna.distributions.FloatDistribution(-10, 10))`.
- Keep `log=true` distributions positive and avoid invalid step/range combinations; invalid distributions fail before the trial is created.

## Storage Upgrade Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `storage upgrade` reports invalid URL | The target is not an RDB URL. | Use only RDB storage URLs with `storage upgrade`; journal files do not use Alembic schema upgrades. |
| Storage version appears newer than package | Database was created/upgraded by a newer Optuna version. | Upgrade Optuna rather than forcing old code against a newer schema. |
| Production migration risk | Schema upgrade mutates the database. | Back up the DB, test upgrade on a copy, then run the command in a controlled maintenance window. |

## Heartbeat and Stale Trial Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError` for heartbeat interval/grace period | Non-positive interval or grace period. | Use positive integers or `None`. |
| Running trials are not failed as stale | Heartbeat is disabled, grace period has not elapsed, or the stale check has not run for that study. | Use `RDBStorage(..., heartbeat_interval=..., grace_period=...)` and `Study.optimize`, or call `optuna.storages.fail_stale_trials(study)` deliberately. |
| Heartbeat warnings around `ask` | Heartbeat is primarily designed for `Study.optimize`. | Prefer `Study.optimize` for heartbeat-managed workers; use CLI ask/tell without heartbeat assumptions. |
| Retried trials miss intermediate values | `RetryHeartbeatStaleTrialCallback` defaults to not inheriting intermediate values. | Set `inherit_intermediate_values=True` only when that is correct for the objective/pruner workflow. |

## Distributed Storage Edge Cases

- Do not use `InMemoryStorage` for multiple processes.
- Do not rely on local file locks across machines or unreliable NFS; use server RDB, Redis-backed journal, or gRPC proxy architecture.
- Ensure every worker uses the same `study_name`, storage URL/proxy host, and direction configuration.
- For `GrpcStorageProxy`, install `grpcio`, start the proxy server before workers, wait for readiness in worker code when needed, and treat proxy/server lifecycle as deployment infrastructure.
- For SQLite, reduce write contention in local experiments and avoid using it as the backend for heavy distributed workloads.
