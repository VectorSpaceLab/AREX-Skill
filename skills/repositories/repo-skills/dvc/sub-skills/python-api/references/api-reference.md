# Python API Reference

This reference is for DVC distribution/import name `dvc`, version evidence `0.1.dev1+g8131c32c3`, Python `>=3.9`. The console entry point is `dvc = dvc.cli:main`, but this sub-skill focuses on Python imports.

## Public Imports

```python
import dvc.api
from dvc.api import DVCFileSystem
from dvc.repo import Repo
```

Prefer these public entry points. Avoid binding automation to private modules such as `dvc.repo.index`, `dvc.fs.dvc._DVCFileSystem`, or internal experiment/cache helpers unless the task is explicitly DVC-internal maintenance.

## Data Access Helpers

### `dvc.api.open()`

Verified signature:

```python
dvc.api.open(
    path: str,
    repo: str | None = None,
    rev: str | None = None,
    remote: str | None = None,
    mode: str = "r",
    encoding: str | None = None,
    config: dict | None = None,
    remote_config: dict | None = None,
)
```

Use it only as a context manager:

```python
with dvc.api.open("data/input.csv", repo=".", rev="HEAD", encoding="utf-8") as stream:
    for line in stream:
        process(line)
```

Key semantics:

- `path` is usually relative to the DVC repo root. Absolute paths are handled through the local data index path logic.
- `repo` can be a local path or Git URL. If omitted, DVC walks upward from the current working directory.
- `rev` selects a Git revision, tag, branch, commit, or DVC experiment name where applicable.
- `remote` selects a configured DVC remote; local projects may try the cache before the default remote.
- `config` injects repo configuration. `remote_config` injects remote-specific options such as credentials or endpoint data.
- `mode` must be read-oriented. Non-read modes raise `ValueError("Only reading `mode` is supported.")`.
- Accessing methods such as `.read()` on the object returned by `dvc.api.open()` before entering `with` raises `AttributeError("dvc.api.open() should be used in a with statement.")`.

Common exceptions to handle:

- `dvc.exceptions.OutputNotFoundError` when the target is not tracked by DVC.
- `dvc.exceptions.PathMissingError` or `dvc.exceptions.FileMissingError` when a tracked path/object cannot be found.
- DVC-specific `IsADirectoryError` when a directory is opened as a file.
- Remote/config errors such as `NoRemoteInExternalRepoError` when the repo needs a remote but none is configured.

### `dvc.api.read()`

Verified signature:

```python
dvc.api.read(
    path,
    repo=None,
    rev=None,
    remote=None,
    mode="r",
    encoding=None,
    config=None,
    remote_config=None,
)
```

`read()` wraps `open()` and returns `fd.read()`. Use it for small files where loading the complete content into memory is acceptable. For large CSVs, parquet shards, model files, or line-oriented processing, use `open()` or `DVCFileSystem.open()` instead.

### `dvc.api.get_url()`

Verified signature:

```python
dvc.api.get_url(
    path: str,
    repo: str | None = None,
    rev: str | None = None,
    remote: str | None = None,
    config: dict | None = None,
    remote_config: dict | None = None,
)
```

Returns a string URL for the storage location of a DVC-tracked file or directory. It resolves the configured cache/remote mapping but does not check whether the object actually exists in storage. Use it for handoff, logging, or passing a remote URL to another system after separately deciding whether existence verification is needed.

## Metrics, Params, Experiments, Artifacts

### `dvc.api.metrics_show()`

Verified signature:

```python
dvc.api.metrics_show(*targets: str, repo: str | None = None, rev: str | None = None, config: dict | None = None) -> dict
```

Returns a flattened dictionary of metrics for the selected workspace or revision. With no targets, it uses metrics tracked in `dvc.yaml`. When multiple files contain the same key, DVC prefixes keys with the metric file name.

### `dvc.api.params_show()`

Verified signature:

```python
dvc.api.params_show(
    *targets: str,
    repo: str | None = None,
    stages: str | Iterable[str] | None = None,
    rev: str | None = None,
    deps: bool = False,
    config: dict | None = None,
) -> dict
```

Returns tracked parameters for the selected workspace or revision. `stages` can be a single stage name or iterable. Use `deps=True` when the caller wants only stage dependency params.

### `dvc.api.exp_show()`

Verified signature:

```python
dvc.api.exp_show(
    repo: str | None = None,
    revs: str | list[str] | None = None,
    num: int = 1,
    param_deps: bool = False,
    force: bool = False,
    config: dict | None = None,
) -> list[dict]
```

Returns a list of experiment rows derived from `Repo.experiments.show()` and DVC's experiment tabulation. Empty display values become `None`; rich text values are converted to strings or floats when possible.

### `dvc.api.exp_save()`

Verified signature:

```python
dvc.api.exp_save(name: str | None = None, force: bool = False, include_untracked: list[str] | None = None) -> str
```

Creates an experiment from the current repo using `exp save` semantics and returns the experiment Git revision. It can raise an experiment-exists error when `name` already exists and `force=False`.

### `dvc.api.artifacts_show()`

Verified signature:

```python
dvc.api.artifacts_show(name: str, version: str | None = None, stage: str | None = None, repo: str | None = None) -> dict[str, str]
```

Returns `{"rev": ..., "path": ...}` for a named artifact. `version` and `stage` are mutually exclusive and using both raises `ValueError`. The returned `rev` and `path` can be passed to `dvc.api.open()` or `dvc.api.read()`.

### `dvc.api.get_dataset()`

Verified signature:

```python
dvc.api.get_dataset(name: str) -> dict
```

Returns one of the typed dataset shapes:

- DVC dataset: `{"type": "dvc", "url": str, "path": str, "sha": str}`.
- DataChain dataset: `{"type": "dc", "name": str, "version": int}`.
- URL dataset: `{"type": "url", "files": list[str], "path": str}`.

It opens the current repo, checks the named dataset, and raises if the dataset is missing, invalidated, or missing lock information.

## Repo Automation

Use `Repo` when a script needs to mutate or inspect a DVC project rather than read one file.

```python
from dvc.repo import Repo

with Repo("/path/to/project") as repo:
    status = repo.status()
    changed = repo.diff(a_rev="HEAD", b_rev=None)
```

Verified public method signatures include:

```python
repo.add(targets, no_commit=False, glob=False, out=None, remote=None, to_remote=False, remote_jobs=None, force=False, relink=True) -> list
repo.run(no_exec=False, no_commit=False, run_cache=True, force=True, **kwargs)
repo.reproduce(targets=None, recursive=False, pipeline=False, all_pipelines=False, downstream=False, single_item=False, glob=False, on_error="fail", **kwargs)
repo.push(targets=None, jobs=None, remote=None, all_branches=False, with_deps=False, all_tags=False, recursive=False, all_commits=False, run_cache=False, revs=None, workspace=True, glob=False) -> int
repo.pull(targets=None, jobs=None, remote=None, all_branches=False, with_deps=False, all_tags=False, force=False, recursive=False, all_commits=False, run_cache=False, glob=False, allow_missing=False) -> dict
repo.status(targets=None, jobs=None, cloud=False, remote=None, all_branches=False, with_deps=False, all_tags=False, all_commits=False, recursive=False, check_updates=True) -> dict
repo.diff(a_rev="HEAD", b_rev=None, targets=None, recursive=False) -> dict
```

Repo scripting guidance:

- Use `with Repo(path) as repo:` so locks and filesystem resources are closed correctly.
- `repo.add()` and `repo.run()` modify DVC metadata; run them only in workspaces where mutation is intended.
- `repo.reproduce()` can execute pipeline commands. Confirm safety before running in automation.
- `repo.push()` and `repo.pull()` contact configured remotes and may need optional storage extras and credentials.
- `repo.status(cloud=True)` or `repo.status(remote=...)` performs remote status checks; local status rejects irrelevant options such as `jobs`, `all_branches`, `all_tags`, or `all_commits`.
- `repo.diff()` compares DVC-tracked data, not Git's index, and defaults to comparing `HEAD` to the workspace.

## Choosing the Right Layer

- Use `dvc.api.open()` for one streamed tracked file at a specific `rev` or `remote`.
- Use `dvc.api.read()` for one small tracked file.
- Use `dvc.api.get_url()` when the desired output is a storage URL, not bytes.
- Use `DVCFileSystem` for listing, globbing, `info()`, recursive `get()`, or fsspec-compatible path work.
- Use `Repo` when a script is equivalent to DVC CLI operations such as add, stage creation, reproduce, status, push, pull, or diff.
