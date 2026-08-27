# Deployment and Validation

CrewAI deployment commands target CrewAI AMP. Treat deployment as optional and credential-bound: local validation can be safe, but create/push/status/logs/list/remove typically require authentication and may contact hosted services.

## Command Routing

```bash
crewai login
crewai deploy validate
crewai deploy create
crewai deploy create --skip-validate
crewai deploy create -y
crewai deploy push
crewai deploy push --uuid <deployment_uuid>
crewai deploy push --skip-validate
crewai deploy status
crewai deploy status --uuid <deployment_uuid>
crewai deploy logs
crewai deploy logs --uuid <deployment_uuid>
crewai deploy list
crewai deploy remove --uuid <deployment_uuid>
```

Use `crewai deploy validate` first. It runs the pre-deploy validation suite locally and exits non-zero for blocking issues. `deploy create` and `deploy push` run the same validation unless `--skip-validate` is provided.

## Local Validation Checks

`crewai deploy validate` checks both JSON crew projects and source-layout crew/flow projects.

For all project types, it checks:

- `pyproject.toml` exists and parses.
- `[project].name` exists.
- `uv.lock` or `poetry.lock` exists.
- Lockfile freshness relative to `pyproject.toml`.
- Known API key references in code/JSONC versus `.env`.
- Lockfile-pinned `crewai` version freshness.

For JSON crew projects, it also checks:

- `crew.jsonc` or `crew.json` parses as a valid JSON crew project.
- Referenced agent names have matching files under `agents/`.
- Runtime-only fields such as generated IDs are not present in deployable JSON.
- Referenced known API keys in `crew.jsonc` and `agents/*.jsonc` are present in `.env` or deployment configuration.

For classic crew projects, it also checks:

- `src/<normalized_project_name>/` exists.
- `crew.py` exists and contains a `@CrewBase`-decorated crew class.
- `config/agents.yaml` and `config/tasks.yaml` exist.
- Hatch wheel target resolves correctly.
- The crew module imports cleanly without heavy import-time side effects.

For flow projects, it also checks:

- `[tool.crewai].type = "flow"`.
- `src/<normalized_project_name>/main.py` exists.
- A `Flow` subclass is discoverable.
- Hatch wheel target resolves correctly.
- The flow module imports cleanly.

## Common Finding Codes

| Code | Severity | Meaning | Typical fix |
| --- | --- | --- | --- |
| `missing_pyproject` | error | No `pyproject.toml` at project root | Run from project root or scaffold a project. |
| `invalid_pyproject` | error | TOML cannot be parsed | Fix syntax. |
| `missing_project_name` | error | `[project].name` missing | Add a project name. |
| `missing_lockfile` | error | No `uv.lock` or `poetry.lock` | Run `uv lock` or `poetry lock`. |
| `stale_lockfile` | warning | Lockfile older than `pyproject.toml` | Re-lock dependencies. |
| `invalid_crew_json` | error | JSON crew/agent/task references invalid | Fix `crew.jsonc`, `agents/`, or runtime-only fields. |
| `env_vars_not_in_dotenv` | warning | Known API keys referenced but absent from `.env` | Add keys to local `.env` and deployment env vars. |
| `missing_src_dir` | error | Source-layout project has no `src/` | Restore source layout. |
| `missing_package_dir` | error | `src/<project_name>/` missing | Rename package dir or update `[project].name`. |
| `stale_egg_info` | warning | `src/*.egg-info/` may confuse package discovery | Delete stale artifact and ignore it. |
| `missing_crew_py` | error | Classic crew lacks `crew.py` | Restore generated crew entrypoint. |
| `missing_config_dir` | error | Classic crew lacks `config/` | Restore config directory. |
| `missing_agents_yaml` | error | Classic crew lacks `config/agents.yaml` | Restore agents YAML. |
| `missing_tasks_yaml` | error | Classic crew lacks `config/tasks.yaml` | Restore tasks YAML. |
| `missing_flow_main` | error | Flow project lacks `main.py` | Restore flow entrypoint. |
| `import_timeout` | error | Importing crew/flow takes too long | Move network/heavy work out of import time. |
| `import_failed` | error | Crew/flow module cannot import | Run `crewai run` locally only after safety review. |
| `no_crewbase_class` | error | No `@CrewBase` class found | Decorate the crew class correctly. |
| `no_flow_subclass` | error | No `Flow` subclass found | Define an instantiable `Flow` subclass. |
| `missing_provider_extra` | error | Provider extra package missing | Run the suggested `uv add "crewai[extra]"`. |
| `llm_init_missing_key` | warning | LLM constructed at import time needs an API key | Add deployment env var or lazy-load LLM. |
| `llm_provider_init_failed` | error | Provider initialization failed | Check provider config and extras. |
| `env_var_read_at_import` | warning | Module reads env vars during import | Move env-dependent code into runtime methods. |
| `stale_crewai_pin` | error | Lockfile pins an incompatible old CrewAI | Upgrade the lockfile's CrewAI pin. |
| `pydantic_validation_error` | error | Config validation failed while loading | Fix agent/task fields; use local run for full traceback after safety review. |

## Project Type Detection

A project with `crew.jsonc` is treated as JSON crew unless `pyproject.toml` declares `[tool.crewai].type = "flow"`. This prevents flow projects with nested or stray `crew.jsonc` files from validating/running as JSON crews.

For classic projects, package directory names are normalized from `[project].name` by replacing spaces/hyphens with underscores, lowercasing, and removing unsupported characters. `my-crew` maps to `src/my_crew/`.

## Lockfiles and Dependency Sync

Deployment validation expects a lockfile because hosted deployment resolves dependencies from lock state. Prefer `uv.lock`; `poetry.lock` is accepted. If a deploy create/push sees no lockfile, the CLI may attempt to run project installation first and then validate again. This can mutate project dependency files, so ask before doing it in a user repository.

If `pyproject.toml` changed after the lockfile, refresh the lockfile:

```bash
uv lock
```

For old or incompatible pins, use a targeted upgrade:

```bash
uv lock --upgrade-package crewai
```

## Environment Variables and Credentials

Deployment commands may read `.env`, prompt about environment variables, and store selected keys on CrewAI AMP. Never print secret values. It is safe to discuss variable names such as `OPENAI_API_KEY`, `SERPER_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GEMINI_API_KEY`, `AZURE_OPENAI_API_KEY`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `COHERE_API_KEY`, `GROQ_API_KEY`, `TAVILY_API_KEY`, `FIRECRAWL_API_KEY`, or `EXA_API_KEY`.

Hosted operations requiring credentials include:

- `crewai login` and `crewai logout`.
- `crewai org list`, `crewai org switch`, and `crewai org current`.
- `crewai enterprise configure`.
- `crewai deploy create`, `push`, `status`, `logs`, `list`, and `remove`.
- Remote `template`, `triggers`, and repository `tool` commands.

## Git and ZIP Deployment Behavior

Deployment prepares the project for hosted execution. If a Git origin remote is available, deploy operations can use the remote repository. If no origin remote is found, the CLI uses a ZIP upload path. Deploy create/push can initialize local Git or create an initial commit in some flows; confirm with the user before allowing commands that may mutate repository state.

## Safe Pre-Deploy Workflow

1. Inspect project layout with `python scripts/inspect_crewai_cli.py --project . --json`.
2. Run `crewai version` and confirm the installed CLI is suitable.
3. Run `crewai deploy validate` from the project root.
4. Fix validation errors without running the crew unless import/runtime execution has been reviewed for safety.
5. Confirm lockfile and `.env` variable names are ready.
6. Ask before `crewai login`, `crewai deploy create`, or `crewai deploy push`.

## Routing Notes

- Route crew/task/agent validation errors to [core runtime](../../core-runtime/SKILL.md).
- Route flow subclass and flow graph issues to [flows and events](../../flows-and-events/SKILL.md).
- Route tool credential and custom tool issues to [tools and MCP](../../tools-and-mcp/SKILL.md).
- Route memory/knowledge storage deployment issues to [memory, knowledge, and RAG](../../memory-knowledge-and-rag/SKILL.md).
- Route traces and observability configuration to [observability and hooks](../../observability-and-hooks/SKILL.md).
