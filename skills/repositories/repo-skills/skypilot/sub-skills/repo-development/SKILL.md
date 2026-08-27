---
name: repo-development
description: "Modify the SkyPilot repository safely with structure, style,
  tests, API compatibility, protobuf, dashboard, and PR guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SkyPilot Repo Development

Use this sub-skill when the user wants to change SkyPilot source code, tests, docs, packaging/dependency files, API server schemas, protobufs, dashboard code, CI config, or contribution/PR workflows. This is for maintainer work in a SkyPilot checkout, not for end-user cluster, job, service, storage, or SDK usage.

## Start Here

1. Read [references/development-guide.md](references/development-guide.md) for the repository map, coding conventions, focused validation strategy, protobuf/dashboard workflows, API compatibility rules, critical paths, and PR handoff checklist.
2. Read [references/troubleshooting.md](references/troubleshooting.md) when formatter versions, protobuf generation, API compatibility, dashboard builds, import-time behavior, smoke tests, or Buildkite status checks fail.
3. Run [scripts/repo_sanity.py](scripts/repo_sanity.py) with `--repo-root .` to inspect a checkout and print recommended commands for changed files. It reports only by default; it does not format, run broad tests, start API servers, contact clouds, or mutate the checkout.
4. Add `--check-import` only when a read-only `import sky` probe is safe in the current environment.

## Owns

- Source-editing workflow for `sky/`, `tests/`, `docs/source/`, `examples/`, `llm/`, `charts/`, `sky/dashboard/`, `sky/schemas/proto/`, packaging files, CI files, and maintainer scripts.
- Coding conventions: Google Python style, import placement, typing-only imports, `LazyImport`, TODO/FIXME attribution, exception usage, dependency pin rationale, and generated-file boundaries.
- Formatting/linting/test selection: `format.sh`, development tool versions, `pytest` unit targets, smoke test safety, dashboard lint/build/test commands, protobuf regeneration, and PR `Tested:` sections.
- API compatibility for client/server changes: `API_VERSION`, `MIN_COMPATIBLE_API_VERSION`, `@versions.minimal_api_version(...)`, payload defaults, remote API version branching, serialization compatibility, and backward compatibility tests.
- Critical maintainer paths: managed jobs recovery, API server performance/robustness, CLI/SDK UX, cloud/backend provisioning, and generated protobuf/dashboard coupling.

## Route Elsewhere

- Task YAML authoring or parser-only validation: `../task-yaml/SKILL.md`.
- Interactive cluster commands, status/logs, launch/exec/stop/down behavior: `../cluster-operations/SKILL.md`.
- Managed job launch, queue, recovery, logs, cancellation, and pools: `../managed-jobs/SKILL.md`.
- SkyServe service YAMLs, updates, replicas, autoscaling, and serving logs: `../serving/SKILL.md`.
- Cloud credentials, Kubernetes/Slurm/SSH, storage, volumes, GPU catalogs, and provider-specific triage: `../infrastructure-storage/SKILL.md`.
- Python SDK/API server usage without source edits: `../sdk-api-server/SKILL.md`.

## Operating Principles

- Start from the files changed, then select the smallest meaningful formatter/test/build commands; broaden only when risk or reviewers need it.
- Never run cloud-launching smoke tests, destructive cleanup, Helm upgrades, or credentialed provider checks unless the user explicitly asks and understands cost/resource effects.
- Treat `sky/schemas/generated/` as generated output; edit `.proto` sources and regenerate instead of hand-editing generated files.
- Restart the API server after source changes before manual API-server validation; rebuild dashboard assets first when dashboard source changed.
- For PR summaries, include a concrete `Tested:` section with commands actually run, skipped expensive checks, and any manual verification notes.
