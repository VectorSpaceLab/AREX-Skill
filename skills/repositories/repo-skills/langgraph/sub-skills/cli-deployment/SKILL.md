---
name: cli-deployment
description: "Create, validate, run, containerize, and troubleshoot LangGraph
  app deployments with the `langgraph` CLI and `langgraph.json`."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LangGraph CLI Deployment

Use this sub-skill when a task involves shipping a LangGraph app through the official `langgraph` CLI: creating starter projects, repairing `langgraph.json`, running the in-memory development server, running Docker Compose locally, generating Dockerfiles, building images, or choosing the right deployment command.

## Quick Routing

- Use `langgraph validate` or `scripts/validate_langgraph_config.py` when the task is about config correctness before running anything expensive.
- Use `langgraph dev` for local Python development with hot reload and in-memory server behavior.
- Use `langgraph up` for Docker-backed local deployment with Compose, database/service containers, and production-like networking.
- Use `langgraph dockerfile` when the user wants generated Dockerfile/Compose artifacts to review or customize.
- Use `langgraph build` when the user wants a tagged Docker image.
- Use `langgraph new` when starting from an official template.
- Use `langgraph deploy` only for hosted deployment workflows after credentials/project requirements are clear.

## References and Scripts

- Read [`references/cli-reference.md`](references/cli-reference.md) for command selection, options, defaults, expected outputs, and validation order.
- Read [`references/configuration.md`](references/configuration.md) for `langgraph.json` schemas, Python vs JS branches, graph spec formats, Docker image knobs, and secure config patterns.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for failures around installation, imports, invalid graph pointers, optional dependencies, Docker, sync/async behavior, and security warnings.
- Run [`scripts/validate_langgraph_config.py`](scripts/validate_langgraph_config.py) for offline shape/path/import checks that do not require Docker, credentials, or network.

## Minimal Config Pattern

For a Python app, start with:

```json
{
  "$schema": "https://langgra.ph/schema.json",
  "python_version": "3.11",
  "dependencies": ["."],
  "graphs": {
    "agent": "./agent.py:graph"
  },
  "env": ".env"
}
```

Important defaults and constraints:

- `dependencies` and `graphs` are required for dependency-based Python configs.
- `python_version` accepts `3.11`, `3.12`, or `3.13` in the public schema; patch versions such as `3.11.8` are invalid.
- If omitted for Python graphs, the CLI defaults `python_version` to `3.11`.
- `image_distro` defaults to `debian`; valid values are `debian`, `bookworm`, and `wolfi`; `bullseye` is deprecated.
- `pip_installer` accepts `auto`, `pip`, or `uv`.
- Graph specs use `./path/to/file.py:attribute` for Python and JS/TS extensions for Node graphs.
- The graph object should be an already compiled LangGraph/Pregel object or an accepted graph factory/context manager per CLI schema; see [`../graph-runtime/SKILL.md`](../graph-runtime/SKILL.md) for graph compilation and runtime semantics.

## Validate Before Running

Preferred validation sequence:

1. Run the bundled offline checker:

   ```bash
   python skills/langgraph/sub-skills/cli-deployment/scripts/validate_langgraph_config.py langgraph.json --check-imports
   ```

2. Run the official CLI validator:

   ```bash
   langgraph validate -c langgraph.json
   ```

3. If the task involves Docker output, generate a Dockerfile before building:

   ```bash
   langgraph dockerfile Dockerfile -c langgraph.json
   ```

Expected `langgraph validate` success output includes `Configuration file ... is valid` and the number of graphs found. Unknown top-level keys can emit warnings such as likely misspellings.

## Local Development

Use `dev` for fast Python iteration:

```bash
pip install -U "langgraph-cli[inmem]"
langgraph dev -c langgraph.json --host 127.0.0.1 --port 2024
```

Operational notes:

- `langgraph dev` defaults to host `127.0.0.1` and port `2024`; only use `0.0.0.0` on trusted networks.
- `--no-reload` disables hot reload, and `--no-browser` skips automatic browser launch.
- `--debug-port PORT` enables remote debugging and requires `debugpy`; `--wait-for-client` pauses startup until a debugger attaches.
- `--allow-blocking` disables blocking-operation errors; use it only as a tactical debug aid and fix blocking synchronous I/O in production paths.
- `dev` does not support JS graphs in this CLI version; use the JS CLI for JS/TS graphs.

## Docker-Backed Local Runs

Use `up` when the user wants production-like local infrastructure:

```bash
langgraph up -c langgraph.json --port 8123 --wait
```

Key behavior:

- `up` exposes the API on port `8123` by default, unlike `dev` port `2024`.
- `--wait` waits for services to start; without it, Compose runs with abort-on-container-exit semantics.
- `--watch` restarts on file changes.
- `--verbose` shows detailed logs.
- `--recreate` recreates containers and renews anonymous volumes.
- `--pull/--no-pull` controls whether latest base images are pulled.
- `--postgres-uri` points at an existing Postgres database; omit it to let the CLI compose local services.
- `--engine-runtime-mode distributed` uses separate executor and orchestrator containers; default is `combined_queue_worker`.
- `--debugger-port PORT` pulls and serves the debugger UI; `--debugger-base-url URL` controls which API URL that debugger uses.
- For local dev with Docker, `LANGSMITH_API_KEY` may be required for LangSmith Deployment access; production use requires `LANGGRAPH_CLOUD_LICENSE_KEY`.

## Build and Dockerfile Workflows

Generate reviewable artifacts:

```bash
langgraph dockerfile Dockerfile -c langgraph.json --add-docker-compose
```

Build a tagged image:

```bash
langgraph build -c langgraph.json -t my-langgraph-app:latest
```

Build notes:

- `dockerfile` validates config, writes a Dockerfile, and can add Compose, `.dockerignore`, and `.env` scaffolding.
- `build` requires Docker, a tag via `-t/--tag`, and optional `--base-image`/`api_version` pinning.
- Compatible `api_version` ranges include forms like `~=0.11.0.dev5` and `>~=0.11.0.dev5`.
- Custom `--install-command` and `--build-command` reject unsafe shell characters and patterns, including quotes, backticks, pipes, redirection, semicolons, variables, newlines, and single `&`; `&&` chaining is allowed.
- Prefer config-managed dependencies over custom shell commands whenever possible.

## Dependency and Source Choices

For dependency-based Python deployments:

- Put PyPI packages and local relative directories in `dependencies`.
- Use `"."` when the config lives at the app package root.
- Local dependency entries must point at real directories that can be installed or copied into the Docker context.
- Use `pip_config_file` for pip index configuration, but avoid committing credentials.

For `uv`-managed Python deployments:

```json
{
  "python_version": "3.12",
  "source": {"kind": "uv", "root": ".", "package": "agent"},
  "graphs": {"agent": "./src/agent/graph.py:graph"}
}
```

Rules:

- `source.kind` currently supports only `uv`.
- `source.kind: "uv"` is Python-only and requires `python_version`.
- Remove `dependencies`; packages come from `pyproject.toml` and `uv.lock`.
- Use `source.package` when a uv workspace root has multiple possible members.

For JS/TS deployments:

- Graph file extensions such as `.ts`, `.mts`, `.cts`, `.js`, `.mjs`, and `.cjs` select the Node branch.
- Node version defaults to `20` for Node graphs and must be at least major version `20`.
- `package.json` `engines.node` must be a major version only, not `20.x.y`.
- JS in-memory `langgraph dev` is not supported by this Python CLI version; use the JS CLI path.

## Graph Export Repair Checklist

When `graphs` points to a bad object:

1. Confirm each spec has exactly one `:` separating module path and attribute.
2. Confirm the module path exists relative to the `langgraph.json` directory.
3. Confirm local package directories listed in `dependencies` are importable or installable.
4. Import the target with `python skills/langgraph/sub-skills/cli-deployment/scripts/validate_langgraph_config.py langgraph.json --check-imports`.
5. If the object is an uncompiled `StateGraph`, compile it in source code and export the compiled object; see [`../graph-runtime/SKILL.md`](../graph-runtime/SKILL.md).
6. If the graph relies on prebuilt agents/tools, persistence, or SDK clients, cross-check [`../prebuilt-agents/SKILL.md`](../prebuilt-agents/SKILL.md), [`../persistence/SKILL.md`](../persistence/SKILL.md), and [`../sdk-clients/SKILL.md`](../sdk-clients/SKILL.md).

## Security and Secrets

- Prefer `env: ".env"` for local development and keep secret files out of source control.
- Do not put real API keys directly in `langgraph.json` unless the user explicitly requests an ephemeral local-only example.
- Keep `dev --host 127.0.0.1` unless there is a trusted-network reason to expose the server.
- Review generated Docker artifacts before publishing images, especially `dockerfile_lines`, `pip_config_file`, `base_image`, `api_version`, and local dependencies.
- Do not run Docker build/up commands automatically if they may pull images, start services, consume credentials, or mutate volumes without user confirmation.

## Completion Checklist

Before handing off a deployment change:

- `langgraph.json` has valid `dependencies`/`source`, `graphs`, supported runtime versions, and no unknown typo keys.
- Graph targets import successfully or the remaining import failure is explained with exact missing package/module names.
- Command choice is justified: `dev`, `up`, `dockerfile`, `build`, or `deploy`.
- Ports are explicit when communicating expected URLs: `dev` defaults to `2024`; `up` defaults to `8123`.
- Docker requirements, credentials, optional extras, and persistence backends are called out.
- Generated files do not embed secrets, local absolute paths, or private environment paths.
