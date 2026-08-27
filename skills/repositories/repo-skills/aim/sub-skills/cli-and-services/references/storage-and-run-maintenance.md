# Aim storage and run maintenance

Aim repositories contain a `.aim` directory with structured run metadata, per-run metric/object storage, lock files, progress markers, and indexes. Maintenance commands can repair or optimize this data, but several of them are destructive or require all writers to be stopped.

## Safety checklist before mutating commands

Before `rm`, `mv`, `close`, `update-metrics`, `upgrade`, `restore`, `prune`, or `reindex`:

1. Identify the repository explicitly with `--repo <repo_dir>`.
2. Stop active training writers that use that repo.
3. Stop `aim up`, `aim server`, and `aim-watcher` if the maintenance command can rewrite indexes or run state.
4. Make an external backup of the `.aim` directory or the whole repository directory.
5. List runs and record the exact hashes to operate on.
6. Ask the user for explicit confirmation before adding `-y, --yes` or deleting corrupted runs.

Use shell quotes around wildcard run patterns, for example `'*'`, so the shell does not expand them.

## Inventory first

List all run hashes:

```bash
aim runs --repo <repo_dir> ls
```

List only corrupted runs:

```bash
aim runs --repo <repo_dir> ls --corrupted
```

If a user reports missing UI data or slow queries, start with list commands and non-mutating diagnosis. Do not jump directly to deletion or reindexing.

## Stalled or failed runs

A run can remain active/stalled if its training process crashed before normal finalization. To force-close known inactive runs:

```bash
aim runs --repo <repo_dir> close <run_hash_1> <run_hash_2>
```

Rules:

- Confirm the process is no longer writing. Force-closing an active run can corrupt data.
- Prefer explicit hashes over broad patterns.
- Use `-y` only after the user confirms the exact hashes and downtime.

If the user is writing Python code, prefer calling `run.finalize()` at normal shutdown; route SDK-level cleanup patterns to `tracking-sdk`.

## Corrupted runs

To inspect:

```bash
aim runs --repo <repo_dir> ls --corrupted
```

To delete all corrupted runs only after backup and confirmation:

```bash
aim runs --repo <repo_dir> rm --corrupted
```

The UI may advise removing corrupted runs. Still apply the backup/confirmation checklist, because `rm --corrupted` permanently deletes the matched run data. Use `-y` only for a user-confirmed maintenance window.

## Copying and moving runs

Copy selected runs:

```bash
aim init --repo <dest_repo_dir> --skip-if-exists
aim runs --repo <source_repo_dir> cp --destination <dest_repo_dir> <run_hash_1> <run_hash_2>
```

Move selected runs:

```bash
aim runs --repo <source_repo_dir> mv --destination <dest_repo_dir> <run_hash_1> <run_hash_2>
```

Prefer `cp` when the goal is backup or migration validation. Use `mv` only when the user accepts removal from the source repo.

## Uploading backup snapshots

```bash
aim runs --repo <repo_dir> upload <bucket_name>
```

This creates/uploads a repository backup snapshot to S3. It requires `boto3`, AWS credentials, network access, and permission to create or write the target bucket. Do not run it without explicit bucket and credential confirmation.

## Metric and storage format maintenance

### `aim runs update-metrics`

```bash
aim runs --repo <repo_dir> update-metrics
```

This separates sequence metadata for better reads. It iterates over all runs and rewrites metadata/index entries. Stop active runs and the UI first.

### `aim storage upgrade 3.11+`

```bash
aim storage --repo <repo_dir> upgrade 3.11+ <run_hash_1> <run_hash_2>
```

This optimizes run metric data for read access. The command creates per-run internal backups and prints a restore command when complete, but an external backup is still required for safe operations.

### `aim storage restore`

```bash
aim storage --repo <repo_dir> restore <run_hash_1> <run_hash_2>
```

This rolls back runs from available internal backups. Confirm the backups correspond to the intended previous state.

### `aim storage prune`

```bash
aim storage --repo <repo_dir> prune
```

This removes dangling/orphan params or sequences that no longer refer to existing runs. Use after run deletion if UI autocomplete still shows deleted run metadata. Backup first because it mutates repository storage.

### `aim storage reindex`

```bash
aim storage --repo <repo_dir> reindex
```

This recreates the index database from scratch. It can help when the UI reports index problems or query performance degrades due to inconsistent indexes. Stop `aim up` and active writers first; use `-y` only after explicit confirmation.

## Handling “stalled/corrupted runs” safely

Use this sequence for a user report such as “the UI says runs are corrupted/stalled”:

1. Ask whether training jobs are still running against the repo.
2. Stop UI/server/watcher if maintenance will mutate state.
3. Backup the repository.
4. Run `aim runs --repo <repo_dir> ls` and `aim runs --repo <repo_dir> ls --corrupted`.
5. For active-looking but dead runs, close only named hashes with `aim runs close`.
6. For corrupted runs, delete only after user confirms the `--corrupted` list or exact hashes.
7. If UI remains inconsistent, run `aim storage prune` or `aim storage reindex` in a confirmed maintenance window.
8. Restart `aim up` or `aim server` and re-check.

Do not default to `rm --corrupted -y`, broad wildcard deletion, or reinitialization. `aim init -y` on an existing repo clears old Aim data and is not a repair command.

## Temporary repositories in tests

For automated smoke tests, create a dedicated temporary or user-selected directory and initialize it with:

```bash
aim init --repo <temp_repo_dir> --skip-if-exists
```

Do not run maintenance commands against a developer's current directory by accident. Do not delete a repository directory while Python `Run` objects may still be flushing; finalize/close writers first.
