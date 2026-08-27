# Optuna Storage Workflows

Optuna storage controls persistence, resuming, and distributed coordination. In-memory storage is fine for a single short Python process, but CLI use and multi-process/multi-node optimization need persistent storage.

## Storage Decision Guide

| Situation | Recommended storage | Why |
| --- | --- | --- |
| Local CLI smoke test or resumable local run | `sqlite:///study.db` / `RDBStorage("sqlite:///study.db")` | Easy, persistent, no external server. |
| Single-node multiprocess sharing | `JournalStorage(JournalFileBackend("journal.log"))` or an RDB backend | Shared persistent state; journal file is simple for local use. |
| Multi-node optimization | `RDBStorage` with PostgreSQL/MySQL or another server RDB supported by SQLAlchemy | Avoids unsafe cross-machine file-lock assumptions. |
| Very large number of workers | `GrpcStorageProxy` in front of a storage backend | Reduces direct storage pressure; workers connect to the proxy. |
| Redis-backed journal | `JournalStorage(JournalRedisBackend("redis://..."))` | Avoids host filesystem race conditions, but requires the Redis optional dependency/service. |

SQLite is useful for examples and local persistence. For high-concurrency or multi-node production, use a server database such as PostgreSQL or MySQL and configure the matching SQLAlchemy driver outside Optuna.

## Persistent RDB Usage

Use a storage URL with `create_study` to create or resume a study:

```python
import optuna

storage = "sqlite:///example-study.db"
study = optuna.create_study(
    study_name="example-study",
    storage=storage,
    direction="minimize",
    load_if_exists=True,
)
```

For direct storage control, instantiate `RDBStorage`:

```python
import optuna
from optuna.storages import RDBStorage

storage = RDBStorage("sqlite:///example-study.db")
study = optuna.create_study(study_name="example-study", storage=storage, load_if_exists=True)
```

Verified signature:

```python
RDBStorage(
    url,
    engine_kwargs=None,
    skip_compatibility_check=False,
    *,
    heartbeat_interval=None,
    grace_period=None,
    heartbeat_stale_trial_callback=None,
    failed_trial_callback=None,
    skip_table_creation=False,
)
```

Operational notes:

- `storage upgrade` uses `RDBStorage(..., skip_compatibility_check=True, skip_table_creation=True)` and upgrades known older schemas to the installed Optuna schema head.
- Use `engine_kwargs` for SQLAlchemy engine options such as connection pool settings.
- Do not assume sampler/pruner instance state is persisted in storage. If exact seeded sampler continuation matters, persist and restore the sampler object separately.
- Treat `skip_compatibility_check` and `skip_table_creation` as advanced options for migration/admin flows, not normal study creation.

## File-Backed JournalStorage

Use `JournalStorage` with a backend object:

```python
import optuna
from optuna.storages import JournalStorage
from optuna.storages.journal import JournalFileBackend

storage = JournalStorage(JournalFileBackend("optuna-journal.log"))
study = optuna.create_study(study_name="journal-demo", storage=storage, load_if_exists=True)
```

Verified signatures:

```python
JournalStorage(log_storage)
JournalFileBackend(file_path, lock_obj=None)
JournalFileSymlinkLock(filepath, grace_period=30)
JournalFileOpenLock(filepath, grace_period=30)
```

Use `JournalFileOpenLock` if the default symlink-style lock is unsuitable on the target filesystem, especially on Windows environments where symlink privileges can be restricted.

For CLI journal use, prefer an explicit storage class:

```bash
optuna create-study --storage optuna-journal.log --storage-class JournalFileBackend --study-name journal-demo --direction minimize --skip-if-exists
```

## Redis JournalStorage

Redis-backed journal storage uses `JournalRedisBackend`:

```python
import optuna
from optuna.storages import JournalStorage
from optuna.storages.journal import JournalRedisBackend

storage = JournalStorage(JournalRedisBackend("redis://localhost:6379/0"))
```

Verified signature:

```python
JournalRedisBackend(url, use_cluster=False, prefix="")
```

The Redis Python dependency and a running Redis service are not part of Optuna's base install. If import or connection fails, install/configure Redis support in the application environment rather than adding Redis-only code to simple SQLite/journal-file workflows.

## GrpcStorageProxy

`GrpcStorageProxy` lets workers connect to a proxy server instead of directly hitting the underlying storage. This is intended for large distributed workloads.

Server process:

```python
from optuna.storages import RDBStorage, run_grpc_proxy_server

storage = RDBStorage("postgresql://user:password@host:5432/optuna")
run_grpc_proxy_server(storage, host="0.0.0.0", port=13000)
```

Worker process:

```python
import optuna
from optuna.storages import GrpcStorageProxy

storage = GrpcStorageProxy(host="proxy-host", port=13000)
study = optuna.create_study(study_name="distributed", storage=storage, load_if_exists=True)
```

Verified signatures:

```python
run_grpc_proxy_server(storage, *, host="localhost", port=13000, thread_pool=None)
GrpcStorageProxy(*, host="localhost", port=13000)
```

The `grpcio` dependency is optional. If it is not installed, importing or using gRPC storage will fail. Use RDBStorage directly unless the deployment needs a proxy tier.

## Heartbeat and Stale Trial Handling

Heartbeat is an `RDBStorage`-oriented mechanism for detecting workers that died while trials were running.

```python
import optuna
from optuna.storages import RDBStorage, RetryHeartbeatStaleTrialCallback

storage = RDBStorage(
    "sqlite:///heartbeat-demo.db",
    heartbeat_interval=60,
    grace_period=120,
    heartbeat_stale_trial_callback=RetryHeartbeatStaleTrialCallback(max_retry=3),
)
study = optuna.create_study(study_name="heartbeat-demo", storage=storage, load_if_exists=True)
```

Verified callback signature:

```python
RetryHeartbeatStaleTrialCallback(max_retry=None, inherit_intermediate_values=False)
```

Behavior to rely on:

- `heartbeat_interval` must be `None` or a positive integer.
- `grace_period` must be `None` or a positive integer; when omitted, Optuna uses `2 * heartbeat_interval`.
- The heartbeat thread is tied to `Study.optimize`; trials created through low-level `ask` may warn because heartbeat is designed around optimization loops.
- `fail_stale_trials(study)` fails stale running trials for the same study and invokes `heartbeat_stale_trial_callback` when configured.
- `RetryHeartbeatStaleTrialCallback` can enqueue a retried trial and can inherit parameters, distributions, user attrs, and optionally intermediate values.
- `failed_trial_callback` is deprecated-compatible behavior; prefer `heartbeat_stale_trial_callback`.

## Schema Upgrades

Run upgrades only against RDB URLs and after backing up production databases:

```bash
optuna storage upgrade --storage sqlite:///example-study.db
```

If the current version is already the head revision, Optuna reports that storage is up to date. If the storage version is newer than the installed package understands, update Optuna rather than forcing a downgrade.

## Distributed Safety Notes

- `InMemoryStorage` cannot coordinate multiple processes.
- File-backed journal storage can be convenient for local or simple shared filesystems, but cross-machine/NFS file locking may be unsafe; prefer server RDB or Redis-backed journal for multi-node use.
- `GrpcStorageProxy` does not preserve every backend ordering property exactly; avoid relying on incidental internal ordering across a proxy.
- For multi-worker jobs, every worker must use the same `study_name`, compatible storage configuration, and `load_if_exists=True` or an already-created study.
