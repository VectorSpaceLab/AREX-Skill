---
name: langflow
description: "Use Langflow's visual AI workflow builder, FastAPI backend, LFX
  executor, SDK, frontend, deployment, and monorepo maintenance workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Langflow

Use this repo skill when working with Langflow, the visual workflow builder for AI agents and applications. It covers flow authoring, Python components and bundles, the FastAPI backend, the lightweight `lfx` executor, REST/SDK clients, the React frontend, deployment/operations, and safe monorepo maintenance.

## First Checks

1. Confirm the task is about Langflow specifically, or about a visual AI workflow builder with flows, components, `lfx`, Langflow REST APIs, Langflow SDK, MCP, Docker deployment, or Langflow repository maintenance.
2. If you are checking whether this skill is current for a checkout, read [references/repo-provenance.md](references/repo-provenance.md).
3. For package topology and distribution/import relationships, read [references/package-topology.md](references/package-topology.md).
4. For cross-cutting install/import/runtime pitfalls, read [references/troubleshooting.md](references/troubleshooting.md).

## Route by Task

| User task | Read |
| --- | --- |
| Create, inspect, validate, tweak, import/export, or smoke-run Langflow flow JSON | [flow-authoring](sub-skills/flow-authoring/SKILL.md) |
| Add or update Python components, inputs/outputs, `Message`/`Data` returns, extension bundles, manifests, or component index behavior | [component-development](sub-skills/component-development/SKILL.md) |
| Change FastAPI routes, graph execution, services, settings, auth/authz, database models, Alembic migrations, storage, telemetry, or backend runtime errors | [backend-runtime](sub-skills/backend-runtime/SKILL.md) |
| Use or maintain `lfx run`, `lfx serve`, `lfx-mcp`, Flow DevOps commands, stateless execution, or executor validation | [executor-cli](sub-skills/executor-cli/SKILL.md) |
| Build REST/API clients, use `langflow-sdk`, stream run results, push/pull flows, normalize flow JSON, or inspect OpenAPI contracts | [sdk-and-api-clients](sub-skills/sdk-and-api-clients/SKILL.md) |
| Modify the React/Vite UI, graph workspace, frontend controllers/hooks/stores, icons, or frontend tests | [frontend-development](sub-skills/frontend-development/SKILL.md) |
| Install, run, configure, Dockerize, upgrade, operate, or troubleshoot a Langflow deployment | [deployment-and-operations](sub-skills/deployment-and-operations/SKILL.md) |
| Maintain the monorepo: setup, focused tests, formatting, generated files, package versions, migrations, releases, docs, or CI-style checks | [repo-maintenance](sub-skills/repo-maintenance/SKILL.md) |

## Common Decisions

- **Flow run path:** Use `flow-authoring` for the flow document itself, `executor-cli` for local `lfx` run/serve behavior, `sdk-and-api-clients` for calling a running Langflow server, and `backend-runtime` for implementation bugs in run endpoints or graph execution.
- **Component/UI split:** Use `component-development` for Python component identity, inputs/outputs, bundles, and component indexes. Use `frontend-development` for palette display, icons, graph node UI, React stores, and frontend contract failures.
- **Operations/backend split:** Use `deployment-and-operations` for environment variables, Docker, databases, volumes, secrets, and server startup. Use `backend-runtime` when editing source routes/services/settings/migrations.
- **Maintenance boundary:** Use `repo-maintenance` to choose focused validation and obey monorepo rules, then route into a feature sub-skill for implementation details.

## Install And Verify

For normal use, install the public package in a supported Python environment:

```bash
uv pip install -U langflow
uv run langflow --help
uv run lfx --help
uv run python -c "import langflow, lfx, langflow_sdk; print('imports ok')"
```

For source checkout work, follow the repo-maintenance setup route first because this monorepo has multiple Python packages plus a frontend package. Install only provider, vector-store, document, local-model, or deployment extras needed for the selected workflow.

## Minimal Public Facts

- Public distributions include `langflow`, `langflow-base`, `lfx`, `langflow-sdk`, and extracted `lfx-*` extension bundles.
- Public imports include `langflow`, `lfx`, `langflow_sdk`, and extension bundle modules such as `lfx_arxiv`, `lfx_docling`, `lfx_duckduckgo`, and `lfx_ibm`.
- `langflow` CLI commands include `run`, `superuser`, `copy-db`, `migration`, `api-key`, and `lfx`.
- `lfx` CLI commands include setup (`init`, `login`), authoring (`create`, `validate`, `requirements`, `upgrade`, `extension`), running (`run`, `serve`), and remote (`status`, `push`, `pull`, `export`) workflows.
- The Python SDK exposes sync and async clients, flow/project CRUD models, run/stream helpers, flow file normalization, typed exceptions, and test helpers.

## Safe Defaults

- Prefer focused validation before broad test or service runs.
- Do not execute untrusted flow JSON, custom component code, or Python graph scripts merely to inspect them.
- Do not run credentialed providers, cloud deployments, Docker mutations, destructive migrations, package publishing, or model/GPU workloads unless the user explicitly asks and the environment is safe.
- Do not paste real API keys into flow JSON, docs, examples, `.env`, `.lfx` config, shell history, or committed files.

## Bundled Helpers

Each sub-skill owns its helper scripts. Run helpers from the nearest sub-skill directory so relative `scripts/...` paths resolve after import.

- Flow JSON preflight: `sub-skills/flow-authoring/scripts/validate_flow_json.py`.
- Component skeleton checks: `sub-skills/component-development/scripts/check_component_skeleton.py`.
- FastAPI route inspection: `sub-skills/backend-runtime/scripts/inspect_routes.py`.
- LFX flow command template checks: `sub-skills/executor-cli/scripts/validate_lfx_flow.py`.
- Flow JSON normalization: `sub-skills/sdk-and-api-clients/scripts/normalize_flow_file.py`.
- Frontend package script checks: `sub-skills/frontend-development/scripts/check_frontend_package.py`.
- Langflow environment variable checks: `sub-skills/deployment-and-operations/scripts/check_env_vars.py`.
- Deprecated import checks for repo maintenance: `sub-skills/repo-maintenance/scripts/check_deprecated_imports.py`.
