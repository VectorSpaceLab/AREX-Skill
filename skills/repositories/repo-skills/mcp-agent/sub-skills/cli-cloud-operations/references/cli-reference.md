# CLI Reference

This reference distills the `mcp-agent`, `mcp-cloud`, and `mcpc` command surfaces for future agents. It is self-contained and intentionally favors read-only checks before commands that upload, write config files, or change Cloud resources.

## Entry Points and Global Flags

Installed console scripts:

- `mcp-agent`: primary CLI for local projects and Cloud operations.
- `mcp-cloud`: Cloud-focused entry point backed by the same Cloud command group.
- `mcpc`: short alias for the Cloud command group.
- `silsila`: legacy entry point mapped to the CLI implementation.

Useful global behavior:

- `mcp-agent --help` and subcommand `--help` are safe and should be the first source of exact options in an installed environment.
- Top-level global flags include `--verbose/-v`, `--quiet/-q` where supported, `--format text|json|yaml` on commands that expose structured output, `--color/--no-color`, and `--version`.
- Set `MCP_AGENT_DISABLE_VERSION_CHECK=1` when collecting help in CI to avoid background PyPI version-check noise.
- Prefer `uvx mcp-agent ...` for ad-hoc use without installing into the current project and `uv run mcp-agent ...` when the project already pins `mcp-agent`.

## Top-Level Command Map

| Command | Purpose | Safe first check |
| --- | --- | --- |
| `mcp-agent init` | Create templates or copy quickstarts. | `mcp-agent init --list` |
| `mcp-agent config` | Show, validate, edit, or build config. | `mcp-agent config check` |
| `mcp-agent doctor` | Run broad diagnostics for config, keys, commands, servers, and network. | `mcp-agent doctor` |
| `mcp-agent dev` | Local runtime group for start/chat/invoke/serve/build/logs/check/go/keys/models/client. | `mcp-agent dev --help` |
| `mcp-agent deploy` | Alias for Cloud deploy. Uploads/bundles when run. | `mcp-agent deploy --help` |
| `mcp-agent login` | Alias for Cloud login. Stores or uses credentials. | `mcp-agent login --help` |
| `mcp-agent install` | Install deployed server into client config. Writes unless `--dry-run`. | `mcp-agent install URL --client CLIENT --dry-run` |
| `mcp-agent cloud` | Cloud management group. | `mcp-agent cloud --help` |

## Scaffolding and Quickstarts

Use `mcp-agent init --list` before choosing a template.

Common patterns:

```bash
mcp-agent init --template basic --dir apps/research-agent
mcp-agent init --template server --dir apps/server-starter
mcp-agent init --quickstart workflow --dir workflow-demo --force
mcp-agent init --quickstart hello-world --dir cloud-hello
```

Important flags:

- `--dir/-d PATH`: destination directory, default `.`.
- `--template/-t NAME`: scaffolding template such as `basic`, `server`, `token`, `factory`, or `minimal`.
- `--quickstart NAME`: copy a curated example such as `workflow`, `researcher`, `data-analysis`, `hello-world`, `mcp`, `temporal`, or `chatgpt-app`.
- `--force/-f`: overwrite existing files; only use after confirming ownership of the destination.
- `--no-gitignore`: skip writing `.gitignore`.

Route follow-up app design to `../core-sdk/SKILL.md`. Route MCP server transport choices to `../mcp-server-integration/SKILL.md`.

## Configuration Commands

Config discovery searches upward from the current directory for either `mcp-agent.config.yaml` or `mcp_agent.config.yaml`, including `.mcp-agent/` subdirectories, then falls back to a home-level `.mcp-agent/` directory. Secrets discovery uses the same search pattern for `mcp-agent.secrets.yaml` or `mcp_agent.secrets.yaml`. When a config file is found, secrets in the same directory take precedence over broader discovery.

Safe checks:

```bash
mcp-agent config check
mcp-agent config check --verbose
mcp-agent config show --raw
mcp-agent config show --secrets --raw
mcp-agent doctor
python scripts/check_project_config.py --project . --json
```

Config command notes:

- `config show --path FILE --raw` prints YAML without schema validation.
- `config show` without `--raw` parses YAML and validates structure.
- `config check` summarizes the discovered config and secrets files, execution engine, logger, MCP server count, and provider-key availability.
- `config edit` and `config builder` are interactive and may write files. Avoid them in CI unless the workflow explicitly expects prompts.
- `MCP_APP_SETTINGS_PRELOAD` can override normal file discovery with a literal YAML settings payload; `MCP_APP_SETTINGS_PRELOAD_STRICT=1` makes invalid preload fail immediately.

## Local Development Commands

The `dev` group owns local runtime and validation commands:

| Command | Use | Notes |
| --- | --- | --- |
| `mcp-agent dev start` | Run the application script locally. | Auto-detects `main.py`, then `agent.py`; `--script` overrides. |
| `mcp-agent dev chat` | One-shot or REPL model interaction. | Supports `--message`, `--prompt-file`, `--servers`, `--url`, `--npx`, `--uvx`, `--stdio`, and listing flags. |
| `mcp-agent dev invoke` | Invoke one agent or workflow by name. | Use exactly one of `--agent` or `--workflow`; `--vars` must be JSON. |
| `mcp-agent dev serve` | Serve an app as an MCP server. | Supports `--transport stdio|http|sse`, `--port`, `--host`, `--show-tools`, and `--config`. |
| `mcp-agent dev build` | Preflight build/deploy checks. | Use `--check-only` to avoid writing a manifest. |
| `mcp-agent dev check` | Basic system/config check. | Read-only. |
| `mcp-agent dev logs` | Tail local logs. | Use for local runtime diagnostics. |
| `mcp-agent dev keys` | Manage provider API keys. | `show` and `test` are safer than `set`, `unset`, `rotate`, or `export`. |
| `mcp-agent dev models` | List or set default models. | `models list --format json` is read-only. |
| `mcp-agent dev client` | Print or write client snippets. | Use without `--write` first. |

Read-only local examples:

```bash
mcp-agent dev build --check-only --verbose
mcp-agent dev check
mcp-agent dev models list --format json
mcp-agent dev chat --list-servers --script main.py
mcp-agent dev chat --list-tools --server filesystem --script main.py
```

Mutating or interactive local commands:

- `dev start`, `dev chat`, `dev invoke`, and `dev serve` run user code from the selected script.
- `dev keys set/unset/rotate/export` changes secrets or writes files.
- `dev client --write` edits client configuration.
- `config builder`, `config edit`, and `init --force` may overwrite files.

## Cloud Command Map

All Cloud commands can be reached through `mcp-agent cloud ...`, `mcp-cloud ...`, or `mcpc ...`. The top-level `mcp-agent deploy`, `mcp-agent login`, and `mcp-agent install` are convenience aliases or nearby operations.

| Cloud area | Commands | Notes |
| --- | --- | --- |
| Auth | `cloud login`, `cloud auth login`, `cloud auth whoami`, `cloud auth logout` | `login --api-key KEY` or `MCP_API_KEY`; `--no-open` avoids opening a browser. |
| Apps | `cloud apps list`, `cloud apps status`, `cloud apps workflows`, `cloud apps update`, `cloud apps delete` | Update/delete are mutating; list/status/workflows are read-only. |
| Servers | `cloud servers list`, `cloud servers describe`, `cloud servers delete`, `cloud servers workflows` | `delete --force` skips confirmation. |
| Deploy | `cloud deploy` or top-level `deploy` | Bundles/uploads and may create/update Cloud apps. |
| Configure | `cloud configure` | `--params` and `--dry-run` are safe planning modes. |
| Logger | `cloud logger tail` | Batch mode supports filters; streaming mode has incompatible filter flags. |
| Workflows | `cloud workflows list`, `runs`, `describe/status`, `resume`, `suspend`, `cancel` | Resume/suspend/cancel mutate workflow execution state. |
| Env | `cloud env list`, `add`, `remove`, `pull` | Add/remove mutate secrets; pull writes a local output file. |

Structured read examples:

```bash
mcp-agent cloud auth whoami
mcp-agent cloud servers list --filter prod --sort-by -created --format json
mcp-agent cloud servers describe srv_abc123 --format yaml
mcp-agent cloud workflows list srv_abc123 --format json
mcp-agent cloud workflows runs srv_abc123 --status running --limit 10 --format json
```

## Help Collection

Use the bundled collector when you need a reproducible help snapshot without uploading or writing Cloud state:

```bash
python scripts/collect_cli_help.py --base-command mcp-agent --commands init cloud --json
python scripts/collect_cli_help.py --base-command mcp-agent --output cli-help.json --commands deploy install
```

The collector only appends `--help` to commands. It sets `MCP_AGENT_DISABLE_VERSION_CHECK=1` by default and redacts credential-shaped environment variables from its metadata.
