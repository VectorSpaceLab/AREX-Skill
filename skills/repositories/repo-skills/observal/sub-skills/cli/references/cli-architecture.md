# CLI architecture

This reference is the operating map for the Python `observal` CLI. It distills the command hierarchy, shared contracts, and code surfaces needed for safe CLI edits without reopening the original documentation.

## Entry points and startup

| Surface | Contract |
| --- | --- |
| `pyproject.toml` `[project.scripts]` | `observal = "observal_cli.main:app"`. The sandbox helper entry points are `observal-sandbox-run` and `observal-sandbox-mcp`; they are not the main CLI command tree. |
| `observal_cli.main` import | Creates the root Typer app named `observal`, uses `ErrorHandlingGroup`, imports and registers command modules, and registers the post-command update banner. |
| Root callback | Configures logging, migrates legacy shimmed MCP configs back to direct commands, synchronizes bundled Observal skills, then attempts local lockfile migration. |
| Package-conflict guard | Importing `observal_cli.main` checks whether an unrelated legacy package named `observal` is installed and exits with a remediation message if it conflicts with `observal-cli`. |
| Update banner | Printed only after commands in an interactive TTY, skipped for `self`, `server`, CI, and `OBSERVAL_NO_UPDATE_CHECK`. It must not pollute non-TTY automation. |

Importing the app should be read-only except for the legacy package-conflict check. Startup side effects that touch user state live in the root callback and run only when a CLI command is invoked.

## Registered command hierarchy

Root executable commands currently include:

- `observal api`
- `observal outdated`
- `observal reconcile`
- `observal scan`

Top-level groups currently include:

- `observal admin`
- `observal agent`
- `observal auth`
- `observal config`
- `observal doctor`
- `observal inbox`
- `observal ops`
- `observal registry`
- `observal self`
- `observal server`
- `observal team`

Important nested registration rules:

- `observal registry` contains `mcp`, `skill`, `hook`, `prompt`, `sandbox`, `models`, `version`, `recommend`, and `bulk`.
- `co-authors`, `transfer-owner`, `archive`, and `unarchive` are dynamically attached to component apps and the Agent app.
- `observal agent pull` is registered into the Agent app, not as a root command.
- `observal ops logs` and `observal ops insights` are nested under `ops`.
- `observal doctor support` is nested under `doctor`.
- `observal server migrate` is nested under `server`.

Use command introspection or `--help` to verify the final path. Do not document historical aliases as canonical paths.

## Module ownership map

| Module or file | Owns |
| --- | --- |
| `observal_cli/main.py` | Root app, top-level group wiring, startup callback, update banner. |
| `observal_cli/cmd_auth.py` | `auth` group and `config` group registration. Login, logout, whoami, status, change-password, username, config show/set/path/alias/aliases. |
| `observal_cli/cmd_api.py` | `observal api` escape hatch for authenticated `/api/v1/...` JSON endpoints. |
| `observal_cli/cmd_scan.py` | `observal scan`; read-only local harness inventory. |
| `observal_cli/cmd_doctor.py` | `doctor`, `doctor patch`, `doctor cleanup`; diagnosis and managed telemetry instrumentation commands. |
| `observal_cli/cmd_support.py` | `doctor support bundle` and `doctor support inspect`. |
| `observal_cli/cmd_agent.py` | Agent create, bulk-create, list, my, show, install, archive/delete, unarchive, init, add, build, publish, release, versions. |
| `observal_cli/cmd_pull.py` | Full `observal agent pull` installation workflow. |
| `observal_cli/cmd_mcp.py`, `cmd_skill.py`, `cmd_hook.py`, `cmd_prompt.py`, `cmd_sandbox.py` | Registry component commands for each component type. |
| `observal_cli/cmd_bulk.py` | Mixed registry bulk submission. |
| `observal_cli/cmd_component.py` | Registry component version publish/list. |
| `observal_cli/cmd_models.py` | Registry-backed harness model catalog inspection. |
| `observal_cli/cmd_recommend.py` | Personalized or fallback registry recommendations. |
| `observal_cli/cmd_team.py` | Teamspaces, members, visibility, join requests, invitations. |
| `observal_cli/cmd_inbox.py` | Signed-in user's work and event feed. |
| `observal_cli/cmd_outdated.py` | Installed-version comparison against registry state. |
| `observal_cli/cmd_reconcile_cli.py` | Manual session reconciliation/backfill. |
| `observal_cli/cmd_ops.py` | `ops` commands, `admin` commands, `self` commands, and review subcommands. |
| `observal_cli/cmd_logs.py` | `ops logs`. |
| `observal_cli/cmd_insights.py` | `ops insights`. |
| `observal_cli/cmd_server.py` | Embedded server lifecycle plus Docker upgrade/rollback/version commands. |
| `observal_cli/cmd_migrate.py` | `server migrate` PostgreSQL and ClickHouse export/import/validate commands. |

Keep harness-specific scanning, hook detection, config generation, and session parsing in adapters and harness registries. The CLI orchestrates adapters; it should not grow new ad hoc harness conditionals when an adapter method exists.

## Shared output contract

All structured commands must use the shared renderer in `observal_cli.render`.

| Helper | Use |
| --- | --- |
| `OutputMode` | Type `--output/-o`; valid values are `table` and `json`. |
| `output_json(data)` | Finite JSON documents. Lists become `{"items": [...], "total": N, "page": 1, "page_size": N}` unless `raw=True`. |
| `output_json_line(data)` | JSON Lines streams such as log follow or insight-generation progress. |
| `output_table(table)` / `console.print(table)` | Human table output only after the JSON branch has returned. |
| `esc(value)` | Escape untrusted text before interpolation into Rich markup. |

Rules that must not be broken:

- JSON mode writes exactly machine JSON to stdout for success.
- JSON mode must not emit prompts, spinners, progress banners, Rich markup, update notices, or human warnings on stdout.
- Empty lists remain valid JSON envelopes.
- Detail and mutation commands return direct result objects unless the command has a documented envelope.
- `observal api` is the raw endpoint exception: it preserves arrays and objects exactly with `raw=True`.
- Streams emit compact JSON Lines, one object per line, and are distinct from finite JSON documents.
- A file destination option must not be named or treated as the format selector. Use `--file`, `--archive`, `--output-dir`, or another explicit destination name.

Use this pattern for finite commands:

```python
if output == "json":
    output_json(result)
    return

# human-only Rich or prompt behavior below
```

For nested helpers that may print human progress, use a null context or redirected stdout/stderr while building JSON results.

## Shared error contract

All CLI failures must flow through `observal_cli.errors` or the shared `observal_cli.client` wrappers.

| Category | Exit code | Typical meaning |
| --- | ---: | --- |
| `unexpected` | 1 | Unclassified or internal failure. |
| `usage` | 2 | Typer/Click syntax or invalid output mode. |
| `authentication` | 3 | Missing, expired, or invalid authentication. |
| `permission` | 4 | Filesystem or server authorization denied. |
| `not_found` | 5 | Requested local or server resource missing. |
| `conflict` | 6 | Existing state blocks the requested change. |
| `validation` | 7 | Bad argument, enum, file shape, confirmation, or incompatible options. |
| `rate_limit` | 8 | Server rate limit. |
| `unavailable` | 9 | Network, server, dependency, timeout, database, filesystem, or process unavailable. |
| `version_mismatch` | 10 | CLI and server version mismatch. |

Error behavior:

- Human errors go to stderr as a Rich block with category, operation, resource, remediation, request ID, and debug-only detail.
- JSON errors go to stderr as one JSON object and leave stdout empty.
- Debug detail appears only when `--debug` is present.
- Never include secrets, tokens, authorization headers, passwords, private connection URLs, or submitted secret payload fields in messages, resources, remediation, details, logs, or final reports.

HTTP commands use `observal_cli.client.get`, `post`, `put`, `patch`, `delete`, `request_json`, `get_text`, or `get_with_headers`. New client call sites require human labels in `observal_cli.error_context.OPERATION_LABELS`; a new command module also requires a resource label in `RESOURCE_LABELS`.

## Client and retry contract

`observal_cli.client` owns authenticated server access:

- Loads server URL and bearer token from `observal_cli.config`.
- Sends `Authorization: Bearer ...` and `X-Observal-CLI-Version` headers.
- Enforces exact CLI/server version compatibility once per process for authenticated commands, except recovery groups `self` and `server`.
- Refreshes access tokens once after a 401 response when a refresh token is present.
- Retries only authenticated `GET` requests on HTTP 429, 503, and 504, honoring `Retry-After`.
- Never automatically retries `POST`, `PUT`, `PATCH`, or `DELETE` after a transient response because server state may be unknown.
- Converts HTTP status, connection, timeout, invalid JSON, and content-type failures into categorized `CliError` results with request IDs when available.

When you add a mutation command, design the verification read before considering any retry.

## Config and local state

| File or setting | Contract |
| --- | --- |
| `~/.observal/config.json` | Server URL, tokens, timeout, update-check settings. Written atomically with mode `0600`; output redacts token values. |
| `~/.observal/aliases.json` | Local aliases for UUIDs or canonical identities. Written atomically with mode `0600`. |
| `~/.observal/last_results.json` | Cached list results for numeric shorthand. Agents should prefer UUIDs and `qualified_name`; row numbers are human convenience only. |
| `~/.observal/lockfile.json` | Installed registry state used by `outdated`, `reconcile`, and Agent/component installation tracking. |
| `OBSERVAL_SERVER_URL` | Overrides persisted server URL for the current invocation. |
| `OBSERVAL_ACCESS_TOKEN`, `OBSERVAL_API_KEY`, `OBSERVAL_TOKEN` | Token sources; direct and `_FILE` forms are mutually exclusive for secret resolver inputs. |
| `OBSERVAL_TIMEOUT` | Authenticated request timeout in seconds. |
| `OBSERVAL_PASSWORD`, `OBSERVAL_CURRENT_PASSWORD`, `OBSERVAL_NEW_PASSWORD` | Password inputs for noninteractive auth workflows; `_FILE` forms are preferred. |

Do not reintroduce persisted `output` or `color` settings. Select JSON explicitly per command.

## API route prefixes used by CLI workflows

Use dedicated commands when possible. The authenticated escape hatch accepts only canonical relative `/api/v1/...` paths, rejects full URLs, traversal, fragments, and inline query strings, and takes query parameters through repeated `--param KEY=VALUE` options.

Common command families call these server areas:

| CLI family | Common route area |
| --- | --- |
| `auth` | `/api/v1/auth/...` and `/health` for login/status checks. |
| `registry mcp/skill/hook/prompt/sandbox` | `/api/v1/mcp`, `/api/v1/skills`, `/api/v1/hooks`, `/api/v1/prompts`, `/api/v1/sandboxes`, plus `/api/v1/registry/resolve`. |
| `agent` and `agent pull` | `/api/v1/agents` and Agent install/build/version endpoints. |
| `team` | `/api/v1/teams` and team access/visibility endpoints. |
| `admin review` | `/api/v1/review`. |
| `admin` governance | `/api/v1/admin/...`, audit, security, SAML, SCIM, and settings routes. |
| `ops traces` | `/api/v1/sessions` and `/api/v1/sessions/{session_id}`. |
| `ops insights` | `/api/v1/insights/...`. |
| `reconcile` | Session ingest/reconciliation APIs through the telemetry delivery client. |

Server-side implementation details belong to the server sub-skill; the CLI's job is to validate inputs, call shared client helpers, and preserve the user-facing contract.

## Static self-check

Run the bundled helper from a repository root after any command-tree or bundled-skill change:

```bash
python scripts/check_cli_contract.py --repo-root . --output json
```

If dependencies are not installed in the current Python, run it through the project environment or supply the missing CLI runtime dependencies. A healthy result reports `ok: true`, the root group class as `ErrorHandlingGroup`, the expected top-level command names, a nonzero executable count, and all six bundled skill directories present.
