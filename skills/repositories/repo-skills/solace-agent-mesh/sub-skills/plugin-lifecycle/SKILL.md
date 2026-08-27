---
name: plugin-lifecycle
description: "Create, inspect, install, catalog, add, and build Solace Agent
  Mesh plugin packages safely."
disable-model-invocation: true
metadata:
  disco-role: operating
  repo: solace-agent-mesh
  package: solace-agent-mesh
license: Apache 2.0
---

# Plugin lifecycle

Use this sub-skill when the task is to create a Solace Agent Mesh (SAM) plugin package, add plugin components into a SAM project, install plugins from local paths/wheels/Git/official names, browse the plugin catalog, or build a distributable plugin artifact.

Do **not** use this sub-skill for:

- Project-level `sam add agent`, `sam add gateway`, or `sam add proxy` scaffolding; route to `project-bootstrap`.
- Starting projects, activating plugin-backed components, submitting tasks, or checking live brokers/gateways/LLMs; route to `runtime-operations`.
- CI/release automation, maintainer packaging policy, or broad repository maintenance.

## Fast path

1. Identify the lifecycle operation:
   - New reusable plugin package: `sam plugin create`.
   - Add one plugin instance to an existing SAM project: `sam plugin add`.
   - Install/verify a plugin package without creating a component config: `sam plugin install`.
   - Browse registry/catalog UI: `sam plugin catalog`.
   - Build wheel/sdist artifacts: `sam plugin build`.
2. Open [references/plugin-workflows.md](references/plugin-workflows.md) for command forms, source choices, target files, metadata rules, and side effects.
3. Before invoking an install/add/build operation, inspect the candidate plugin tree safely:

   ```bash
   python sub-skills/plugin-lifecycle/scripts/inspect_plugin.py path/to/plugin --component-name my-component --project-dir path/to/sam-project
   ```

   Add `--json` for machine-readable output, `--strict` to fail on warnings, or `--self-test` to exercise the helper on an embedded tiny fixture.
4. If a command fails or would overwrite files, use [references/troubleshooting.md](references/troubleshooting.md) before retrying.

## Safety boundaries

- `sam plugin install` and `sam plugin add` can run a package-manager command and can modify the active Python environment. Use an isolated environment when possible and prefer an explicit installer such as `--install-command "uv pip install {package}"` or a preinstalled plugin module.
- `sam plugin add` writes component YAML under `configs/agents`, `configs/gateways`, `configs/workflows`, or `configs/plugins` and overwrites an existing target file without a merge step. Always inspect the target path first.
- `sam plugin catalog` starts a local web server, opens a browser when possible, contacts/clones registries, and writes catalog cache/registry state under the SAM CLI home directory. Do not run it as a dry validation step.
- `sam plugin build` runs `python -m build` in the plugin directory and creates/updates `dist/` artifacts. Build backends may use isolated build environments.
- This sub-skill does not run native repo tests, live catalog servers, brokers, LLM calls, gateway checks, or evaluation tasks.

## Minimal checklist

- Plugin name is intentional after SAM normalization: display/name input -> kebab directory, snake Python module, Pascal display strings.
- `pyproject.toml` exists and has `[project].name` plus `[tool.<project_name_with_underscores>.metadata].type` set to `agent`, `gateway`, `tool`, `workflow`, or `custom`.
- `config.yaml` exists at plugin package root and uses `__COMPONENT_*__` placeholders where component-specific names should be substituted by `sam plugin add`.
- Generated source exists for the plugin type: agent/tool usually include `tools.py`; gateway includes `app.py` and `component.py`; workflow is YAML-first with only package boilerplate; custom includes custom Python skeleton.
- Build metadata includes package files and force-includes `config.yaml`, `README.md`, and `pyproject.toml` into the installed module so `sam plugin add` can read them after installation.
- Install source is unambiguous: already installed module, local directory, wheel, Git URL, `git+...#subdirectory=...`, or official plugin name.
- Existing project component files are backed up or intentionally replaced before running `sam plugin add`.

## Provenance distilled

This sub-skill was distilled from SAM plugin documentation, plugin CLI command implementations, plugin templates, plugin catalog/official registry helpers, and plugin command unit tests. Runtime guidance is self-contained and does not require opening the source repository evidence.
