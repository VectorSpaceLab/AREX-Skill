---
name: cli-and-storage
description: "Use this sub-skill for Optuna command-line workflows and
  persistent/distributed storage: CLI commands, SQLite/RDB URLs, JournalStorage,
  GrpcStorageProxy, schema upgrades, CLI ask/tell, OPTUNA_STORAGE, and
  heartbeat/stale-trial behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Optuna CLI and Storage

Use this sub-skill when the task involves operating Optuna studies from the command line or choosing/configuring persistent storage for resumable or distributed optimization.

## Route Here For

- Running `optuna` CLI commands such as `create-study`, `ask`, `tell`, `trials`, `studies`, `best-trial`, `best-trials`, `delete-study`, `study set-user-attr`, and `storage upgrade`.
- Using `--storage`, `--storage-class`, `OPTUNA_STORAGE`, SQLite URLs, `RDBStorage`, `JournalStorage`, `JournalFileBackend`, `JournalRedisBackend`, or `GrpcStorageProxy`.
- Designing ask/tell workflows where an external system evaluates suggested parameters and reports values back to Optuna.
- Handling storage schema upgrades, storage URL/class mismatches, heartbeat monitoring, stale trials, and retry callbacks.

## Route Elsewhere

- Python objective functions, `Study.optimize`, `Study.ask`, and `Study.tell` authoring patterns: use `../optimization-workflows/SKILL.md`.
- Sampler/pruner selection and algorithm settings: use `../samplers-pruners/SKILL.md`.
- Plotting, trial dataframes, parameter importances, and visual analysis: use `../analysis-visualization/SKILL.md`.
- Artifact upload/download and external artifact stores: use `../artifacts-integrations/SKILL.md`.

## Primary References

- CLI commands, flags, and safe command sequences: `references/cli-reference.md`.
- Storage backend selection, persistent/distributed patterns, upgrades, and heartbeat behavior: `references/storage-workflows.md`.
- Common failures and fixes for CLI/storage workflows: `references/troubleshooting.md`.

## Bundled Smoke Scripts

- `scripts/optuna_cli_smoke.py`: creates a temporary SQLite-backed study through the installed `optuna` CLI, runs `ask`/`tell`, and inspects trials.
- `scripts/storage_smoke.py`: verifies local `RDBStorage` and file-backed `JournalStorage` behavior without external services.

Run bundled scripts from this sub-skill directory with an environment where `optuna` is importable:

```bash
python scripts/optuna_cli_smoke.py
python scripts/storage_smoke.py
```

## Operational Defaults

- Prefer `sqlite:///relative-or-absolute-file.db` for local persistent smoke tests and examples.
- Prefer `RDBStorage` backed by PostgreSQL/MySQL for real multi-node optimization; SQLite is suitable for local development, not high-concurrency production.
- Prefer file-backed `JournalStorage(JournalFileBackend(...))` for simple local or single-node multiprocess sharing.
- Use `--storage-class JournalFileBackend` when a CLI storage path is a journal log file or when URL inference is ambiguous.
- Set `heartbeat_interval` and `grace_period` only for `RDBStorage`-style heartbeat workflows, and use `RetryHeartbeatStaleTrialCallback` when stale trials should be retried automatically.
