# CLI Deployment Troubleshooting

Use this guide to diagnose LangGraph CLI and `langgraph.json` failures without relying on source checkout paths.

## Install and Import Failures

### `langgraph: command not found`

Cause: `langgraph-cli` is not installed in the active environment or console scripts are not on `PATH`.

Fix:

```bash
python -m pip install -U langgraph-cli
python -m pip show langgraph-cli
langgraph --help
```

If `langgraph --help` still fails, invoke the environment's Python module tooling or reactivate the environment.

### `Required package 'langgraph-api' is not installed`

Cause: `langgraph dev` needs the in-memory server extra.

Fix:

```bash
python -m pip install -U "langgraph-cli[inmem]"
langgraph dev -c langgraph.json --no-browser
```

Python must be 3.11 or newer for the in-memory server.

### Graph module import fails

Common causes:

- `graphs.agent` path is relative to the wrong directory.
- The local package directory is missing from `dependencies`.
- The graph file imports optional packages not installed in the active environment.
- The graph attribute name after `:` is misspelled.
- The module has import-time side effects that require credentials or services.

Fix sequence:

```bash
python skills/langgraph/sub-skills/cli-deployment/scripts/validate_langgraph_config.py langgraph.json --check-imports
python -m pip install -e .
langgraph validate -c langgraph.json
```

If import-time credentials are required, refactor code so credentials are read when the graph runs, not while the module imports.

## Invalid Config and Data

### Missing `dependencies`

Dependency-based Python configs require `dependencies`. Minimal repair:

```json
{
  "dependencies": ["."],
  "graphs": {"agent": "./agent.py:graph"}
}
```

If the project is uv-managed, use `source.kind: "uv"` and remove `dependencies`.

### Missing `graphs`

Add at least one graph:

```json
{
  "graphs": {
    "agent": "./my_agent/graph.py:graph"
  }
}
```

### Invalid Python version

Symptoms include `Invalid Python version format` or `Minimum required version`.

Fixes:

- Use `3.11`, `3.12`, or `3.13`.
- Do not specify patch versions such as `3.11.8`.
- Do not use Python below 3.11.
- Do not use `bullseye` suffixes; use `image_distro` with `debian`, `bookworm`, or `wolfi`.

### Unknown top-level key warnings

The CLI warns for unrecognized keys and suggests close matches. Treat these as typos unless the user's installed CLI explicitly supports a newer field. Confirm with:

```bash
langgraph validate -c langgraph.json
```

## Graph Object Problems

### Target exports an uncompiled graph

Symptom: config validates but server startup fails because the exported attribute is a builder rather than a compiled runnable graph.

Fix:

- In the graph module, call `.compile()`.
- Export the compiled object under the name used in `langgraph.json`.
- Review [`../../graph-runtime/SKILL.md`](../../graph-runtime/SKILL.md) for compile/runtime patterns.

### Sync vs async confusion

Symptoms include event loop errors, blocking-operation warnings, or graph nodes hanging under `dev`.

Fixes:

- Use async graph nodes for async model/tool clients.
- Do not call `asyncio.run()` inside already-running async graph paths.
- Avoid blocking I/O in async nodes; switch to async client APIs or run blocking work in a thread.
- Use `langgraph dev --allow-blocking` only to unblock debugging, not as a production fix.

### Prebuilt agent dependency failures

If the graph uses prebuilt agents, verify compatible package imports and model/tool setup. See [`../../prebuilt-agents/SKILL.md`](../../prebuilt-agents/SKILL.md). Missing model provider packages belong in `dependencies` or the project package metadata.

## Docker and Service Failures

### Docker not installed

`langgraph build` checks for Docker and fails with `Docker not installed` if unavailable. Install/start Docker Desktop or Docker Engine before `build`, `up`, or Dockerfile validation that requires Docker capabilities.

### Port mismatch

Common mistake: checking `8123` after starting `dev`, or checking `2024` after starting `up`.

- `langgraph dev` default API port: `2024`.
- `langgraph up` default exposed API port: `8123`.

Always state the command and explicit port in handoff notes.

### `up` exits when services stop

Without `--wait`, `up` uses abort-on-container-exit behavior. For a normal local server workflow, prefer:

```bash
langgraph up -c langgraph.json --port 8123 --wait
```

### Persistent state or database failures

If the app relies on checkpointing, stores, Postgres, or custom persistence:

- Confirm the config's `checkpointer` and `store` fields.
- Confirm `--postgres-uri` or the default local service is appropriate.
- Confirm credentials are passed through `env` or the shell.
- See [`../../persistence/SKILL.md`](../../persistence/SKILL.md).

### Distributed runtime mode issues

`--engine-runtime-mode distributed` creates separate executor and orchestrator behavior. Use it only when the deployment needs that separation. For most local debugging, default `combined_queue_worker` is simpler.

## Build and Image Failures

### Unsafe custom build commands

The CLI rejects custom `--install-command` and `--build-command` containing dangerous shell content. Avoid quotes, backticks, semicolons, pipes, redirection, `$`, newlines, tabs, single `&`, and backslashes. Use package manager files or simple commands such as:

```bash
langgraph build -c langgraph.json -t app:latest --build-command "npm run build"
```

If quoting is blocked in the installed version, move the logic into package scripts and call the package script directly.

### `api_version` range and base image conflict

Compatible ranges such as `~=0.11.0.dev5` cannot be combined with a tagged `base_image`. Either remove the tag from `base_image` or pin `api_version` directly.

### Local dependency path outside build context

Docker generation may need extra build contexts for local paths outside the app directory. Prefer keeping app packages under a clear workspace root, or use `source.kind: "uv"` with explicit `source.root` and `source.package` for uv workspaces.

## JS/TS Deployment Pitfalls

- Python `langgraph dev` rejects JS graphs; use the JS CLI path.
- Node graph extensions include `.ts`, `.mts`, `.cts`, `.js`, `.mjs`, and `.cjs`.
- Node major version must be at least `20`.
- `package.json` `engines.node` should be a major version like `20`, not `20.11.1`.

## Security Warnings

- Do not bind `langgraph dev` to `0.0.0.0` unless the network is trusted.
- Do not commit `.env` files or API keys.
- Review generated Dockerfiles before building and publishing images.
- Treat `dockerfile_lines`, custom base images, pip config files, and custom build commands as supply-chain sensitive.
- Ask before running commands that pull images, start containers, mutate volumes, or contact hosted deployment services.

## Exclusions

This sub-skill intentionally excludes maintainer-only release automation, CI internals, benchmark-only code, expensive notebooks, and tests that require network access or hosted credentials. Runtime guidance is self-contained and does not require reading original repository files.
