---
name: sharing-cli-cache
description: "Share Datasets datasets to the Hub, operate datasets-cli, manage
  cache/download/offline settings, and troubleshoot safe Hub/cache workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Sharing, CLI, and Cache Operations

Use this sub-skill when the task involves publishing datasets to the Hugging Face Hub, preparing dataset repository metadata, running `datasets-cli`, controlling caches/downloads/offline mode, or diagnosing operational issues around auth, revisions, PRs, sharding, storage, and local filesystems.

## Route First

- For loading local files or Hub datasets, route to `../loading-local-hub/SKILL.md`.
- For `Features`, schema, media columns, and format conversion, route to `../features-formats/SKILL.md`.
- For `map`, streaming, iterable datasets, shuffling, multiprocessing transforms, and pipeline performance, route to `../processing-streaming/SKILL.md`.
- Stay here for `Dataset.push_to_hub`, `DatasetDict.push_to_hub`, dataset cards, repository structure, `datasets-cli`, `DownloadConfig`, cache directories, offline mode, and safe deletion from the Hub.

## What To Read

- Read `references/sharing-and-hub.md` for Hub upload planning, `push_to_hub` arguments, repository/card structure, auth/revision/PR choices, and private multi-config uploads.
- Read `references/cli-cache-reference.md` for `datasets-cli env`, `datasets-cli test`, `datasets-cli delete_from_hub`, cache environment variables, `DownloadConfig`, offline/local-files behavior, and fsspec storage options.
- Read `references/troubleshooting.md` when diagnosing token/private repo errors, dataset card metadata, sharding/embed problems, corrupted cache, offline surprises, fsspec auth, or destructive operations.
- Use `scripts/cli_cache_smoke.py --help` for a safe, local diagnostic helper that summarizes CLI/cache/offline settings and can optionally run non-destructive `datasets-cli` help/env commands.
- Copy or adapt `scripts/dataset_card_minimal.md` as a self-contained starting README template for Hub dataset repositories.

## Safety Defaults

- Treat upload/delete commands as network-mutating unless they are `--help`, `env`, or an explicit local dry-run helper.
- Never paste access tokens into logs, Markdown, command history, or dataset cards; prefer `token=True`, environment-backed auth, or the Hub login flow.
- Use `create_pr=True` or a PR revision for risky Hub updates when the caller does not own the target repo or wants review before merge.
- For destructive `datasets-cli delete_from_hub`, confirm the dataset id, config name, revision, and that the command deletes only the intended supported data-only configuration.
- Keep cache cleanup scoped: use a dedicated `cache_dir` for tests and inspect before deleting shared cache directories.
