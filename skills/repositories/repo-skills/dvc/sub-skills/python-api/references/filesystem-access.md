# Filesystem Access

DVC exposes multiple Python access layers. Pick the one that matches the data shape and memory budget.

## Streaming One File

Use `dvc.api.open()` for a single tracked file when you want to process bytes or text without loading the whole object.

```python
import csv
import dvc.api

with dvc.api.open(
    "data/train.csv",
    repo="/path/to/project",
    rev="main",
    remote="storage",
    encoding="utf-8",
) as stream:
    for row in csv.DictReader(stream):
        handle(row)
```

Safe patterns:

- Pass `encoding` for text mode; omit it or use binary modes such as `"rb"` for bytes.
- Catch DVC exceptions around the `with` block, not only around code inside it, because opening may resolve repo metadata and remote storage.
- Use `remote_config` only for values you would otherwise provide to DVC remote configuration; do not hard-code secrets into reusable scripts.

## Reading One Small File

Use `dvc.api.read()` when the file is small enough to fit comfortably in memory.

```python
import json
import dvc.api

payload = dvc.api.read("reports/metrics.json", repo=".", encoding="utf-8")
metrics = json.loads(payload)
```

Avoid `read()` for large datasets, model files, archives, or unbounded user-selected paths. Prefer `open()` or `DVCFileSystem` for those cases.

## Resolving a Remote URL

Use `dvc.api.get_url()` when a downstream tool needs the storage URL for a tracked output.

```python
import dvc.api

url = dvc.api.get_url("models/model.pkl", repo=".", remote="storage")
```

Important gotcha: `get_url()` does not verify that the object exists in remote storage. It resolves the URL from DVC metadata and storage mapping. If your workflow requires proof, perform an explicit existence check with the relevant storage client or a DVC remote operation that is safe for the task.

## DVCFileSystem Entry Point

`DVCFileSystem` is exposed as `dvc.api.DVCFileSystem` and wraps DVC plus Git-tracked files in a fsspec-style filesystem.

```python
from dvc.api import DVCFileSystem

fs = DVCFileSystem(repo="/path/to/project", rev="main", remote="storage")
try:
    for info in fs.ls("data", detail=True):
        print(info["name"], info.get("type"), info.get("size"), info.get("dvc_info"))
finally:
    fs.close()
```

Verified constructor parameters include:

```python
DVCFileSystem(
    repo=None,
    rev=None,
    subrepos=False,
    repo_factory=None,
    fo=None,
    target_options=None,
    target_protocol=None,
    config=None,
    remote=None,
    remote_config=None,
    **kwargs,
)
```

Key behavior:

- `repo` may be a `Repo` instance, local path, URL, or omitted for the current DVC project.
- `fo` and `url` in `kwargs` are compatibility aliases for the repo location.
- `rev` controls Git revision selection. For local repos, unspecified `rev` uses the working directory; for remote repos it defaults to the default branch behavior.
- `subrepos=True` lets the filesystem traverse nested DVC repos.
- `fs.open(path, mode="rb")` is read-only at the underlying DVC filesystem layer. Non-read write modes raise a read-only `OSError`.
- `ls()`, `info()`, `exists()`, `glob()`, `walk()`, `get()`, `get_file()`, `du()`, and `isdvc()` are appropriate for directory/glob workflows.
- `info()` dictionaries can include `dvc_info`, `fs_info`, `type`, `size`, `md5`, and `isexec`, depending on whether the path is DVC-tracked, Git/workspace-backed, or both.
- `close()` releases the internal repo stack; call it explicitly in long-lived scripts.

## fsspec-Style Workflows

Use `DVCFileSystem` when an agent needs to select among many paths before opening them.

```python
from dvc.api import DVCFileSystem

fs = DVCFileSystem(repo=".", rev="HEAD")
try:
    candidates = fs.glob("data/**/*.csv")
    for path in candidates:
        if fs.isdir(path):
            continue
        with fs.open(path, mode="rb") as stream:
            consume_bytes(path, stream)
finally:
    fs.close()
```

For downloads, be explicit:

```python
fs.get("data/prepared", "./prepared-copy", recursive=True)
```

Downloading can transfer data from cache or remote storage. Do not call `get()` in a helper or agent action unless the user has selected an output path and the task requires materializing files.

## DVCPath and UPath

DVC also includes a `DVCPath` implementation for UPath-style usage, with examples such as:

```python
from upath import UPath

local = UPath("dvc://path/to/local/repo")
remote = UPath("dvc+https://github.com/iterative/example-get-started", rev="main")
```

Use this only when the target environment has compatible UPath/fsspec dependencies. For general agent automation, `dvc.api.DVCFileSystem` is the more direct public entry point.

## `repo`, `rev`, `remote`, `config`, and `remote_config`

These parameters appear across the Python access API:

- `repo`: local DVC project path, Git URL, SSH Git URL, or omitted current project discovery.
- `rev`: Git revision, tag, branch, commit, or DVC experiment name where applicable.
- `remote`: DVC remote name used to resolve or fetch data.
- `config`: dictionary merged into repo config for this Python operation.
- `remote_config`: dictionary passed to the selected remote for this operation.

Credential guidance:

- Prefer existing DVC config, environment variables, cloud-native credential providers, or short-lived values passed by the user.
- Never write secrets into generated skill content or reusable helper defaults.
- Do not assume optional remote backends are installed. The DVC package advertises extras such as `s3`, `gs`, `azure`, `ssh`, `gdrive`, `webdav`, `webhdfs`, `hdfs`, and `oss`, but they are not guaranteed by the base install.

## Local vs Remote Data

DVC metadata can identify an output even when bytes are missing locally or remotely.

- `status()` and `diff()` answer metadata/workspace questions.
- `get_url()` returns where data should live according to metadata and remote mapping.
- `open()`/`read()`/`DVCFileSystem.open()` need actual bytes in cache or remote storage.
- `pull()`/`get()`/`get_file()` may download or materialize data and should require explicit user intent.
