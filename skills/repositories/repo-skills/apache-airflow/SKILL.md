---
name: apache-airflow
description: "Route Apache Airflow repo tasks across Dag authoring, operations,
  providers, deployment, and contribution workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

<!-- SPDX-License-Identifier: Apache-2.0 -->

# Apache Airflow Repo Skill

Use this skill when a task names Apache Airflow, the `apache-airflow` Python package, the Airflow monorepo, Airflow Dags, Task SDK, `airflow`/`airflowctl`, providers, official Docker images, Helm chart, Breeze, or Airflow contribution rules.

This skill is a router. Read the nearest sub-skill for workflow depth and use repo-level references only for shared context.

## Start Here

1. Read `references/repo-provenance.md` before relying on this skill for a checkout; refresh the skill if the commit, dirty state, or public package versions no longer match.
2. Read `references/troubleshooting.md` for cross-cutting installation, import, routing, and validation failures.
3. Use `scripts/check_airflow_skill_environment.py` for a quick installed-package and helper-script check when a Python environment is available.
4. Choose exactly one primary sub-skill from the route map, then follow its linked references and bundled scripts.

## Route Map

- `sub-skills/authoring-task-sdk/` — write, migrate, validate, or debug Airflow 3 Dag authoring code using `airflow.sdk`, Task SDK, TaskFlow, dynamic task mapping, assets, timetables, Params, XCom/context, and standard provider operators/sensors.
- `sub-skills/operations-cli-api/` — install or run Airflow, inspect configuration, use `airflow` or `airflowctl`, choose Stable REST API vs CLI, operate core components, test/backfill Dags from the command line, and troubleshoot metadata DB/API/server state.
- `sub-skills/providers-extensions/` — use provider packages, standard operators/sensors/hooks, custom operators/hooks/sensors, plugins/listeners/timetables/notifiers/extra links, provider metadata, and provider package conventions.
- `sub-skills/deployment-helm-docker/` — plan or debug deployments with the official Helm chart and Docker images, including chart values, custom images, Dag delivery, logs, secrets/config, migrations, and autoscaling.
- `sub-skills/contribution-tooling/` — change the Airflow repository safely with Breeze, `uv`, `prek`, selective checks, docs/news/changelog rules, generated-file constraints, PR conventions, and component-specific tests.

## Common Routing Decisions

- If the task is about a user Dag file, start with `authoring-task-sdk` even if the symptom appears through `airflow dags test`; return to `operations-cli-api` only for command/config execution details.
- If a provider import fails in a Dag, use `providers-extensions` for package/extras/provider metadata and `authoring-task-sdk` for Dag structure.
- If a scheduler or Dag processor cannot parse Dags in Kubernetes, use `deployment-helm-docker` for image/Dag delivery and `operations-cli-api` for component/database diagnosis.
- If the task is to edit Airflow source code, use `contribution-tooling` first, then route to the domain sub-skill for product behavior.
- Java SDK, Go SDK, new language SDK, translation, and provider release-manager workflows have specialized repo-local skills in the source checkout; this generated skill keeps only routing-level notes for those areas.

## Install and Import Facts

- Public package names verified for this snapshot: `apache-airflow`, `apache-airflow-core`, `apache-airflow-task-sdk`, `apache-airflow-ctl`, and `apache-airflow-providers-standard`.
- Public import roots verified for this snapshot: `airflow`, `airflow.sdk`, `airflowctl`, and `airflow.providers.standard`.
- Airflow installation should use official constraints for repeatability; do not recommend broad `[all]` extras unless the user explicitly needs broad provider coverage.
- Dag authors should use the Airflow 3 public interface from `airflow.sdk`; avoid internal metadata DB access from task code.

## Bundled Helpers

- `scripts/check_airflow_skill_environment.py` checks installed distribution metadata/imports and confirms bundled helper scripts are present.
- Sub-skill helpers provide targeted checks: Dag file parsing, CLI parser inspection, provider metadata sanity checks, Helm values summaries, and first-pass Airflow contribution command recommendations.

## Safety Boundaries

- Runtime instructions in this skill are self-contained and do not depend on the original repository checkout.
- Do not copy local environment paths, private prefixes, or machine-specific setup details into user-facing work.
- Do not run Airflow native tests, examples, Docker builds, Helm cluster commands, or release-management scripts unless the active sub-skill classifies them as safe for the current environment.
- In Airflow prose, write Dag in title case; preserve literal code/config/CLI tokens such as `DAG`, `dag_id`, `dag`, `airflow dags list`, and `get_dag` exactly.
