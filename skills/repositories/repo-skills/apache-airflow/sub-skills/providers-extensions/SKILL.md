---
name: providers-extensions
description: "Work with Airflow providers, standard operators/sensors/hooks,
  custom extensions, provider metadata, and provider package maintenance
  conventions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

<!-- SPDX-License-Identifier: Apache-2.0 -->

# Providers and Extensions

Use this sub-skill when a task involves Airflow providers or extension points: selecting provider packages/extras, importing standard operators/sensors/hooks in Dags, writing custom operators/hooks/sensors, registering plugins/listeners/timetables/notifiers/extra links, or maintaining provider package metadata.

## Route First

- For general Dag authoring, TaskFlow, task mapping, assets, schedules, or `airflow.sdk` basics, use `../authoring-task-sdk/` first and return here only for provider-specific imports or extension classes.
- For CLI, Breeze, CI, release preparation, or broad provider-release classification workflows, use `../contribution-tooling/`; this sub-skill only covers the provider files and safe metadata checks needed during ordinary development.
- For REST API, web UI internals, scheduler, executor, Helm, Docker, or deployment behavior, use the corresponding sibling sub-skill rather than treating providers as a catch-all.
- For cloud-service-specific APIs, prefer the relevant provider’s own documentation or source; this sub-skill covers Airflow provider conventions and the standard provider patterns, not deep SDK behavior for every integration.

## What To Read

- `references/provider-api-patterns.md` for public extension boundaries, standard provider imports, operator/sensor/hook patterns, package naming, extras, and provider entry points.
- `references/extension-workflows.md` for recipes for custom operators, hooks, sensors, plugins, listeners, timetables, notifiers, extra links, and provider-package tests.
- `references/provider-metadata.md` for `provider.yaml`, `get_provider_info`, `pyproject.toml`, generated-file cautions, docs/changelog rules, and the bundled checker.
- `references/troubleshooting.md` for missing provider packages, import errors, connection IDs, deferrable trigger dependencies, generated-file mistakes, and docs/changelog pitfalls.

## Fast Guidance

- Install/import provider-specific code explicitly. Airflow core does not guarantee that every provider is installed; standard operators such as `BashOperator` and `FileSensor` live in `apache-airflow-providers-standard`.
- Use public bases for new runtime code: `airflow.sdk.BaseOperator`, `airflow.sdk.BaseSensorOperator`, `airflow.sdk.BaseHook`, `airflow.sdk.BaseNotifier`, `airflow.sdk.BaseOperatorLink`, and documented plugin/listener/timetable APIs.
- Keep expensive work out of operator constructors. Resolve hooks, connections, network clients, and service jobs inside `execute`, `poke`, trigger code, or helper methods called from execution.
- Treat `provider.yaml` as the human-edited source for provider metadata. `get_provider_info.py`, provider docs indexes, and most provider `pyproject.toml` content are generated; edit only the preserved dependency sections unless the generation workflow says otherwise.
- Before touching provider metadata, run `scripts/check_provider_metadata.py --provider-dir <provider-dir>` against the provider directory you are editing and fix reported errors before relying on generated files.

## Done Criteria

A provider/extension change is ready when imports come from installed provider packages, custom classes use public extension points, metadata and entry points agree, generated files are not hand-edited incorrectly, and tests cover the changed operator/hook/sensor/plugin behavior without depending on external services unless explicitly mocked or isolated.
