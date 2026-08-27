---
name: project-bootstrap
description: "Create, modify, inspect, and troubleshoot Solace Agent Mesh
  project scaffolds without running live services."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Project bootstrap

Use this sub-skill when the task is to create or change a Solace Agent Mesh (SAM) project scaffold with `sam init`, `sam add agent`, `sam add gateway`, or `sam add proxy`; reason about generated project layout; configure shared services; or dry-inspect generated files.

Do **not** use this sub-skill for:

- Plugin packages, plugin installs, plugin catalogs, or plugin builds; route to `plugin-lifecycle`.
- Starting projects, brokers, gateways, REST calls, tasks, or Web UI interaction; route to `runtime-operations`.
- Authoring workflow DAG internals; route to `workflow-authoring`.
- Authoring or running `sam eval`; route to `evaluation`.

## Fast path

1. Decide the project creation surface:
   - Browser setup: `sam init --gui` launches the configuration portal on port `5002`.
   - Non-interactive setup: `sam init --skip ...` uses provided flags or defaults and is suitable for automation.
   - Terminal setup: `sam init` prompts for browser versus terminal configuration.
2. For project-level initialization behavior, generated layout, shared config, `.env`, model provider, broker, Web UI, platform service, artifact, session, and database decisions, use [references/project-initialization.md](references/project-initialization.md).
3. For adding components to an existing project, use [references/component-scaffolding.md](references/component-scaffolding.md).
4. Before any live `sam run` or task submission, run the bundled dry inspector from the generated skill tree:

   ```bash
   python sub-skills/project-bootstrap/scripts/inspect_project.py path/to/sam-project
   ```

   Add `--json` for machine-readable output, `--strict` to fail on warnings, or `--self-test` to exercise the helper on an embedded tiny fixture.
5. If the scaffold is incomplete or surprising, map symptoms to fixes in [references/troubleshooting.md](references/troubleshooting.md).

## Safety boundaries

- This sub-skill may parse files, write project scaffolding guidance, and run safe helper-script help/self-test checks.
- Do not run native repository tests, `sam run`, broker containers, LLM probes, gateway health checks, task submission, plugin install/build, or evaluation commands from this sub-skill.
- Treat GUI operations as local configuration-portal bootstrap behavior only; do not assume the browser completed successfully unless generated files or CLI return data prove it.

## Minimal scaffold checklist

A typical `sam init` project contains:

- `requirements.txt` pinning the installed SAM package family.
- `.env` with namespace, broker, Web UI, platform, logging, authorization, S3/OAuth placeholders, and selected model secrets.
- `configs/shared_config.yaml` with broker, optional model anchors, service anchors, data tools, and auto-summarization.
- `configs/logging_config.yaml`.
- `configs/agents/main_orchestrator.yaml`.
- `configs/gateways/webui.yaml` when the Web UI gateway is enabled.
- `configs/services/platform.yaml` when the Web UI gateway is enabled.
- `src/__init__.py`, plus component source packages created by `sam add gateway`.

## Provenance distilled

This sub-skill was distilled from SAM project, agent, gateway, CLI, installation, configuration, and run-project documentation; CLI init/add implementation; project templates; configuration portal backend behavior; and CLI unit tests covering initialization, add-agent/add-gateway/add-proxy, artifact storage, persistence, GUI handoff, name formatting, overwrite behavior, and error handling. Runtime files are self-contained and do not require opening those source files.
