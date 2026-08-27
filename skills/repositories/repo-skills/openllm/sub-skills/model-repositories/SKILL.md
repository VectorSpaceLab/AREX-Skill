---
name: model-repositories
description: "Guides OpenLLM model repository management, custom public repo
  URLs, model listing and lookup, and troubleshooting for `openllm repo` and
  `openllm model` commands."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Model Repositories

Use this sub-skill when the task is about the catalog of OpenLLM Bentos rather than running a server.

## Typical triggers

- `openllm repo list|add|remove|update|default`
- `openllm model list|get`
- Parsing `repo_alias/model:version` or `MODEL:VERSION` forms
- Custom public repository setup
- Missing, ambiguous, or stale model catalog entries

## What this route covers

- Repository configuration defaults and the on-disk cache layout.
- URL parsing for public Git repositories.
- How `list_bento` locates Bentos and de-duplicates aliases.
- Model table output and hidden readme output behavior.
- Troubleshooting for invalid repo URLs, clone failures, stale caches, missing models, and ambiguous tags.

## Read next

- [references/repo-and-model-cli.md](references/repo-and-model-cli.md) for the command map and usage patterns.
- [references/repository-format.md](references/repository-format.md) for the custom repo layout OpenLLM expects.
- [references/api-reference.md](references/api-reference.md) for verified helper signatures and return shapes.
- [references/troubleshooting.md](references/troubleshooting.md) for the common failure modes.
- [scripts/validate_repo_url.py](scripts/validate_repo_url.py) to validate a repository URL without cloning.
- [scripts/inspect_model_catalog.py](scripts/inspect_model_catalog.py) to inspect a local Bentos catalog tree.

## Boundaries

Do not route local server startup or chat to this sub-skill. If the issue is a local readiness or resource problem, use `local-serving` or `environment-maintenance`. If the issue is BentoCloud deployment, use `cloud-deployment`.
