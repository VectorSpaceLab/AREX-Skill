---
name: tool-shed-operations
description: "Operate Galaxy Tool Shed repositories, repository metadata,
  installed Tool Shed tools, Tool Shed APIs, and publishing/install
  troubleshooting safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Galaxy Tool Shed Operations

Use this sub-skill when a task involves Tool Shed repository installation or publishing, repository metadata reset/regeneration, repository dependencies, installed Tool Shed repositories, Tool Shed API scripts, test shed bootstrapping, `shed_tool_conf.xml`, or Tool Shed Whoosh search indexes.

## Start Here

- Read [Tool Shed Workflows](references/tool-shed-workflows.md) for repository installation, metadata reset, repository dependencies, installed-repository state, and search-index workflows.
- Read [API And Scripts](references/api-and-scripts.md) for Tool Shed API surfaces, bundled dry-run planning, legacy script behavior, and service-required scripts.
- Read [Troubleshooting](references/troubleshooting.md) when installs, metadata, repository dependencies, permissions, search, or reset operations fail.
- Use `python scripts/tool_shed_api_plan.py --help` to draft safe plans for categories, users, metadata reset, install checks, and Whoosh-index work without contacting a server by default.

## Routing Boundaries

- Stay here for Tool Shed repositories, Tool Shed-side categories/users, repository metadata, `repository_dependencies.xml`, installed Tool Shed repository state, Tool Shed search indexes, and `shed_tool_conf.xml` effects.
- Use [Workflows And Tools](../workflows-and-tools/SKILL.md) for local tool XML, tool tests, workflow YAML, and wrapper authoring before a repository is published.
- Use [API Automation](../api-automation/SKILL.md) for generic Galaxy API authentication, histories, datasets, workflows, OpenAPI inspection, and non-Tool-Shed API automation.
- Use [Configuration And Admin](../configuration-and-admin/SKILL.md) for `galaxy.yml`, server startup, process management, and general admin configuration around shed config files.

## Safety Defaults

- Treat every non-local Tool Shed or Galaxy URL as production-like until the user confirms it is disposable or staging.
- Prefer dry-run plans and metadata previews before write actions; do not create users/categories, reset production metadata, reinstall repositories, or rebuild indexes without explicit user approval.
- Do not print or persist API keys; pass secrets through environment variables and redact them in logs or generated command plans.
- Distinguish Tool Shed server APIs from Galaxy server APIs: Tool Shed APIs manage repositories/categories/users, while Galaxy APIs manage installed Tool Shed repositories inside a Galaxy instance.
