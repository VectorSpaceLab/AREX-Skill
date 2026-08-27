---
name: galaxy
description: "Use Galaxy repository guidance for server configuration, APIs,
  tool and workflow development, data/storage, Tool Shed operations, and
  web-client development."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Galaxy Repo Skill

Use this skill when a task involves the Galaxy scientific workflow platform repository: configuring or starting a Galaxy server, automating the Galaxy API, authoring tools or workflows, working with datatypes/storage, operating Tool Shed repositories, or developing the Vue/TypeScript web client.

Galaxy is a large package-centric Python and web monorepo. Start with the route map below, then read only the sub-skill and references that match the task.

## Quick Start

- Read [Repository Provenance](references/repo-provenance.md) before deciding whether this skill matches a current Galaxy checkout or needs refresh.
- Read [Package Layout](references/package-layout.md) when the task depends on the monorepo, split packages, install modes, or import checks.
- Read [Development and Testing](references/development-and-testing.md) when choosing focused Python, API, integration, framework, workflow, Selenium, Playwright, or client tests.
- Read [Troubleshooting](references/troubleshooting.md) for cross-cutting install/import, package-layout, optional dependency, service, Node/client, and safety failures.
- Run `python scripts/inspect_galaxy_environment.py --help` for a safe environment/package-layout diagnostic helper.

## Route Map

- [Configuration and Admin](sub-skills/configuration-and-admin/SKILL.md): choose this for `galaxy.yml`, `run.sh`, Gravity/startup, config validation, jobs, dependency resolvers, admin configuration, and startup troubleshooting.
- [API Automation](sub-skills/api-automation/SKILL.md): choose this for Galaxy HTTP API calls, API keys, histories, datasets, workflow import/invocation, OpenAPI orientation, API tests, and `401`/`403`/`400` debugging.
- [Workflows and Tools](sub-skills/workflows-and-tools/SKILL.md): choose this for Galaxy tool XML/YAML, tool tests, workflow Format2 YAML, workflow framework tests, CWL surfaces, `galaxy-tool-util` CLIs, and dependency/mulled hints.
- [Data and Storage](sub-skills/data-and-storage/SKILL.md): choose this for datatypes, sniffers, metadata, data managers, tool data tables, object stores, file sources, dataset storage, and storage cleanup safety.
- [Tool Shed Operations](sub-skills/tool-shed-operations/SKILL.md): choose this for Tool Shed repositories, repository metadata reset, repository dependencies, installed Tool Shed tools, Tool Shed API scripts, `shed_tool_conf.xml`, and Whoosh indexes.
- [Web Client Development](sub-skills/web-client-development/SKILL.md): choose this for `client/` pnpm workspace tasks, Vue/TypeScript code, Vitest, Pinia, MSW/OpenAPI mocks, Vite dev server, generated API-client package, and client build/test troubleshooting.

## Common Decisions

- If the task names `galaxy.yml`, config samples, startup, database settings, jobs, dependency resolvers, or admin deployment, start with [Configuration and Admin](sub-skills/configuration-and-admin/SKILL.md).
- If the task asks for `curl`, API keys, `bioblend`, OpenAPI, histories, datasets, or workflow invocation through HTTP, start with [API Automation](sub-skills/api-automation/SKILL.md).
- If the task asks to write a Galaxy tool wrapper or workflow file, start with [Workflows and Tools](sub-skills/workflows-and-tools/SKILL.md); use [API Automation](sub-skills/api-automation/SKILL.md) only when executing those artifacts through a running server.
- If the task mentions datatypes, sniffers, `.loc`, data managers, object stores, file sources, storage templates, cloud credentials, or cleanup scripts, start with [Data and Storage](sub-skills/data-and-storage/SKILL.md).
- If the task mentions Tool Shed repository metadata, categories/users, installed repositories, repository dependencies, or Tool Shed search, start with [Tool Shed Operations](sub-skills/tool-shed-operations/SKILL.md).
- If the task touches Vue components, TypeScript, `pnpm`, Vitest, MSW, generated API client, or Vite proxy settings, start with [Web Client Development](sub-skills/web-client-development/SKILL.md).

## Install and Inspection Notes

Galaxy supports both a root checkout workflow and split packages under `packages/`. For coding-agent inspection, prefer scoped imports and split-package metadata over broad full-server installs unless the task explicitly needs a runnable Galaxy service.

Minimum orientation checks:

```bash
python - <<'PY'
import galaxy.version
print(galaxy.version.VERSION)
PY
python scripts/inspect_galaxy_environment.py --expected-version 26.2.dev0
```

The helper is read-only. It reports Python version, importability of representative Galaxy modules, installed split-package metadata when available, and common package-layout caveats. It does not start Galaxy, install dependencies, build the client, contact services, or mutate config/data.

## Safety Boundaries

- Treat full Galaxy server startup, database migration, object-store migration, Tool Shed metadata reset, cloud storage tests, and client dependency installation as service- or environment-affecting operations; plan before running.
- Do not run cloud, credentialed, network-heavy, destructive cleanup, or long integration/Selenium/client build commands unless the user explicitly authorizes them and supplies the target environment.
- Prefer targeted unit/parser/help checks first; escalate to service-backed integration only after the generated route explains the risk and prerequisites.
- Keep API keys, database URLs, cloud credentials, OAuth secrets, and user data out of prompts, logs, and generated examples.

## When to Refresh

Run `refresh-repo-skill` if the current Galaxy checkout commit, dirty source state, package version, split-package metadata, public API routes, tool-util CLIs, client workspace commands, or major evidence paths differ from [Repository Provenance](references/repo-provenance.md).
