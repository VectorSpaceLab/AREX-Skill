---
name: kedro
description: "Use Kedro to create, configure, run, extend, inspect, and
  troubleshoot production-ready data and analytics pipeline projects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Kedro

Use this repo skill when the task involves Kedro data or analytics pipelines: `node()`, `Pipeline`, `DataCatalog`, `OmegaConfigLoader`, `kedro run`, project scaffolding, `KedroSession`, hooks/plugins, runners, inspection snapshots, or the optional server API.

Kedro is a Python framework for production-ready data engineering and data science pipelines. The source evidence for this skill targets Kedro `1.4.0`, whose distribution and import name are both `kedro` and whose console script is `kedro`.

## Quick Checks

- Install/import check: `python -c "import kedro; print(kedro.__version__)"`.
- CLI check without telemetry: `KEDRO_DISABLE_TELEMETRY=1 kedro --version` and `KEDRO_DISABLE_TELEMETRY=1 kedro --help`.
- Environment diagnostic: run `scripts/check_kedro_environment.py --help`, then `scripts/check_kedro_environment.py --check-cli`.
- Core package only includes Kedro framework primitives; concrete datasets such as `pandas.CSVDataset` usually require `kedro-datasets` and relevant extras.
- Optional server workflows need the `server` extra or equivalent `fastapi`/`uvicorn` dependencies.

## Route by Task

- Use `sub-skills/pipelines-and-nodes/SKILL.md` for graph authoring with `node()`, `Node`, `Pipeline`, `pipeline()`, namespaces, tags, modular pipelines, slicing semantics, preview payloads, and graph validation.
- Use `sub-skills/data-catalog-and-config/SKILL.md` for `DataCatalog`, dataset YAML, credentials, versioning, catalog factories, `OmegaConfigLoader`, parameters, globals, and config merge behavior.
- Use `sub-skills/project-cli-and-sessions/SKILL.md` for `kedro new`, starters, project layout, global/project CLI command availability, project metadata, settings, `bootstrap_project()`, `configure_project()`, `KedroSession`, packaging, IPython, and Jupyter.
- Use `sub-skills/runners-and-execution/SKILL.md` for `kedro run`, `KedroSession.run()`, `SequentialRunner`, `ThreadRunner`, `ParallelRunner`, async I/O, run slicing, load versions, runtime params, and missing-output resume.
- Use `sub-skills/hooks-and-extensions/SKILL.md` for project hooks, plugin entry points, custom CLI commands, custom datasets, custom runners, notebook extension points, serving patterns, and deployment integrations.
- Use `sub-skills/inspection-and-server/SKILL.md` for read-only project snapshots, `kedro.inspection.get_project_snapshot`, snapshot model interpretation, optional HTTP server endpoints, and server dependency/startup troubleshooting.

## Current API Facts

- Import pipeline APIs from `kedro.pipeline`: `node`, `Node`, `Pipeline`, `pipeline`, `GroupedNodes`, and optional preview/LLM helpers.
- Use `kedro.pipeline.pipeline(...)` for reusable namespaced pipelines; do not use stale `kedro.pipeline.modular_pipeline` imports.
- Construct catalogs with `DataCatalog(...)` or `DataCatalog.from_config(catalog, credentials=None, load_versions=None, save_version=None)`.
- Load project config with `OmegaConfigLoader(conf_source, env=None, runtime_params=None, config_patterns=None, base_env=None, default_run_env=None, custom_resolvers=None, merge_strategy=None, ignore_hidden=True)`.
- Create sessions with `KedroSession.create(project_path=None, save_on_close=True, env=None, runtime_params=None, conf_source=None)`.
- Built-in runners are `SequentialRunner(is_async=False)`, `ThreadRunner(max_workers=None, is_async=False)`, and `ParallelRunner(max_workers=None, is_async=False)`.

## Common Workflows

1. For a new project, use `project-cli-and-sessions` to choose `kedro new` flags, validate naming, opt out of telemetry if required, and explain generated layout.
2. For pipeline code, use `pipelines-and-nodes` to design nodes and reusable pipeline factories before choosing catalog entries or runners.
3. For data/config files, use `data-catalog-and-config` to validate catalog structure, credentials indirection, runtime params, config environments, and optional dataset dependencies.
4. For execution, use `runners-and-execution` to build the `kedro run` command or programmatic `KedroSession.run()` call and select the runner.
5. For customization, use `hooks-and-extensions` to add hooks/plugins/custom commands or datasets, then return to sibling skills for config and run validation.
6. For diagnostics, use `inspection-and-server` for read-only snapshots and optional server APIs; use execution routes only when the task explicitly runs nodes.

## References

- Read `references/package-overview.md` for package facts, command families, optional extras, public API map, and cross-skill workflow examples.
- Read `references/troubleshooting.md` for cross-cutting install/import, CLI, telemetry, optional dependency, project detection, stale API, and secret-handling issues.
- Read `references/repo-provenance.md` to see the source commit, dirty-state note, package version, and evidence paths used to create this skill.
- `references/repo-routing-metadata.json` is structured metadata for managed `repo-skills-router` import.

## Safety and Boundaries

- Do not rely on the original repository checkout, docs, tests, templates, or scripts at runtime; this skill bundles distilled references and safe helper scripts.
- Avoid printing credentials from `credentials.yml`, environment variables, or cloud auth helpers; validate the presence and shape of secrets without echoing values.
- Set `KEDRO_DISABLE_TELEMETRY=1` or `DO_NOT_TRACK=1` for automated `kedro` CLI probes when telemetry/network side effects are undesirable.
- Warn before `kedro new` with remote starters, `--example=yes`, deployment commands, server startup, or any command that writes projects, builds artifacts, opens browsers, or uses network access.
