# Hub API reference

ModelScope keeps legacy import paths while delegating most Hub work to the separate `modelscope_hub` package. Use this reference for Python workflows, cache semantics, credentials, endpoint selection, and compatibility pitfalls.

## Import surface

Common public imports:

```python
from modelscope import snapshot_download, model_file_download
from modelscope.hub.snapshot_download import dataset_snapshot_download
from modelscope.hub.file_download import dataset_file_download
from modelscope.hub.api import HubApi, ModelScopeConfig
```

If these imports fail because `modelscope_hub` is missing, install or repair the declared Hub dependency before debugging higher-level code:

```bash
python -m pip install 'modelscope-hub>=0.2.0'
```

## Snapshot downloads

### Model snapshot

Current compatibility signature:

```python
snapshot_download(
    model_id=None,
    revision=None,
    cache_dir=None,
    user_agent=None,
    local_files_only=False,
    cookies=None,
    ignore_file_pattern=None,
    allow_file_pattern=None,
    local_dir=None,
    allow_patterns=None,
    ignore_patterns=None,
    max_workers=None,
    repo_id=None,
    repo_type=None,
    progress_callbacks=None,
    token=None,
    endpoint=None,
) -> str
```

Minimal model snapshot:

```python
from modelscope import snapshot_download

model_dir = snapshot_download(
    repo_id='Qwen/Qwen3-0.6B',
    repo_type='model',
    revision='master',
)
```

Legacy positional form is preserved for backward compatibility:

```python
model_dir = snapshot_download('Qwen/Qwen3-0.6B', revision='master')
```

Prefer the explicit `repo_id=` + `repo_type=` form in new code because it matches modern CLI terminology and makes model-vs-dataset decisions visible.

### Dataset snapshot

Current compatibility signature:

```python
dataset_snapshot_download(
    dataset_id=None,
    revision=None,
    cache_dir=None,
    local_dir=None,
    allow_file_pattern=None,
    ignore_file_pattern=None,
    allow_patterns=None,
    ignore_patterns=None,
    max_workers=None,
    cookies=None,
    repo_id=None,
    token=None,
    endpoint=None,
) -> str
```

Example:

```python
from modelscope.hub.snapshot_download import dataset_snapshot_download

dataset_dir = dataset_snapshot_download(
    repo_id='owner/dataset-name',
    revision='master',
    allow_patterns=['*.jsonl', '*.csv'],
)
```

For dataset loading after the files exist, route to `../../datasets-config/SKILL.md`.

## Single-file downloads

### Model file

Current compatibility signature:

```python
model_file_download(
    model_id: str,
    file_path: str,
    revision: str = None,
    *,
    cache_dir: str = None,
    local_dir: str = None,
    cookies: dict = None,
    token: str = None,
    endpoint: str = None,
    local_files_only: bool = False,
    user_agent=None,
) -> str
```

Example:

```python
from modelscope.hub.file_download import model_file_download

readme_path = model_file_download(
    'Qwen/Qwen3-0.6B',
    'README.md',
    revision='master',
    cache_dir='/mnt/modelscope-cache',
)
```

When `revision` is omitted, `model_file_download` attempts release-mode revision resolution through `HubApi.get_valid_revision_detail`; if that lookup fails, the delegated downloader still receives the unresolved revision. For deterministic runs, pass a revision explicitly.

### Dataset file

Current compatibility signature:

```python
dataset_file_download(
    dataset_id: str,
    file_path: str,
    *,
    cache_dir: str = None,
    local_dir: str = None,
    revision: str = None,
    cookies: dict = None,
    token: str = None,
    endpoint: str = None,
    local_files_only: bool = False,
    user_agent=None,
) -> str
```

Example:

```python
from modelscope.hub.file_download import dataset_file_download

path = dataset_file_download(
    'owner/dataset-name',
    'metadata/train.jsonl',
    revision='master',
    local_files_only=True,
)
```

## Include/exclude filters

Both snapshot functions accept legacy names (`allow_file_pattern`, `ignore_file_pattern`) and modern names (`allow_patterns`, `ignore_patterns`). Prefer modern names in new code:

```python
model_dir = snapshot_download(
    repo_id='Qwen/Qwen3-0.6B',
    repo_type='model',
    revision='master',
    allow_patterns=['*.json', 'tokenizer*'],
    ignore_patterns=['*.bin', 'onnx/*'],
)
```

Use patterns for repository-wide filtering. Use single-file APIs or explicit CLI file arguments when you know exact paths. Do not assume filters apply to explicit file lists; command documentation says patterns can be ignored when explicit file paths are specified.

## Cache and local directory semantics

| Option | Use when | Notes |
| --- | --- | --- |
| `cache_dir=` / `--cache-dir` | You want reusable cache-managed storage. | Overrides the environment cache root for that call. |
| `MODELSCOPE_CACHE` | You want one cache root for a process or shell session. | Legacy `clear-cache` and cache helpers read this variable. |
| `MS_CACHE_HOME` | You need legacy compatibility. | `modelscope.hub` bridges `MS_CACHE_HOME` to the new Hub config only when `MODELSCOPE_CACHE` is not set. |
| `local_dir=` / `--local-dir` | You want a stable visible folder rather than an opaque cache path. | If both local and cache directories are supplied, local-dir behavior takes precedence for the returned/visible files. |
| `local_files_only=True` | You require offline/cache-only behavior. | It fails if the requested repo/revision/file is absent from the selected cache/local path. It does not populate cache. |

Default cache roots differ across compatibility layers:

- Legacy SDK helpers report `~/.cache/modelscope/hub` and use `models/` or `datasets/` below it for some clear-cache behavior.
- The delegated `modelscope_hub` downloader uses `~/.cache/modelscope` by default when `MODELSCOPE_CACHE` is unset.
- ModelScope includes a legacy-cache reuse probe so old layouts can still be reused when the modern hub layout is absent.

Practical rule: set `MODELSCOPE_CACHE` or pass `cache_dir=` consistently in every CLI/Python/serving process involved in one workflow.

## Cache layouts and legacy reuse

Modern `modelscope_hub` layouts include paths conceptually like:

- `{cache}/models/{owner}--{name}/snapshots/{revision}/...`
- `{cache}/datasets/{owner}--{name}/snapshots/{revision}/...`
- `{cache}/{type}s/{owner}/{safe_name}/...` for layouts the delegated hub already knows how to reuse, with dots in the name transformed to a safe variant.

Older ModelScope SDKs also stored repos in layouts such as:

- `{cache}/{owner}/{name}/...`
- `{cache}/hub/{owner}/{name}/...`
- `{cache}/{type}s/{owner}/{name}/...`

The compatibility wrapper searches for non-empty legacy directories that `modelscope_hub` would otherwise miss. It returns a legacy path as `local_dir` only when a modern known layout is absent, avoiding accidental override of the delegated hub's own cache detection. If cache reuse is surprising, inspect both the modern and legacy roots before re-downloading.

## Offline/local-only workflows

Use offline mode only after populating the relevant cache once:

```python
# Online/populate step, performed once with network access.
snapshot_download(
    repo_id='Qwen/Qwen3-0.6B',
    repo_type='model',
    revision='master',
    cache_dir='/mnt/modelscope-cache',
    allow_patterns=['README.md', '*.json'],
)

# Later offline step.
model_dir = snapshot_download(
    repo_id='Qwen/Qwen3-0.6B',
    repo_type='model',
    revision='master',
    cache_dir='/mnt/modelscope-cache',
    local_files_only=True,
    allow_patterns=['README.md', '*.json'],
)
```

`local_files_only=True` is an assertion that the file already exists in the selected local/cache layout. Expected failures for missing offline content include `CacheNotFound`, `ValueError`, or delegated Hub errors depending on installed `modelscope_hub` version.

## Authentication and credentials

Common approaches:

```python
from modelscope.hub.api import HubApi

api = HubApi(token='...')          # one API object, avoid printing the token
api.login('...')                   # persists credentials through Hub config
```

Credential helpers preserve legacy names:

```python
from modelscope.hub.api import ModelScopeConfig

ModelScopeConfig.save_git_token(token)
loaded = ModelScopeConfig.get_git_token()
```

`ModelScopeConfig.save_token()` and `ModelScopeConfig.get_token()` remain as deprecated aliases for git-token methods. Avoid them in new code unless maintaining legacy call sites.

Credential/config variables:

| Variable | Purpose |
| --- | --- |
| `MODELSCOPE_CREDENTIALS_PATH` | Overrides the credentials/config location bridged into `modelscope_hub` config. It may point at a directory or at a legacy credentials file path. |
| `MODELSCOPE_API_TOKEN` | Used by several higher-level ModelScope commands and training/serving helpers as an access-token environment variable. For core Hub download helpers, prefer explicit `token=` or persisted login unless the installed CLI documents this variable. |
| `MODELSCOPE_CACHE` | Primary cache root override. |
| `MS_CACHE_HOME` | Legacy cache alias bridged only when `MODELSCOPE_CACHE` is unset. |

Security guidance: do not hard-code tokens in skill files, shell history, notebooks, or logs. When writing automation, read tokens from environment or secret storage and pass them as `token=`.

## Endpoint selection

Python download and API helpers accept `endpoint=`:

```python
model_dir = snapshot_download(
    repo_id='owner/name',
    repo_type='model',
    endpoint='https://www.modelscope.cn',
    token=os.environ.get('MODELSCOPE_API_TOKEN'),
)
```

Endpoint-related variables/constants in the package include:

| Setting | Meaning |
| --- | --- |
| `MODELSCOPE_DOMAIN` | Environment domain consulted by endpoint resolution helpers when no explicit endpoint is passed. |
| `MODELSCOPE_PREFER_AI_SITE` | Site preference switch delegated from `modelscope_hub` constants for choosing the international/AI site in supported flows. |
| `HUB_DATASET_ENDPOINT` | Dataset subsystem endpoint override; route dataset loading details to `../../datasets-config/SKILL.md`. |

Use explicit `endpoint=` only when the user knows which site/account namespace they intend. Endpoint mismatches can look like authentication failures or missing repositories because tokens and repo ids may belong to a different site.

## HubApi compatibility layer

`HubApi` subclasses `modelscope_hub.compat.LegacyHubApi`, preserves legacy attributes (`endpoint`, `token`, `timeout`, `max_retries`, `headers`), and proxies unknown public attributes to the internal new `modelscope_hub.HubApi` object.

Stable patterns:

```python
from modelscope.hub.api import HubApi

api = HubApi(token=os.environ.get('MODELSCOPE_API_TOKEN'))

# Read/list/info patterns, exact method availability may depend on modelscope_hub.
models = api.list_models(owner_or_group='damo')
info = api.model_info('owner/model-name')
exists = api.file_exists('owner/model-name', 'README.md', revision='master')

# Repository creation/upload patterns; remote side effects.
url = api.create_repo(repo_id='owner/name', repo_type='model', exist_ok=True)
commit = api.upload_folder(
    repo_id='owner/name',
    repo_type='model',
    folder_path='local-folder',
    path_in_repo='.',
    commit_message='Upload local folder',
)
```

Upload shims:

- `HubApi.upload_folder(repo_id, folder_path=None, **kwargs)` delegates to the new Hub API and defaults `repo_type` to `model` if omitted.
- `HubApi.upload_file(repo_id=None, path_or_fileobj=None, path_in_repo=None, **kwargs)` also defaults `repo_type` to `model` if omitted.
- If a `token=` different from the object's configured token is passed to upload methods, the shim creates a temporary new Hub API object with that token.

Before upload, confirm `repo_type`, `path_in_repo`, commit message, overwrite semantics, size/LFS constraints, and token permissions.

## Progress callbacks and concurrency

`snapshot_download` accepts `max_workers` and `progress_callbacks`. If `max_workers` is omitted, the compatibility wrapper forwards `4`. Progress callbacks are classes, not instances, and are instantiated per file. Treat high concurrency as optional and network-dependent; reduce workers when debugging transient connection or lock issues.

## Error classes to catch

The legacy error module re-exports structured `modelscope_hub` errors and aliases:

```python
from modelscope.hub.errors import (
    AuthenticationError,
    CacheNotFound,
    FileIntegrityError,
    HubError,
    InvalidParameter,
    NetworkError,
    NotExistError,
    PermissionDeniedError,
    RequestTimeoutError,
    ServerError,
)
```

Use broad `HubError` only at workflow boundaries. For troubleshooting, preserve the original exception text, repo id, repo type, revision, cache/local directory, endpoint, and whether `local_files_only` was set.
