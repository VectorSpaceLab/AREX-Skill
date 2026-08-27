---
name: remotes-and-cache
description: "Configure DVC remotes and cache behavior, move data with
  push/pull/fetch/gc, and diagnose remote backend dependency or configuration
  failures safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DVC Remotes and Cache

Use this sub-skill when a user asks how to configure DVC data remotes, choose remote URL schemes, push/pull/fetch tracked data, inspect cloud status, tune cache storage/link behavior, or troubleshoot missing optional remote backends.

## Route Here When

- The task mentions `dvc remote add`, `remote modify`, `remote default`, `remote list`, `remote remove`, or `remote rename`.
- The user needs safe guidance for `dvc push`, `dvc pull`, `dvc fetch`, `dvc status -c`, `dvc gc`, `dvc cache dir`, `cache.type`, or `dvc unprotect`.
- The user is diagnosing `RemoteMissingDepsError`, credential/auth issues, unsupported URL schemes, no default remote, missing cache objects, or link/relink behavior.
- The workflow uses `dvc import-url`, `dvc get`, `dvc get-url`, `dvc list-url`, or `dvc artifacts get` specifically because data is transferred through a remote or external URL.

## Route Elsewhere

- For `dvc add`, stages, `dvc repro`, pipeline outputs, or `.dvc`/`dvc.yaml` authoring that does not require remote/cache decisions, use the `data-and-pipelines` sub-skill.
- For Python API access such as `dvc.api.open()`, `dvc.api.get_url()`, `Repo.get()`, or `Artifacts.get()`, route to `python-api` after using this sub-skill only to identify remote/cache settings.
- Do not run real cloud/network transfers, credential prompts, or native repo remote tests from this skill. Prefer help output, config inspection, local filesystem remotes, and no-network diagnostics.

## Core Workflow

1. Identify whether the user needs a local filesystem remote, HTTP(S) URL, cloud/object-store backend, SSH/WebDAV/HDFS backend, or a `remote://name/path` reference layered on an existing remote.
2. Read `references/remote-workflows.md` for safe command recipes and validation commands before proposing any `push`, `pull`, `fetch`, `status -c`, `gc -c`, `import-url --to-remote`, or URL-transfer command.
3. Read `references/configuration.md` before editing config levels, `remote.<name>.*` options, `cache.dir`, `cache.type`, `cache.shared`, or protected-link behavior.
4. Run `python scripts/check_remote_support.py --scheme <scheme>` when optional backend availability is unclear; it inspects local Python distribution/import availability only and performs no network I/O.
5. Use `references/troubleshooting.md` to map symptoms to safe checks and fixes, especially for missing extras, credentials, no default remote, unsupported URL schemes, missing cache, and link/relink issues.

## Safe Defaults

- Prefer local filesystem remotes for examples: `dvc remote add -d localremote /path/to/dvc-remote` followed by `dvc remote list` and `dvc status -c`.
- Treat `dvc push`, `dvc pull`, `dvc fetch`, `dvc gc -c`, cloud `import-url`, `get-url`, and `list-url` as potentially network/credential operations unless the remote URL is local.
- Do not recommend `dvc[all]` unless the user explicitly needs multiple backends; map a missing backend to the narrow extra such as `dvc[s3]`, `dvc[gs]`, `dvc[azure]`, `dvc[ssh]`, `dvc[webdav]`, or `dvc[webhdfs]`.
- Use `--local` for credentials and machine-specific paths so secrets stay in `.dvc/config.local`; use project config for shareable remote names and non-secret URLs.
- For destructive cleanup, prefer `dvc gc --dry` first and explain that `dvc gc -c` can remove remote objects in addition to local cache objects.

## Evidence Base

This sub-skill is distilled from DVC command parsers and schemas for `remote`, `config`, `cache`, `push/pull/fetch/status`, `gc`, `get`, `get-url`, `import-url`, `list-url`, `artifacts get`, `unprotect`, config schema validation, filesystem resolution, README optional-extra guidance, and remote/cache tests. Runtime guidance is self-contained and does not require reopening those source files.
