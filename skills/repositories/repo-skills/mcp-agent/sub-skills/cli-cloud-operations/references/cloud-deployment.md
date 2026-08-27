# Cloud Deployment and Operations

This reference covers the operational path from a local `mcp-agent` project to MCP Agent Cloud and client installation. Treat deploy, env mutation, app/server deletion, workflow control, and client install writes as mutating operations.

## Authentication

Authenticate before any Cloud operation that needs account state:

```bash
mcp-agent login --no-open
mcp-agent login --api-key "$MCP_API_KEY"
mcp-agent cloud auth whoami
mcp-agent cloud auth logout
```

Credential resolution uses `--api-key`, `MCP_API_KEY`, or stored credentials from `mcp-agent login`. `MCP_API_BASE_URL` or `--api-url` can override the API endpoint when targeting a non-default control plane.

For CI, prefer environment variables and non-interactive commands:

```bash
export MCP_API_KEY=...
export MCP_AGENT_DISABLE_VERSION_CHECK=1
mcp-agent cloud auth whoami
```

## Preflight Before Deploy

The current deploy command is not a read-only dry run. Use these checks before running deploy:

```bash
mcp-agent --help
mcp-agent deploy --help
mcp-agent config check --verbose
mcp-agent doctor
mcp-agent dev build --check-only --verbose
python scripts/check_project_config.py --project ./app --json
```

Preflight checklist:

- Confirm the selected project directory contains `mcp_agent.config.yaml` or `mcp-agent.config.yaml`.
- Confirm whether a secrets file exists beside the config file.
- Confirm `main.py` imports safely if deployment will materialize settings from the app.
- Confirm provider keys and Cloud key are available through secrets or environment variables.
- Confirm every required env capture value is set or has a fallback in config before using `--non-interactive`.
- Confirm the ignore file excludes local caches, build outputs, private notebooks, `.env` files, test artifacts, and large data.

## CI-Safe Deploy Command

Use explicit paths and flags so the command fails instead of asking questions:

```bash
mcp-agent deploy research-app \
  --config-dir ./app \
  --working-dir . \
  --ignore-file .mcpacignore \
  --non-interactive \
  --no-git-tag \
  --retry-count 3
```

Add one of these auth policy flags deliberately:

- `--auth`: require authentication for the deployed server.
- `--no-auth`: allow unauthenticated access; needed for clients that cannot send auth headers, but risky for private tools.
- Omit both only when preserving an existing app setting is intentional.

Use `--app-description` when the Cloud app description must be updated. Use `--api-url` and `--api-key` only when environment variables or stored credentials are not appropriate.

## Deploy Artifacts

Deploy expects a project/config directory and materializes deployment-ready files there:

- `mcp_agent.deployed.config.yaml`: sanitized configuration snapshot consumed by the control plane.
- `mcp_agent.deployed.secrets.yaml`: transformed secrets file containing secret handles, including captured `env` values.

Deployment behavior to account for:

- `--config-dir` is resolved against `--working-dir` when relative.
- If no app name is passed, the CLI tries the `name` field from config, then falls back to `default`.
- If `mcp_agent.deployed.secrets.yaml` already exists and `--non-interactive` is set, previously deployed secrets are reused where possible.
- Config materialization may load `main.py` from the config directory to find app settings; avoid top-level side effects in app modules.
- `--git-tag` creates a local git tag after Cloud app setup; use `--no-git-tag` for CI unless tags are part of release policy.

## Ignore File Rules

Deploy passes a gitignore-style file to the bundler. Precedence is:

1. `--ignore-file FILE`
2. `.mcpacignore` in `--config-dir`
3. `.mcpacignore` in the current working directory
4. default excludes only

Recommended `.mcpacignore` patterns:

```gitignore
.git/
.venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.env
.env.*
*.log
notebooks/
data/
dist/
build/
```

Do not rely on `.gitignore` alone. The deploy bundler reads `.mcpacignore` or the explicit `--ignore-file`, not the repository `.gitignore` by default.

## Environment Secrets

A config-level `env` list tells deployment which environment variables to capture as Cloud secrets. Supported forms:

```yaml
env:
  - OPENAI_API_KEY
  - {SUPABASE_URL: https://db.example.com}
```

Resolution order:

1. Current process environment value.
2. Fallback literal from config mapping.
3. Interactive prompt when not using `--non-interactive`.
4. Error when `--non-interactive` and no value/fallback exists.

Cloud env commands:

```bash
mcp-agent cloud env list my-app
mcp-agent cloud env add OPENAI_API_KEY "$OPENAI_API_KEY" --app my-app
mcp-agent cloud env add --from-env-file .env.deploy --app my-app
mcp-agent cloud env pull my-app --format env --output .env.mcp-cloud --force
mcp-agent cloud env remove OPENAI_API_KEY my-app
```

Safety notes:

- `env list` masks handles and is read-only.
- `env add` creates or updates Cloud secrets.
- `env remove` deletes a stored secret handle.
- `env pull` writes local files and may reveal resolved secret values; never commit those files.

## Configure Published Servers

Use `cloud configure` when adopting a published server template that needs user secrets:

```bash
mcp-agent cloud configure --id https://srv_example.deployments.example/mcp --params
mcp-agent cloud configure --id https://srv_example.deployments.example/mcp --dry-run --secrets-file team-secrets.yaml
mcp-agent cloud configure --id https://srv_example.deployments.example/mcp --secrets-file team-secrets.yaml
```

Modes:

- `--params`: list required secrets and exit.
- `--dry-run`: validate required parameters with mock clients without persisting secrets.
- `--secrets-file`: supply YAML values.
- `--secrets-output-file`: choose where prompted secrets are written; do not combine with `--secrets-file`.

## Logs and Observability

Batch log retrieval is safer for scripted diagnostics:

```bash
mcp-agent cloud logger tail srv_abc123 --since 1h --grep "ERROR|WARN" --limit 100 --format json
mcp-agent cloud logger tail srv_abc123 --order-by timestamp --desc --limit 50
```

Streaming mode:

```bash
mcp-agent cloud logger tail srv_abc123 --follow
```

`--follow` cannot be combined with `--since`, non-default `--limit`, `--order-by`, `--asc`, or `--desc`. Use `--grep` with either batch or streaming when narrowing messages.

## Apps and Servers

Read-only inventory:

```bash
mcp-agent cloud servers list --filter prod --sort-by -created --format json
mcp-agent cloud servers describe srv_abc123 --format yaml
mcp-agent cloud apps status app_abc123
mcp-agent cloud apps workflows app_abc123
```

Mutating operations:

```bash
mcp-agent cloud apps update app_abc123 --description "Production research agent"
mcp-agent cloud apps update app_abc123 --auth
mcp-agent cloud apps update app_abc123 --no-auth
mcp-agent cloud servers delete srv_abc123
mcp-agent cloud apps delete app_abc123
```

Only use delete commands after confirming whether the identifier is an app, configured server, or deployed server. Avoid `--force` unless the deletion target is unambiguous.

## Workflow Operations

Read-only workflow inspection:

```bash
mcp-agent cloud workflows list srv_abc123 --format json
mcp-agent cloud workflows runs srv_abc123 --status running --limit 10 --format json
mcp-agent cloud workflows describe srv_abc123 run_xyz789 --format yaml
```

Mutating workflow control:

```bash
mcp-agent cloud workflows resume srv_abc123 run_xyz789 --payload '{"response":"approved"}'
mcp-agent cloud workflows suspend srv_abc123 run_xyz789 --payload '{"reason":"maintenance"}'
mcp-agent cloud workflows cancel srv_abc123 run_xyz789
```

Payloads are JSON strings. Normalize run status filters to `running`, `failed`, `timed_out`, `canceled`, `terminated`, `completed`, or `continued`.

## Client Install

Always preview first:

```bash
mcp-agent install https://srv_abc.deployments.example \
  --client claude_code \
  --name research-agent \
  --dry-run
```

Supported clients include `vscode`, `claude_code`, `cursor`, `claude_desktop`, and `chatgpt`.

Install behavior:

- URLs without `/sse` or `/mcp` get `/sse` appended automatically.
- Authenticated clients receive an `Authorization: Bearer ...` header from the active API key.
- Claude Desktop uses an `npx mcp-remote` wrapper.
- VS Code writes project-local `.vscode/mcp.json`.
- Cursor and Claude Desktop write user-level client configs.
- ChatGPT requires unauthenticated access on the server.
- `--force` overwrites existing server configuration entries.

Use `--dry-run` when generating snippets for review or documentation. Redact bearer tokens before sharing output.
