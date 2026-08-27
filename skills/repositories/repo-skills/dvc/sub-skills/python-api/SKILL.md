---
name: python-api
description: "Use DVC as a Python library for streaming reads, fsspec filesystem
  access, Repo automation, params/metrics/experiments inspection, and safe
  exception handling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DVC Python API

Use this sub-skill when an agent needs to call DVC from Python instead of shelling out to the `dvc` console script. It covers the supported `dvc.api` surface, `DVCFileSystem`/fsspec-style access, selected `Repo` methods for scripted automation, and common failure modes.

## Start Here

- For one tracked file, prefer `dvc.api.open()` when streaming and `dvc.api.read()` only when loading the full file is acceptable.
- For directory listings, globs, recursive downloads, or path metadata, prefer `dvc.api.DVCFileSystem` over `dvc.api.read()`.
- For pipeline mutation or automation, use `dvc.repo.Repo` as a context manager and call public methods such as `add()`, `run()`, `reproduce()`, `status()`, `push()`, `pull()`, and `diff()`.
- For params, metrics, artifacts, and experiments, use the public `dvc.api` helpers first; drop to `Repo` only when the helper does not expose the needed operation.
- For remote credentials/backends, remember extras such as `s3`, `gs`, `azure`, `ssh`, `gdrive`, `webdav`, `webhdfs`, `hdfs`, and `oss` are optional and may not be installed.

## References

- `references/api-reference.md` lists public signatures, return shapes, and safe usage patterns.
- `references/filesystem-access.md` explains streaming reads, `get_url()`, `DVCFileSystem`, fsspec-style workflows, revisions, remotes, and config injection.
- `references/troubleshooting.md` maps common Python API errors to fixes.
- `scripts/dvc_api_smoke.py` is a safe helper for verifying the installed package, opening a user-supplied tracked file, and showing optional metadata.

## Routing Notes

- Use `../data-and-pipelines/SKILL.md` for CLI/stage concepts before translating them to `Repo.run()` or `Repo.reproduce()`.
- Use the sibling `metrics-params-plots` sub-skill for metric, parameter, and plot semantics when available; this sub-skill only covers Python call shapes.
- Use `../experiments/SKILL.md` for experiment workflows; this sub-skill covers `dvc.api.exp_show()` and `dvc.api.exp_save()` integration points.
- Use `../remotes-and-cache/SKILL.md` for remote configuration, cache, optional storage extras, and push/pull behavior.

## Safe Defaults

- Do not import private DVC modules for user-facing automation unless you are diagnosing DVC internals; prefer `dvc.api` and `dvc.repo.Repo`.
- Do not call `dvc.api.open()` outside a `with` block; it intentionally raises `AttributeError` on attribute access before entering the context.
- Do not use write modes with `dvc.api.open()`; only read modes are supported and non-read modes raise `ValueError`.
- Do not treat `dvc.api.get_url()` as proof that a remote object exists; it resolves the configured cache/remote URL for a tracked output.
- Do not load large files with `dvc.api.read()` when a streaming reader or `DVCFileSystem.open()` would avoid memory pressure.
