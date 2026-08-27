# LangGraph CLI Reference

This reference summarizes the deployment-facing `langgraph` commands and their safe validation order.

## Installation and Entry Point

The console entry point is:

```text
langgraph = langgraph_cli.cli:cli
```

Install paths:

```bash
pip install -U langgraph-cli
pip install -U "langgraph-cli[inmem]"
```

Use the `inmem` extra for `langgraph dev`. Without it, `dev` can fail with a message asking for `pip install -U "langgraph-cli[inmem]"`. The in-memory server requires Python 3.11 or newer.

## Command Selection

| Command | Use When | Avoid When |
| --- | --- | --- |
| `langgraph new [PATH] --template TEMPLATE` | Starting from an official template | The app already exists and only config is broken |
| `langgraph validate -c langgraph.json` | Checking config syntax and known CLI validation | Graph imports or Docker build context need deeper local checks |
| `langgraph dev -c langgraph.json` | Fast Python development with hot reload | JS/TS graphs, production-like Docker services, or no `inmem` extra |
| `langgraph up -c langgraph.json` | Docker Compose local deployment | Docker is unavailable or the user has not approved service startup |
| `langgraph dockerfile Dockerfile -c langgraph.json` | Generating reviewable Docker artifacts | The user only needs a quick in-memory local run |
| `langgraph build -c langgraph.json -t IMAGE` | Building a deployable Docker image | Docker is unavailable or no image tag is chosen |
| `langgraph deploy` | Hosted deployment workflows | Credentials, target project, or hosted deployment intent is unclear |

## `validate`

```bash
langgraph validate -c langgraph.json
```

Behavior:

- Loads JSON and reports invalid JSON parse failures.
- Warns for unknown top-level keys and likely misspellings.
- Calls config validation and exits non-zero on `click.UsageError` or `ValueError`.
- On success, prints `Configuration file ... is valid` and the graph count.

Recommended preflight:

```bash
python skills/langgraph/sub-skills/cli-deployment/scripts/validate_langgraph_config.py langgraph.json --check-imports
langgraph validate -c langgraph.json
```

The bundled script catches common local file/import mistakes before the official CLI is invoked.

## `dev`

```bash
langgraph dev -c langgraph.json --host 127.0.0.1 --port 2024
```

Defaults and options:

- Host defaults to `127.0.0.1` for security.
- Port defaults to `2024`.
- `--no-reload` disables automatic reload.
- `--no-browser` skips opening a browser.
- `--n-jobs-per-worker N` caps concurrent jobs per worker; default behavior is 10.
- `--debug-port PORT` enables remote debugging; install `debugpy` first.
- `--wait-for-client` waits for a debugger on the debug port.
- `--studio-url URL` points Studio at a non-default instance.
- `--allow-blocking` allows synchronous blocking operations during debugging.
- `--tunnel` exposes the local server through a public tunnel; do not combine with SSL options.
- `--ssl-certfile` and `--ssl-keyfile` must be provided together.

Important limitations:

- `dev` imports `langgraph_api.cli.run_server`; install `langgraph-cli[inmem]` if missing.
- `dev` rejects JS graph configs and directs users to the JS CLI.
- The command appends the current working directory and local dependency directories to `sys.path`, so relative paths should be checked from the app root.

## `up`

```bash
langgraph up -c langgraph.json --port 8123 --wait
```

Defaults and options:

- Port defaults to `8123`.
- Uses Docker Compose and prints API, Docs, and Studio URLs after startup.
- `--wait` waits for services to start.
- Without `--wait`, Compose is run with abort-on-container-exit behavior.
- `--watch` restarts on file changes.
- `--verbose` streams detailed server logs.
- `--recreate` forces container recreation and renews anonymous volumes.
- `--pull/--no-pull` controls base image pulling.
- `--docker-compose PATH` adds services from another Compose file.
- `--postgres-uri URI` uses an existing Postgres database instead of the default local database behavior.
- `--image IMAGE` skips building and uses an already built image.
- `--base-image IMAGE` pins the API server base image.
- `--api-version VERSION` selects the API server version.
- `--engine-runtime-mode combined_queue_worker|distributed` chooses one combined service or distributed executor/orchestrator containers.
- `--debugger-port PORT` serves the debugger UI locally; `--debugger-base-url URL` defaults debugger access to `http://127.0.0.1:[PORT]`.

Credential notes:

- Local dev with Docker may require `LANGSMITH_API_KEY` with LangSmith Deployment access.
- Production use requires `LANGGRAPH_CLOUD_LICENSE_KEY`.
- Do not invent or embed keys; ask the user to provide them through environment management.

## `dockerfile`

```bash
langgraph dockerfile Dockerfile -c langgraph.json
langgraph dockerfile Dockerfile -c langgraph.json --add-docker-compose
```

Behavior:

- Validates config before writing.
- Emits `✅ Configuration validated!` and `✅ Created: Dockerfile` on success.
- Writes a Dockerfile to the requested path.
- Reports additional Docker build contexts when local dependencies need them.
- With `--add-docker-compose`, also writes Compose, `.dockerignore`, and an empty `.env` scaffold if `.env` does not exist.
- Generated `.dockerignore` excludes `.env`, `.env.*`, dependency directories, logs, VCS files, build/cache directories, IDE files, and tests.

Use this command when an agent needs a safe reviewable artifact before building or starting containers.

## `build`

```bash
langgraph build -c langgraph.json -t my-app:latest
```

Behavior and options:

- Requires Docker to be installed.
- Requires `-t/--tag`.
- Validates config before building.
- `--pull/--no-pull` chooses latest or local base images.
- `--base-image` pins a base image.
- `--api-version` selects the API server version.
- `--engine-runtime-mode distributed` can choose different default base image behavior.
- Extra unknown options are forwarded as Docker build args because the command accepts unprocessed trailing arguments.

Custom commands:

```bash
langgraph build -c langgraph.json -t app:latest --install-command "npm ci" --build-command "npm run build"
```

The CLI blocks dangerous shell content in `--install-command` and `--build-command`: quotes, backticks, backslashes, newlines, tabs, nulls, pipes, semicolons, `$`, redirection, and single `&` are disallowed. `&&` chaining is allowed. Prefer package-manager files and config over custom commands.

## `new`

```bash
langgraph new my-app --template TEMPLATE_NAME
```

Use this only when creating a project from a template. Template availability is maintained by the CLI; avoid hard-coding template names unless the user supplies one or `langgraph new --help` lists it.

## `deploy`

`deploy` is wired as a top-level command group. Treat hosted deploy flows as credential- and platform-sensitive. Before running it, confirm the target environment, required credentials, and whether network calls or remote mutation are acceptable.

## Safe Agent Workflow

1. Read or create `langgraph.json`.
2. Run the bundled offline checker.
3. Run `langgraph validate`.
4. For local Python debugging, run `langgraph dev` with explicit host/port.
5. For Docker review, run `langgraph dockerfile`.
6. For Docker execution, ask before `langgraph up` if it may start services, pull images, or use credentials.
7. For images, ask for a tag before `langgraph build`.
8. For hosted deployment, confirm remote target and credentials before `langgraph deploy`.
