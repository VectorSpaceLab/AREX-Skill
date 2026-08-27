---
name: hub-and-cli
description: "Use ModelScope Hub, cache, download/upload, and CLI workflows
  safely from the modelscope package."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ModelScope Hub and CLI

Use this sub-skill when the task is about ModelScope Hub access, the `modelscope`/`ms` command line, downloading repositories or files, upload command selection, authentication boundaries, endpoint/cache settings, offline cache reuse, or cache troubleshooting.

## Fast routing

- Need CLI command selection, help boundaries, download/cache syntax, or legacy command aliases: read [CLI reference](references/cli-reference.md).
- Need Python APIs such as `snapshot_download`, `dataset_snapshot_download`, `model_file_download`, `dataset_file_download`, `HubApi`, credentials, endpoint variables, or `modelscope_hub` compatibility behavior: read [Hub API reference](references/hub-api-reference.md).
- Need to diagnose auth, repo id/revision, endpoint, network, cache, offline, missing `modelscope_hub`, or `local_dir`/`cache_dir` confusion: read [troubleshooting](references/troubleshooting.md).
- Need a safe dry-run plan before downloading: run `python scripts/plan_download.py --help`, then use the generated CLI command or Python snippet after approval. The script performs no network calls.

## Boundaries and cross-skill routes

- This sub-skill stops at obtaining or managing local Hub files. For pipeline inference after a model download, route to `../pipelines-and-models/SKILL.md`.
- For `MsDataset.load`, dataset streaming, dataset recipe validation, or config/file I/O after a dataset snapshot is available, route to `../datasets-config/SKILL.md`.
- For server/studio deployment details, vLLM integration, export, and large checkpoint tools, route to `../serving-export-and-tools/SKILL.md`.
- Treat uploads, cache clearing, login persistence, and endpoint changes as operations with external side effects. Ask for explicit user approval before mutating remote Hub repositories, deleting caches, or saving credentials.

## Working checklist

1. Identify the interface: `modelscope`/`ms` CLI, Python download helper, or `HubApi`.
2. Confirm repo id shape (`owner/name`), repo type (`model` or `dataset` for most downloads), revision, and whether the target is public or private.
3. Decide storage semantics: use `local_dir` for a user-visible copy, `cache_dir`/`MODELSCOPE_CACHE` for reusable cache, and `local_files_only=True` only when the cache is already populated.
4. Avoid exposing tokens. Prefer environment variables and Python `token=` parameters over literal tokens in shell history.
5. For include/exclude filters, quote glob patterns in shell commands and remember that explicit file paths take precedence over patterns.
