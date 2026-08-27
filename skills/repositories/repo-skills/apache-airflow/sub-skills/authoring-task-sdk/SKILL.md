---
name: authoring-task-sdk
description: "Write, migrate, debug, and review Airflow 3 Dag authoring code
  using airflow.sdk and Task SDK public interfaces."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

<!-- SPDX-License-Identifier: Apache-2.0 -->

# Authoring Task SDK

Use this sub-skill when the task is about author-facing Airflow 3 Dag code: creating Dags, migrating Airflow 2 imports, reviewing TaskFlow or standard provider operators, diagnosing Dag discovery/import issues, and validating that a Dag file is parseable and discoverable.

## Read First

- `references/api-reference.md` for verified imports, signatures, public-interface boundaries, and standard provider operator signatures.
- `references/workflows.md` for task-oriented recipes: new Dag, import migration, dependencies, task groups, dynamic task mapping, assets, timetables, Params, XCom/context, TaskFlow, and standard operators/sensors.
- `references/troubleshooting.md` for parse/import failures, discovery heuristics, schedule/Param/template mistakes, metadata DB access restrictions, async/deferrable confusion, and optional Graphviz issues.
- `scripts/validate_dag_file.py` for a bundled safe parse/import helper that validates one Dag file without depending on the original repository checkout.

## Scope

This sub-skill covers author-facing Python APIs used in Dag files:

- Dag declaration with `airflow.sdk.DAG` or `@dag`, including `schedule`, `start_date`, `catchup`, `params`, `tags`, `task_group`, `fail_fast`, `allowed_run_types`, `deadline`, `disable_bundle_versioning`, and `rerun_with_latest_version`.
- TaskFlow decorators (`@task`, `@task.branch`, provider decorators exposed under `@task.<provider>`), `@task_group`, dependency helpers, dynamic task mapping, and XComArg wiring.
- Assets and asset scheduling with `Asset`, `AssetAlias`, inlet/outlet events, asset expressions, and mixed asset/time schedules.
- Timetable selection, event schedules, Params, Jinja templates, context access, XComs, Variables, Connections, and standard provider operators/sensors commonly embedded in Dag files.

## Boundaries

- For CLI commands, REST API operations, Dag runs, state management, and operational debugging, route to the operations/CLI/API sub-skill.
- For provider package development, provider tests, hooks/operators implementation, or packaging conventions, route to the provider/extension sub-skill.
- For Helm, Docker images, executor deployment, triggerer/scheduler operations, or production configuration, route to the deployment sub-skill.
- For contributor tooling, Breeze, static checks, PR workflow, or repository development tasks, route to the contribution tooling sub-skill.

## Validation

Prefer validating changed Dag files with the bundled helper before recommending broader operational commands:

```bash
python skills/apache-airflow/sub-skills/authoring-task-sdk/scripts/validate_dag_file.py path/to/dag_file.py --list-dags
python skills/apache-airflow/sub-skills/authoring-task-sdk/scripts/validate_dag_file.py path/to/dag_file.py --expect-dag-id example_dag
```

Use `--repo-root` only when the user explicitly wants the helper to import packages from a current checkout. Do not bake local checkout paths into Dag code or skill documentation.
