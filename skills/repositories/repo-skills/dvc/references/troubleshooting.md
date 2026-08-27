# DVC Cross-Cutting Troubleshooting

Read this when a DVC task fails before it clearly belongs to one sub-skill, or when symptoms span install/import, repository discovery, optional remotes, cache state, and CLI/API routing.

## Install Or Import Fails

Symptoms:

- `ModuleNotFoundError: No module named 'dvc'`.
- `dvc: command not found`.
- `ModuleNotFoundError` for a remote backend such as S3, Azure, Google Cloud Storage, SSH, WebDAV, HDFS, OSS, or Google Drive.

Actions:

1. Install core DVC with `pip install dvc` or the user's package manager.
2. For remote backend failures, install only the needed extra: `dvc[s3]`, `dvc[gs]`, `dvc[azure]`, `dvc[ssh]`, `dvc[gdrive]`, `dvc[webdav]`, `dvc[webhdfs]`, `dvc[hdfs]`, or `dvc[oss]`.
3. Re-run `python -c "import dvc; print(dvc.__version__)"` and `dvc --help`.
4. Use `scripts/check_dvc_install.py` or `sub-skills/remotes-and-cache/scripts/check_remote_support.py` for no-network diagnostics.

## Not In A DVC Repository

Symptoms:

- `dvc root` fails.
- CLI commands complain that there is no DVC repository.
- Python API calls cannot discover a project from the current directory.

Actions:

1. If the task is setup, run `dvc init` inside the intended Git/project root.
2. If the task should inspect an existing project, change to the project or pass `--cd <path>` to CLI commands.
3. For Python, pass `repo=<path-or-url>` explicitly to `dvc.api` helpers.
4. If the task is maintaining the DVC codebase rather than using a project, route to `sub-skills/repo-development/SKILL.md`.

## Remote Or Cache Problems

Symptoms:

- No default remote is configured.
- `push`, `pull`, `fetch`, `get`, `import-url`, or `get_url` fails with missing data, credentials, or backend dependencies.
- Workspace files are missing even though metadata exists.
- Cache links are broken, protected, or not relinked.

Actions:

1. Route to `sub-skills/remotes-and-cache/SKILL.md`.
2. Start with `dvc remote list`, `dvc config --list --show-origin`, and `dvc status -c` only when remote access is safe.
3. For local checks, prefer a filesystem remote or `--help`/config inspection instead of cloud operations.
4. Use `dvc pull --allow-missing` only when missing data is acceptable; do not hide data-loss risk.
5. Use `dvc checkout`, `dvc commit`, `dvc unprotect`, and cache-type changes only after confirming workspace impact.

## Command Routing Confusion

- Stage creation, target syntax, `dvc.yaml`, `dvc.lock`, and `dvc repro`: use `sub-skills/data-and-pipelines/SKILL.md`.
- Experiment sweeps and experiment refs: use `sub-skills/experiments/SKILL.md`.
- Metrics, params, and plots reporting: use `sub-skills/metrics-params-plots/SKILL.md`.
- Python streaming or `DVCFileSystem`: use `sub-skills/python-api/SKILL.md`.
- Editing DVC source code or choosing tests: use `sub-skills/repo-development/SKILL.md`.

## Unsafe Or Expensive Operations

Treat these as opt-in unless the user explicitly approves them:

- Cloud or network transfers.
- Commands using credentials or Studio/live services.
- `dvc gc -c`, destructive workspace cleanups, or commands that delete cache objects.
- Long training or benchmark stages triggered by `dvc repro` or `dvc exp run`.
- Full DVC test suite execution when a focused target is enough.
