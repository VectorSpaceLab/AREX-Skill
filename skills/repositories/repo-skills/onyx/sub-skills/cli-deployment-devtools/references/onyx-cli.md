# Onyx CLI

`onyx-cli` is the product-facing CLI. Use it to query an Onyx server, run an interactive chat TUI, generate images through a configured server-side provider, serve the TUI over SSH, install the bundled agent skill, and manage guided Docker Compose self-hosted deployments. Do not confuse it with `ods`, which is the repository developer utility covered in [ods-devtools.md](ods-devtools.md).

## Install and configure

Install one of the released distributions when the command is missing:

```bash
pip install onyx-cli
# or, inside an existing uv-managed Python environment:
uv pip install onyx-cli
```

Standalone release binaries also exist for major desktop/server platforms. Building from source is optional and requires Go 1.24+.

First-time interactive setup:

```bash
onyx-cli chat
```

The chat TUI asks for the Onyx server URL and personal access token (PAT), tests the connection, and writes config under the standard user config directory. Environment variables override the config file and are often better for CI or one-off agent calls:

```bash
export ONYX_SERVER_URL="https://your-onyx-server.example"
export ONYX_PAT="<personal-access-token>"
onyx-cli validate-config
```

Supported environment variables:

| Variable | Purpose |
| --- | --- |
| `ONYX_SERVER_URL` | Server origin or already-prefixed API base; defaults to the Onyx cloud origin. |
| `ONYX_API_PREFIX` | API path prefix; defaults to `/api`; set to an empty value only when intentionally targeting a direct backend. |
| `ONYX_PAT` | PAT used for authenticated API calls when no config file value should be used. |
| `ONYX_PERSONA_ID` | Default agent/persona ID for `ask` and `search`. |
| `ONYX_STREAM_MARKDOWN` | `true`/`false` override for progressive markdown rendering in chat. |
| `ONYX_SSH_HOST_KEY` | Host key path for `serve` when `--host-key` is not supplied. |
| `ONYX_DEPLOYMENT_DIR` | Deployment directory override for `onyx-cli deploy` when `--dir` is not supplied. |

Validation command:

```bash
onyx-cli validate-config
```

It reports the active config source, server URL, authentication status, and server version when available.

## Non-interactive behavior

When stdout or stdin is not a TTY, `onyx-cli` behaves predictably for agents and scripts:

- Running with no subcommand prints help and exits 0 instead of launching chat.
- Results go to stdout; progress, warnings, and errors go to stderr.
- ANSI styling and interactive prompts are suppressed.
- `ask` plain-text output truncates at 50000 bytes by default and saves the full answer to a temp file; pass `--max-output 0` to disable.
- `ask --json` emits NDJSON stream events and bypasses plain-text truncation.
- `search` stdout remains valid JSON when truncated: lower-ranked results are dropped and a `truncation` object includes the complete response path.
- Multi-query `search` accepts up to three query arguments and runs them concurrently. Partial failures are returned in-band per query; the command fails only if every query fails.

## Ask, search, and agents

Use `agents` to discover IDs for scoped queries:

```bash
onyx-cli agents
onyx-cli agents --json
```

Use `ask` for a synthesized answer:

```bash
onyx-cli ask "What changed in the deployment process?"
onyx-cli ask --agent-id 5 "Summarize this topic"
cat context.txt | onyx-cli ask --prompt "Find the root cause"
onyx-cli ask --json "List active integrations"
```

Useful `ask` flags:

| Flag | Use |
| --- | --- |
| `--agent-id <int>` | Override the default persona/agent. |
| `--json` | Emit NDJSON event stream rather than final plain text. |
| `--prompt <text>` | Supply the question while stdin provides context. |
| `--quiet` | Buffer and print the answer once instead of streaming. |
| `--max-output <bytes>` | Set the plain-text truncation limit; `0` disables it. |

Use `search` for source documents and structured JSON:

```bash
onyx-cli search "deployment checklist"
onyx-cli search "roadmap" "incident process" "release policy"
onyx-cli search --source slack,google_drive "auth migration status"
onyx-cli search --days 30 "recent production incidents"
onyx-cli search --agent-id 5 "engineering roadmap"
onyx-cli search --raw "API documentation"
onyx-cli search --no-query-expansion "exact error message text"
```

Default single-query shape is `{"results": [{"title", "url", "source_type", "content", "updated_at"}, ...]}`. Multi-query output is `{"searches": [{"query", "results"}, ...]}`. Use `--raw` only when you need the full API response, including lower-level fields such as citation IDs.

Useful `search` flags:

| Flag | Use |
| --- | --- |
| `--source <a,b>` | Filter by source type, for example `slack,google_drive`. |
| `--days <n>` | Restrict to recently updated results. |
| `--agent-id <int>` | Search with an agent/persona scope. |
| `--raw` | Print the full API response. |
| `--no-query-expansion` | Skip LLM query expansion for exact names, titles, or error strings. |
| `--max-output <bytes>` | Limit JSON output in non-TTY mode; `0` disables truncation. |

## Image generation and editing

Image generation runs through the image provider configured by an Onyx admin; no local image-provider key is needed. If no provider is configured, the CLI exits with code 9 and a message to configure image generation in the admin panel.

Generate images:

```bash
onyx-cli image generate -p "a red bicycle on a beach" -o bike.png
onyx-cli image generate -p "app icon, flat style" --shape square -n 3 -o icon.png
```

Edit or composite images:

```bash
onyx-cli image edit -i photo.png -p "replace the sky with a sunset" -o out.png
onyx-cli image edit -i a.png -i b.png -p "combine these into one scene" -o merged.png
```

Common flags are `--prompt/-p`, `--output/-o`, `--shape square|portrait|landscape`, `--quality/-q`, and `--num/-n`. `image edit` also requires at least one `--input-image/-i`. Output files are created exclusively; choose a new path if a file already exists.

## Chat TUI and SSH serving

Interactive chat:

```bash
onyx-cli chat
onyx-cli chat --no-stream-markdown
```

Useful chat slash commands include `/configure`, `/agent`, `/attach <path>`, `/sessions`, `/connectors`, `/settings`, `/clear`, `/help`, and `/quit`.

Serve the TUI over SSH:

```bash
onyx-cli serve --host 0.0.0.0 --port 2222
ssh your-host -p 2222
```

Clients can paste a PAT at login, or send `ONYX_PAT` through SSH environment forwarding:

```bash
export ONYX_PAT="<personal-access-token>"
ssh -o SendEnv=ONYX_PAT your-host -p 2222
```

Hardening flags include `--host-key`, `--idle-timeout`, `--max-session-timeout`, `--rate-limit-per-minute`, `--rate-limit-burst`, and `--rate-limit-cache`. Exposing an SSH endpoint is a host/network operation; confirm intended bind address and access controls first.

## Guided self-hosted deployment commands

`onyx-cli deploy` manages a Docker Compose self-hosted deployment. It writes deployment files to a user config directory by default, detects legacy guided installs, and can be pointed elsewhere with `--dir` or `ONYX_DEPLOYMENT_DIR`.

Prefer dry runs and read-only status before changing a host:

```bash
onyx-cli deploy install --dry-run
onyx-cli deploy status
onyx-cli deploy status --json
onyx-cli deploy logs api_server --tail 200
```

Install or restart:

```bash
onyx-cli deploy install
onyx-cli deploy install --lite --no-prompt
onyx-cli deploy install --include-craft
onyx-cli deploy install --dev
onyx-cli deploy install --tag v4.4.6
onyx-cli deploy install --offline --local --no-prompt
```

Important install flags:

| Flag | Use |
| --- | --- |
| `--lite` | Minimal deployment: no vector DB, Redis, model servers, or background worker. |
| `--include-craft` | Enable Craft; Docker Compose Craft uses the host Docker socket and should run only on trusted hosts. |
| `--dev` | Stack the dev overlay and publish service ports for local development/testing. |
| `--prod` | Manage an existing standalone prod compose deployment; not for casual fresh installs. |
| `--project <name>` | Docker Compose project name override. |
| `--tag <tag>` | Image tag to deploy. |
| `--local` | Use local deployment files rather than fetching release-matched copies. |
| `--offline` | Do not contact the network; relies on local files/images and implies local mode. |
| `--no-prompt` | Apply defaults without interactive prompts; be explicit about mode flags. |
| `--dry-run` | Show the plan without writing files, pulling images, or starting containers. |
| `--no-wait` | Return after starting containers instead of waiting for health. |
| `--force` | Overwrite managed hand-edited files after backup and/or recreate running services. Requires approval. |

Lifecycle commands:

```bash
onyx-cli deploy status --json
onyx-cli deploy logs api_server background --tail 100 --since 10m
onyx-cli deploy stop
onyx-cli deploy upgrade --tag v4.4.6
onyx-cli deploy upgrade --tag v4.4.6 --no-prompt --force
onyx-cli deploy uninstall
```

Safety rules:

- `status` is read-only. Exit code 0 means healthy, 9 means no install exists, and 1 means stopped/degraded/starting.
- `logs` is read-only but may expose secrets; scope services and tail windows where possible.
- `stop` pauses containers but keeps data; still confirm if the stack may be shared.
- `upgrade` preserves `.env` edits, rewrites the image tag, refreshes managed files, and backs up hand-edited managed files before overwriting.
- `uninstall` permanently removes containers, volumes, and the deployment directory. Require explicit approval; interactive runs require typing `DELETE`, and scripted runs require `--force`.

## Install the bundled CLI skill

The CLI can install its own small agent skill for using `onyx-cli` as a knowledge-query tool:

```bash
onyx-cli install-skill
onyx-cli install-skill --global
onyx-cli install-skill --copy
onyx-cli install-skill --agent claude-code
```

By default it writes a canonical project-level `.agents/skills/onyx-cli/` copy and symlinks compatible agent-specific locations. `--copy` avoids symlinks for environments that do not support them.

## Exit codes and common recovery

| Code | Name | Typical cause | Recovery |
| --- | --- | --- | --- |
| 0 | Success | Command completed. | Continue. |
| 1 | General | Unclassified failure, stopped/degraded deploy status, or unexpected stream end. | Read stderr and re-run with `--debug` if useful. |
| 2 | BadRequest | Invalid args, missing prompt/query, invalid image shape, too many search queries. | Fix flags or quoting. |
| 3 | NotConfigured | Missing PAT/config or server URL for `serve`. | Run `onyx-cli chat` or set `ONYX_SERVER_URL` and `ONYX_PAT`. |
| 4 | AuthFailure | Server returned 401/403. | Check PAT, permissions, server URL, and API prefix. |
| 5 | Unreachable | Server or deployment endpoint could not be reached. | Check network, server URL, local containers, and proxy path. |
| 6 | RateLimited | Server returned 429. | Back off and retry later. |
| 7 | Timeout | Request timed out. | Reduce request size or retry after checking service health. |
| 8 | ServerError | Server returned 5xx. | Check server logs/status before retrying. |
| 9 | NotAvailable | Missing endpoint/feature, no deployment, or no image provider. | Confirm server version/feature configuration. |

For missing Docker, image pulls, DHI login, `.env`/secret issues, or Postgres access, see [troubleshooting.md](troubleshooting.md).
