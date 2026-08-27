# CLI and Cloud Troubleshooting

Use this reference when CLI behavior differs from expectations. Start with read-only commands, collect exact help from the installed version, and avoid Cloud mutations until the target app/server and credentials are confirmed.

## Config Discovery Surprises

Symptoms:

- `mcp-agent config check` sees a different file than expected.
- Deploy uses config from a parent directory.
- Local dev behaves differently when run from a subdirectory.

Likely causes:

- Discovery walks from the current directory upward and checks both direct filenames and `.mcp-agent/` subdirectories.
- Supported config names are `mcp-agent.config.yaml` and `mcp_agent.config.yaml`.
- Supported secrets names are `mcp-agent.secrets.yaml` and `mcp_agent.secrets.yaml`.
- If a config file is found, secrets beside it are merged before broader secrets discovery.
- `MCP_APP_SETTINGS_PRELOAD` can bypass file discovery entirely.

Safe diagnosis:

```bash
pwd
mcp-agent config check --verbose
mcp-agent config show --raw
python scripts/check_project_config.py --project . --json
python scripts/check_project_config.py --project ./app --config ./app/mcp_agent.config.yaml --json
```

Fixes:

- Run commands from the intended project directory.
- Pass explicit `--config-dir` and `--working-dir` to deploy.
- Pass explicit `--script` to local dev commands.
- Remove or update stale parent/home `.mcp-agent` files.
- Unset `MCP_APP_SETTINGS_PRELOAD` unless intentionally using preloaded YAML.

## Schema Validation Failures

Symptoms:

- `config show` or `config check` exits with a YAML/schema error.
- `doctor` reports invalid config/secrets.
- Deploy skips materialization because settings cannot load.

Safe diagnosis:

```bash
mcp-agent config show --raw
mcp-agent config show --path mcp_agent.config.yaml
mcp-agent config show --secrets --raw
mcp-agent doctor
python scripts/check_project_config.py --project . --json
```

Common fixes:

- Fix YAML indentation and duplicate keys.
- Keep provider credentials in secrets or environment variables, not in copied snippets.
- For MCP server entries, match transport to required fields: stdio needs `command`; HTTP/SSE-style transports need `url`.
- For deployment `env`, use strings or single-key mappings only.

## Missing Cloud API Key

Symptoms:

- Deploy says login is required.
- Cloud list/log/env commands fail as unauthenticated.
- Install says an API key is required.

Safe diagnosis:

```bash
mcp-agent login --help
mcp-agent cloud auth whoami
```

Fixes:

- Run `mcp-agent login --no-open` for browserless login.
- Export `MCP_API_KEY` in CI.
- Pass `--api-key` only when command history and logs are protected.
- If using a non-default control plane, set `MCP_API_BASE_URL` or pass `--api-url` consistently.

## Non-Interactive Deploy Prompts

Symptoms:

- CI hangs or fails because deploy wants confirmation.
- Deploy asks whether to reuse deployed secrets.
- Deploy asks for missing environment values.

Fixes:

- Add `--non-interactive` so prompts become deterministic failures or reuse existing deployed secrets.
- Ensure all config `env` keys exist in the process environment or have fallback values.
- Specify `--auth` or `--no-auth` instead of relying on an interactive decision.
- Use `--no-git-tag` unless local tag creation is intended.
- Run `mcp-agent dev build --check-only --verbose` and `scripts/check_project_config.py` before deploy.

CI template:

```bash
MCP_AGENT_DISABLE_VERSION_CHECK=1 \
mcp-agent deploy "$APP_NAME" \
  --config-dir "$CONFIG_DIR" \
  --working-dir "$WORKING_DIR" \
  --ignore-file "$IGNORE_FILE" \
  --non-interactive \
  --no-git-tag \
  --retry-count 3
```

## Ignore File and Bundle Problems

Symptoms:

- Deployment uploads files that should be excluded.
- Bundle includes local caches, test artifacts, notebooks, or `.env` files.
- Deployment misses files needed at runtime.

Rules:

- Deploy does not automatically read `.gitignore`.
- Ignore precedence is explicit `--ignore-file`, then `.mcpacignore` in `--config-dir`, then `.mcpacignore` in current working directory.
- Patterns use gitignore/gitwildmatch syntax.

Fixes:

- Create a dedicated `.mcpacignore` for deployment, not just `.gitignore`.
- Keep `mcp_agent.config.yaml`, runtime source files, and `requirements.txt` included.
- Exclude local environments, caches, logs, datasets, review/test artifacts, and secret dotenv files.
- Pass `--ignore-file` explicitly in CI.

## Deployed Artifact Confusion

Symptoms:

- `mcp_agent.deployed.config.yaml` or `mcp_agent.deployed.secrets.yaml` appears after deploy.
- A raw secret unexpectedly becomes a handle.
- Previously deployed secrets are reused.

Explanation:

- Deploy materializes a sanitized config snapshot and transformed secret handles before bundling.
- `mcp_agent.deployed.config.yaml` is safe configuration for the control plane.
- `mcp_agent.deployed.secrets.yaml` stores secret handles and should be protected like deployment metadata.
- In non-interactive mode, an existing deployed secrets file is reused when present.

Fixes:

- Inspect generated files after deploy and decide which should be committed according to team policy.
- Delete or rotate stale deployed secret handles intentionally; do not blindly overwrite in CI.
- Keep raw secrets in `mcp_agent.secrets.yaml`, environment variables, or a secure secret manager.

## Client Install Overwrite Risks

Symptoms:

- `mcp-agent install` modifies the wrong client config.
- Existing server entry is overwritten.
- ChatGPT install fails for an authenticated server.

Safe workflow:

```bash
mcp-agent install "$SERVER_URL" --client claude_code --name my-server --dry-run
mcp-agent install "$SERVER_URL" --client vscode --name my-server --dry-run
```

Fixes:

- Always preview with `--dry-run`.
- Use `--name` to avoid generated-name collisions.
- Add `--force` only after confirming overwrite is intended.
- For ChatGPT, deploy or update the app with unauthenticated access if policy allows: `mcp-agent cloud apps update APP --no-auth`.
- Redact `Authorization` headers before sharing snippets.

## Cloud Auth Confusion

Symptoms:

- `mcp-agent login` works but `mcp-cloud` fails, or vice versa.
- Commands target the wrong API endpoint.
- `whoami` differs between shells.

Fixes:

- Remember `mcp-agent cloud`, `mcp-cloud`, and `mcpc` use the same Cloud command group.
- Check `MCP_API_KEY` and `MCP_API_BASE_URL` in the active shell.
- Run `mcp-agent cloud auth whoami` immediately before mutating operations.
- Avoid mixing stored credentials and per-command `--api-key` during the same troubleshooting session.

## Log Tail Filters

Symptoms:

- `cloud logger tail --follow --since 1h` fails.
- `--order-by` or `--limit` fails with `--follow`.
- Logs are too noisy.

Rules:

- `--follow` is streaming mode and cannot be combined with `--since`, non-default `--limit`, `--order-by`, `--asc`, or `--desc`.
- Batch mode supports `--since`, `--grep`, `--limit`, `--order-by timestamp|severity`, `--asc`, `--desc`, and `--format`.

Examples:

```bash
mcp-agent cloud logger tail srv_abc --since 30m --grep "ERROR|WARN" --limit 100 --format json
mcp-agent cloud logger tail srv_abc --follow --grep "timeout|failed"
```

## Env Secret Capture Failures

Symptoms:

- Deploy fails in non-interactive mode with a missing environment variable.
- `cloud env add --from-env-file` cannot infer the app.
- Pulled env files overwrite local files.

Fixes:

- For deploy capture, export each configured `env` key or provide a fallback in config.
- For bulk add, include `--app APP_OR_ID` with `--from-env-file`.
- For `env pull`, set `--output` and use `--force` only after confirming overwrite.
- Never commit pulled dotenv files or files containing resolved secret values.

## Workflow Control Mistakes

Symptoms:

- A workflow resume/cancel targets the wrong run.
- Status filtering returns no results.
- Payload parsing fails.

Fixes:

- Inspect first: `mcp-agent cloud workflows runs SERVER --limit 20 --format json`.
- Use exact `run_id` from the list output.
- Keep `--payload` as valid JSON in a single shell argument.
- Use accepted status filters: `running`, `failed`, `timed_out`, `canceled`, `terminated`, `completed`, or `continued`.
- Treat `resume`, `suspend`, and `cancel` as production mutations.
