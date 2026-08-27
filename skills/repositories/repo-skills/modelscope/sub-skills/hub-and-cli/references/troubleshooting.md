# Hub and CLI troubleshooting

This guide covers the failure modes most likely to block ModelScope Hub, CLI, cache, local/offline, and authentication workflows.

## Quick triage checklist

Collect these facts before changing anything:

```bash
python - <<'PY'
import importlib.util
print('modelscope importable:', importlib.util.find_spec('modelscope') is not None)
print('modelscope_hub importable:', importlib.util.find_spec('modelscope_hub') is not None)
PY
modelscope --help || true
ms --help || true
modelscope download --help || true
modelscope cache --help || true
```

Then record:

- repo id, repo type, revision, and explicit file paths/patterns;
- whether the repo is public, private, gated, or in another account/site;
- `cache_dir`, `local_dir`, `MODELSCOPE_CACHE`, and `MS_CACHE_HOME` values;
- `local_files_only` / offline requirement;
- endpoint or domain settings;
- whether a token is passed, persisted, or intentionally absent.

Do not print token values. Print only whether a token is present.

## `modelscope_hub` missing or CLI entry points missing

Symptoms:

- `ModuleNotFoundError: No module named 'modelscope_hub'` while importing `modelscope.hub.*` or running `modelscope`.
- `modelscope: command not found` or `ms: command not found`.
- `python -m modelscope.cli.cli ...` fails before command parsing.

Likely causes:

- The ModelScope checkout/package is importable from source, but its declared Hub dependency is not installed.
- The package was installed without console scripts in the active environment.
- A different Python environment is being used for `python` vs `modelscope`.

Actions:

```bash
python - <<'PY'
from importlib import metadata
for name in ('modelscope', 'modelscope-hub'):
    try:
        print(name, metadata.version(name))
    except metadata.PackageNotFoundError:
        print(name, 'not installed')
PY
python -m pip install 'modelscope-hub>=0.2.0'
python -m pip install --upgrade modelscope
python -m modelscope.cli.cli --help
```

If console scripts are missing but module execution works, use `python -m modelscope.cli.cli <command>` as a temporary workaround and repair the environment later.

## Authentication and token failures

Symptoms:

- 401/403 responses, `AuthenticationError`, `PermissionDeniedError`, `NotLoginException`, or HTTP errors when accessing private files.
- Public downloads work but private downloads fail.
- Upload creates permission or unauthorized errors.

Actions:

1. Confirm whether the repo is private/gated and whether the token belongs to the same ModelScope site/endpoint as the repo.
2. Prefer an explicit token for one operation in Python:

   ```python
   snapshot_download(
       repo_id='owner/private-model',
       repo_type='model',
       revision='master',
       token=os.environ['MODELSCOPE_API_TOKEN'],
   )
   ```

3. If using CLI login, remember it persists credentials:

   ```bash
   modelscope login --token "$MODELSCOPE_API_TOKEN"
   ```

4. If credentials appear stale, inspect which credentials path is in use without printing contents. Check `MODELSCOPE_CREDENTIALS_PATH` and whether the process is running as the expected OS user.
5. For uploads, verify write permission and destination repo type; a token that can read a repo may not be allowed to upload.

Avoid:

- putting literal tokens in command history;
- mixing persisted login for one account with `endpoint=` for another site;
- copying credential files into project directories.

## Invalid repo id or wrong repo type

Symptoms:

- `InvalidParameter`, `NotExistError`, HTTP 404, or CLI parse errors.
- The same owner/name works in a browser but not in CLI/API.
- Dataset id supplied to model APIs or model id supplied to dataset APIs.

Checks:

- Repo ids are normally `owner/name`. The dry-run planner rejects empty owners/names, URL-like ids, local paths, and ids with spaces.
- Use `repo_type='model'` for model repos and `repo_type='dataset'` for dataset repos. Some commands also support `studio`, but deep studio deployment belongs to `../../serving-export-and-tools/SKILL.md`.
- Do not pass full web URLs to download helpers. Extract the owner/name part and pass endpoint separately only if needed.

Examples:

```python
snapshot_download(repo_id='Qwen/Qwen3-0.6B', repo_type='model')
dataset_snapshot_download(repo_id='owner/dataset-name')
model_file_download('Qwen/Qwen3-0.6B', 'README.md')
dataset_file_download('owner/dataset-name', 'data/train.jsonl')
```

## Revision not found or wrong default revision

Symptoms:

- `NotExistError`, no valid revision, 404, or missing files at a tag/branch.
- A file exists on the website but not at the revision used by code.
- Offline cache exists for one revision but `local_files_only=True` asks for another.

Actions:

1. Pass `revision=` explicitly for reproducibility.
2. Confirm the revision name belongs to the selected repo type and endpoint.
3. For model single-file downloads, remember that omitting `revision` can trigger release-mode resolution; pass a known branch/tag if the exact revision matters.
4. If using HuggingFace-like inputs through ModelScope patches, `main` may be normalized to `master` in some compatibility paths. Use the exact ModelScope revision where possible.

## Network, timeout, and server errors

Symptoms:

- `NetworkError`, `RequestTimeoutError`, `ServerError`, `FileDownloadError`, incomplete downloads, repeated retries, or `ReadTimeout`.

Actions:

- Retry later or with lower parallelism:

  ```python
  snapshot_download('owner/name', revision='master', max_workers=1)
  ```

- Keep the same `cache_dir` so partial or completed files can be reused if the downloader supports it.
- Confirm proxy/firewall/DNS settings outside ModelScope if all network requests fail.
- For heavy Hub API operations, ModelScope exposes timeout/retry tunables such as `MODELSCOPE_API_HTTP_CLIENT_TIMEOUT`, `MODELSCOPE_API_HTTP_CLIENT_CONNECT_TIMEOUT`, and `API_HTTP_CLIENT_MAX_RETRIES`. Treat changes as process-level configuration; document them in the run log.
- If a file integrity error occurs, remove only the affected file/revision directory when known; avoid clearing the entire cache unless necessary and approved.

## Cache not reused or files downloaded twice

Symptoms:

- A previous download exists, but a new run downloads again.
- `local_files_only=True` fails even though a visually similar folder exists.
- `scan-cache` shows zero repos in one directory while files exist in another.

Likely causes:

- Mixed roots: `MODELSCOPE_CACHE`, `MS_CACHE_HOME`, explicit `cache_dir`, and default roots differ.
- Legacy SDK layout (`{cache}/hub/...` or `{cache}/{owner}/{name}`) vs modern `modelscope_hub` layout (`{cache}/models/{owner}--{name}/snapshots/...`).
- Repo type mismatch (`models` vs `datasets`).
- Revision mismatch.
- Empty legacy directory ignored by the reuse probe.

Actions:

```bash
echo "MODELSCOPE_CACHE=${MODELSCOPE_CACHE:-<unset>}"
echo "MS_CACHE_HOME=${MS_CACHE_HOME:-<unset>}"
modelscope cache scan --dir "${MODELSCOPE_CACHE:-$HOME/.cache/modelscope}" || true
modelscope scan-cache --dir "${MODELSCOPE_CACHE:-$HOME/.cache/modelscope/hub}" || true
```

Then use one explicit root:

```python
CACHE = '/mnt/modelscope-cache'
snapshot_download('owner/name', repo_type='model', revision='master', cache_dir=CACHE)
snapshot_download('owner/name', repo_type='model', revision='master', cache_dir=CACHE, local_files_only=True)
```

If a legacy cache should be reused, verify it is non-empty and that no modern known layout for the same repo already exists. The compatibility wrapper intentionally lets the modern layout win when both are present.

## `local_dir` versus `cache_dir` confusion

Symptoms:

- Code expects files in `cache_dir` but the returned path points elsewhere.
- User supplies both `local_dir` and `cache_dir` and later cannot find cache entries.

Rule of thumb:

- `local_dir` is for a user-visible copy/location.
- `cache_dir` is for ModelScope/modelscope_hub-managed reuse.
- If both are provided, `local_dir` takes precedence for the output location in the compatibility layer and CLI docs. Do not assume `cache_dir` is populated in the way a later cache-only run expects.

Safer patterns:

```python
# Cache-managed reuse.
model_dir = snapshot_download('owner/name', repo_type='model', cache_dir='/mnt/ms-cache')

# Project-visible copy.
model_dir = snapshot_download('owner/name', repo_type='model', local_dir='./models/owner-name')
```

## Offline/local-only failures

Symptoms:

- `CacheNotFound`, `ValueError`, or `NotExistError` with `local_files_only=True`.
- Private repo offline test fails before any network call.

Expected behavior:

`local_files_only=True` never downloads. It only succeeds if the exact repo type, repo id, revision, and file/pattern set can be satisfied from the selected local/cache path.

Actions:

1. Run one online population step with the same cache/local settings.
2. Re-run with `local_files_only=True` and the same revision.
3. If using a visible `local_dir`, point subsequent offline operations at that `local_dir` or use the same `cache_dir` that was populated.
4. Avoid changing include/exclude filters between populate and offline runs unless you know all newly requested files are already present.

## Include/exclude pattern surprises

Symptoms:

- Too many files downloaded.
- Expected files missing.
- Shell expands `*.json` before the CLI sees it.

Actions:

- Quote patterns in shell commands: `--include '*.json' 'tokenizer*'`.
- Prefer `allow_patterns`/`ignore_patterns` in Python for new code.
- Do not combine explicit file paths with patterns if exact behavior matters; command docs state patterns can be ignored when explicit files are specified.
- For model inference, include not only weights but also `configuration.json`, tokenizer/preprocessor files, custom code when trusted, and any task-specific assets. Route inference planning to `../../pipelines-and-models/SKILL.md`.

## Endpoint and site confusion

Symptoms:

- Token accepted by one operation but repo missing in another.
- Public repo id appears different between `modelscope.cn` and `modelscope.ai`.
- Browser URL and API endpoint do not match.

Actions:

- Decide whether the workflow targets the default China site, international site, or a private endpoint.
- Pass endpoint explicitly in Python if needed:

  ```python
  HubApi(endpoint='https://www.modelscope.cn', token=token)
  snapshot_download('owner/name', endpoint='https://www.modelscope.cn', token=token)
  ```

- Check `MODELSCOPE_DOMAIN`, `MODELSCOPE_PREFER_AI_SITE`, and CLI `--endpoint` if available.
- Keep credentials, endpoint, and repo id from the same site/account namespace.

## Cache clearing risks

Symptoms:

- User asks to free disk space or fix corruption.
- `clear-cache` prompts to delete all models/datasets.

Safe order:

1. Scan cache first.
2. Clear a single model/dataset/repo if possible.
3. Back up or record the path if the cache is expensive to rebuild.
4. Only clear the entire cache with explicit approval.

Legacy `clear-cache` behavior:

- `--model owner/name` removes model cache and temporary cache for that id.
- `--dataset owner/name` removes dataset cache and temporary cache for that id.
- no id targets the entire ModelScope cache and prompts interactively.

## Upload failures

Symptoms:

- permission denied, repo not found, invalid repo id, large file/LFS errors, timeouts, or upload retries.

Actions:

- Confirm the repo exists or intentionally call `HubApi.create_repo(..., exist_ok=True)`.
- Confirm `repo_type` (`model` or `dataset`) and token write permission.
- Set `path_in_repo` deliberately; do not upload a whole working directory root by accident.
- Use a meaningful `commit_message`.
- For large files or many files, expect modelscope_hub upload validation, retry, and LFS decisions. If upload limits are hit, reduce the upload set or split commits.
- Do not retry destructive/overwrite uploads automatically without user approval.

## File locks and concurrent downloads

Symptoms:

- Processes wait on lock files or concurrent downloads race.
- Shared NFS cache has stale file handle warnings.

Actions:

- Prefer one writer per repo/revision/cache root at a time.
- If lock problems happen on unusual filesystems, move `MODELSCOPE_CACHE` to a local disk for the download, then copy or mount read-only for consumers.
- The repository contains a file-lock environment toggle used in tests (`MODELSCOPE_HUB_FILE_LOCK=false`), but disabling locks can corrupt concurrent cache writes. Use only for controlled debugging, not normal operation.

## When to route away

- Download completed and the user wants to run inference: `../../pipelines-and-models/SKILL.md`.
- Dataset snapshot completed and the user wants to load/filter/stream/train on it: `../../datasets-config/SKILL.md`.
- The user wants `modelscope server`, vLLM serving, studio deployment, ONNX export, or checkpoint conversion: `../../serving-export-and-tools/SKILL.md`.
