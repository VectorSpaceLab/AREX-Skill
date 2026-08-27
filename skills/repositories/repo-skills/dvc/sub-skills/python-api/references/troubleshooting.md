# Python API Troubleshooting

Use this guide when DVC Python calls fail or an agent needs to choose safer behavior.

## Missing Repository

Symptoms:

- `Repo()` or `dvc.api.*(repo=None)` fails outside a DVC project.
- A remote Git URL works for Git metadata but not for DVC data access.

Fixes:

- Pass `repo="/path/to/project"` or `repo="https://...git"` explicitly.
- For local automation, run discovery once and log `repo.root_dir` rather than relying on the process working directory.
- Use `Repo.open(repo, uninitialized=True, ...)` only when you intentionally need behavior that permits uninitialized Git/DVC repos; ordinary user automation should prefer `Repo(repo)` or public `dvc.api` helpers.

## Missing Output or Untracked Path

Symptoms:

- `dvc.exceptions.OutputNotFoundError` for `dvc.api.get_url()` or data access.
- `PathMissingError`, `FileMissingError`, or `FileNotFoundError` for a path that was expected to exist.
- `DVCFileSystem.info()` or `ls()` cannot find a path.

Fixes:

- Confirm the path is relative to the DVC repo root unless you are intentionally using an absolute local data-index path.
- Check whether the path is tracked by DVC, Git, or both. `DVCFileSystem.info(path)` may expose `dvc_info` and `fs_info` when available.
- For DVC outputs, ensure the `.dvc`/`dvc.yaml` metadata and `dvc.lock` are present for the selected `rev`.
- Do not assume `get_url()` proves storage existence; use it as a resolver, then verify object existence separately if required.

## Missing Remote or Remote Object

Symptoms:

- Errors indicating no default remote or no remote in an external repo.
- Storage backend import errors for S3, GCS, Azure, SSH, GDrive, WebDAV, WebHDFS, HDFS, or OSS.
- `open()`/`read()` resolves metadata but cannot stream bytes.

Fixes:

- Pass `remote="name"` when the repo has multiple remotes or no default remote.
- Confirm the relevant optional extra is installed in the runtime environment. Extras include `azure`, `gdrive`, `gs`, `hdfs`, `oss`, `s3`, `ssh`, `webdav`, and `webhdfs`; base DVC does not guarantee all remote clients.
- Use `remote_config={...}` only for operation-scoped settings supplied by the user. Avoid persisting credentials from scripts.
- Distinguish metadata resolution from data transfer: `get_url()` may succeed while `open()` fails because bytes are absent or credentials are missing.

## Non-Read `open()` Modes

Symptom:

```text
ValueError: Only reading `mode` is supported.
```

Cause: `dvc.api.open()` supports read modes only.

Fixes:

- Use `mode="r"`, `"rt"`, or `"rb"` depending on text/binary needs.
- To create or modify DVC-tracked outputs, write to the workspace with normal Python file APIs, then use `Repo.add()` or DVC CLI concepts from the data-and-pipelines sub-skill.

## Context Manager Misuse

Symptom:

```text
AttributeError: dvc.api.open() should be used in a with statement.
```

Cause: `dvc.api.open()` returns a context manager wrapper, not an already-open file object.

Wrong:

```python
stream = dvc.api.open("data.csv")
text = stream.read()
```

Right:

```python
with dvc.api.open("data.csv") as stream:
    text = stream.read()
```

For one small file, `dvc.api.read("data.csv")` is acceptable if memory use is bounded.

## Directory vs File Access

Symptoms:

- A DVC-specific directory error when opening a directory path.
- A helper works for `data/file.csv` but fails for `data/`.

Fixes:

- Use `DVCFileSystem.ls()`, `glob()`, or `walk()` to enumerate directories.
- Open only file paths. Check `fs.info(path)["type"]` before streaming.
- Use `fs.get(path, destination, recursive=True)` only when the user explicitly wants files materialized locally.

## Private APIs and Version Drift

Symptoms:

- Imports from `dvc.repo.*` internals break after upgrading DVC.
- Code depends on private classes such as `_DVCFileSystem`.

Fixes:

- Prefer `dvc.api`, `dvc.api.DVCFileSystem`, and `dvc.repo.Repo` public methods.
- Treat native DVC tests as behavior evidence, not as runtime dependencies.
- Keep scripts defensive: print the installed `dvc.__version__`, catch broad `DvcException` for user-facing diagnostics, and avoid assuming a private object layout.

## Repo Methods That Mutate or Execute

Symptoms:

- `Repo.run()` or `Repo.reproduce()` executes commands unexpectedly.
- `Repo.pull()` or `Repo.push()` contacts cloud storage.

Fixes:

- Treat `Repo.run()`, `Repo.add()`, `Repo.reproduce()`, `Repo.pull()`, and `Repo.push()` as side-effecting operations.
- For read-only diagnostics, prefer `repo.status()`, `repo.diff()`, `dvc.api.metrics_show()`, `dvc.api.params_show()`, `dvc.api.exp_show()`, `DVCFileSystem.info()`, and `DVCFileSystem.ls()`.
- Require explicit user confirmation before running pipeline commands, downloading files, or uploading data.

## Exception Handling Pattern

Use DVC-specific exceptions for targeted handling and a final `DvcException` fallback for user-facing CLI helpers.

```python
from dvc.exceptions import DvcException, OutputNotFoundError, PathMissingError
import dvc.api

try:
    with dvc.api.open("data/input.csv", repo=".", encoding="utf-8") as stream:
        header = stream.readline()
except OutputNotFoundError as exc:
    raise SystemExit(f"Path is not tracked by DVC: {exc}") from exc
except PathMissingError as exc:
    raise SystemExit(f"Tracked path is missing from storage/workspace: {exc}") from exc
except DvcException as exc:
    raise SystemExit(f"DVC failed: {exc}") from exc
```

Avoid swallowing exceptions silently; DVC errors often encode whether the problem is metadata, local cache, remote configuration, or missing storage bytes.
