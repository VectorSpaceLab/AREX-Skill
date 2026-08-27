---
name: data-designer-repo-skill
description: "Use when you need to design DataDesigner configs, run
  preview/create/validate workflows, inspect the CLI or agent context, work with
  plugins or MCP tools, or adapt documented recipes and integrations for
  synthetic dataset generation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# DataDesigner Repo Skill

Use this skill for the DataDesigner repository and its published Python packages.
It is a router, not a full manual.

## Start here

- Read `references/package-overview.md` for the package layout, verified entry points, and route map.
- Read `references/troubleshooting.md` when the package or CLI fails to import, model aliases are missing, persona assets are absent, or a generation path needs external credentials.
- Read `references/repo-provenance.md` when you want to check whether this skill still matches the current checkout.
- Run `scripts/check_datadesigner_environment.py` if you want a quick read-only smoke check of the active installation.

## Install and smoke check

For a published install, use:

```bash
pip install data-designer
```

For a workspace checkout, use the repo's uv workspace sync instead of hand-installing individual packages:

```bash
uv sync --all-packages --no-default-groups
```

Minimal import check:

```bash
python -I -c "import data_designer.config as dd; from data_designer.interface import DataDesigner; print(dd.DataDesignerConfigBuilder, DataDesigner)"
```

If `data-designer agent context` reports no usable model aliases, that is a configuration state, not an install failure. Config-only workflows can still validate.

## Route map

### config-authoring
Use for dataset schema design: builder API, columns, samplers, validators, processors, seed sources, custom columns, person data, and config troubleshooting.

### generation-runtime
Use for `DataDesigner.validate`, `preview`, `create`, `check_models`, `set_run_config`, result handling, export, push to Hugging Face Hub, resume, and workflow chaining.

### cli-and-agent-tools
Use for the `data-designer` CLI, config/model/provider commands, download/persona management, plugin catalog commands, and `data-designer agent context/types/state`.

### plugins-and-extensions
Use for custom column generators, plugin entry points, plugin install/uninstall planning, MCP tool configs, and installed-plugin inspection.

### recipes-and-integrations
Use for notebook tutorials, code/SQL/image/VLM recipes, trace ingestion, workflow chaining, human review flows, and Hugging Face export guidance.

## What not to do

- Do not depend on files from the original checkout at runtime. Use only bundled references and scripts under this skill tree.
- Do not tell future agents to open original repo docs or examples when a bundled reference exists.
- Do not treat optional remote model, persona-download, GPU, or Docker flows as required for the base package unless the task explicitly asks for them.

## Read next

- `references/package-overview.md` for the verified package map and workflow groups.
- `references/troubleshooting.md` for cross-cutting failures.
- `sub-skills/<id>/SKILL.md` for the specific workflow you need.
