---
name: dagster
description: "Use when working with Dagster OSS: assets, jobs, Definitions,
  config/resources, schedules/sensors, automation, CLI/local development,
  deployment operations, GraphQL/webserver, Pipes external processes,
  components/projects, or editing the Dagster repository itself."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Dagster

Use this skill for Dagster OSS framework and repository tasks. Dagster is an orchestration platform for building, running, and observing data assets, jobs, schedules, sensors, resources, and external-process integrations.

## First Checks

1. Confirm whether the user is using Dagster in an application project or editing the Dagster OSS repository itself.
2. For application work, confirm `dagster` is installed in the active Python environment and run a minimal import check when useful:

```bash
python - <<'PY'
import dagster as dg
print(dg.__version__)
PY
```

3. For local CLI work, prefer help-only checks before executing user code:

```bash
dagster --help
dagster definitions validate --help
dagster-webserver --help
dagster-graphql --help
```

4. Read `references/repo-provenance.md` before deciding whether this generated skill is current for a Dagster checkout or needs refresh.
5. Use `references/troubleshooting.md` for cross-cutting install/import, optional dependency, target loading, and environment issues before routing deeper.
6. Use `scripts/dagster_skill_doctor.py --help` for a safe local package and command availability probe.

## Route By Task

- **Assets, jobs, ops, and Definitions:** use `sub-skills/asset-definitions/SKILL.md` for `@asset`, `@multi_asset`, `@asset_check`, `@op`, `@job`, `Definitions`, `define_asset_job`, partitions, backfills, selections, and local materialization tests.
- **Config and resources:** use `sub-skills/configuration-resources/SKILL.md` for `Config`, `RunConfig`, `ConfigurableResource`, `EnvVar`, resource dependencies, IO managers, and resource tests.
- **Schedules, sensors, and automation:** use `sub-skills/automation-schedules-sensors/SKILL.md` for schedules, sensors, run requests, cursors, asset sensors, run status sensors, declarative automation, freshness, and backfill automation.
- **Local CLI and development server:** use `sub-skills/cli-local-development/SKILL.md` for `dagster project`, `dagster dev`, `dagster definitions validate`, asset/job execution, workspace targets, schedule/sensor commands, instance inspection, and debug commands.
- **Deployment and operations:** use `sub-skills/deployment-operations/SKILL.md` for `DAGSTER_HOME`, `dagster.yaml`, daemon/webserver services, run launchers, run coordinators, storage, Docker/Kubernetes/ECS checklists, monitoring, and operational failures.
- **GraphQL and webserver:** use `sub-skills/graphql-and-webserver/SKILL.md` for `dagster-webserver`, `dagster-graphql`, `DagsterGraphQLClient`, remote GraphQL URLs, path prefixes, headers/auth, read-only mode, and API troubleshooting.
- **Pipes external processes:** use `sub-skills/pipes-external-processes/SKILL.md` for `dagster-pipes`, `open_dagster_pipes`, external process message protocols, materialization/check reporting, loaders, writers, and subprocess patterns.
- **Components and projects:** use `sub-skills/components-projects/SKILL.md` for component-ready projects, component scaffolding, component YAML/templates, `dagster.components`, `dg`, `create-dagster`, and current project-tooling caveats.
- **Dagster repo edits:** use `sub-skills/repo-development/SKILL.md` for package lookup, Python/UI/docs validation, coding conventions, mandatory `make ruff`, `uv`, focused tests, and git/stack constraints in the Dagster OSS monorepo.

## Installation Notes

- Public application users normally install `dagster`; add `dagster-webserver`, `dagster-graphql`, `dagster-pipes`, or integration packages only when the workflow needs them.
- The generated skill verified core packages and help commands for `dagster`, `dagster-webserver`, and `dagster-graphql` at version `1!0+dev` from the source snapshot.
- `dg` and `create-dagster` project tooling are covered from source/docs evidence, but this checkout’s `dagster-dg-core` depends on an unpublished `dagster-cloud-cli==1!0+dev` package; verify those entry points in the user’s environment before relying on them.
- Broad integration libraries, Dagster Cloud account administration, UI internals, Helm templates, CI/release automation, and credentialed/service-specific examples are intentionally long-tail gaps unless a user explicitly asks to extend this skill.

## Safety

- Do not start long-running services, run destructive CLI commands, wipe assets, migrate instances, deploy infrastructure, push images, or mutate production schedule/sensor state without explicit user approval.
- Keep credentials in environment variables or secret managers; do not write secrets into `dagster.yaml`, workspace files, Dockerfiles, manifests, or generated code.
- For repo edits, always follow `sub-skills/repo-development/SKILL.md`; after any Python code change in the Dagster repo, `make ruff` from the repo root is mandatory.
