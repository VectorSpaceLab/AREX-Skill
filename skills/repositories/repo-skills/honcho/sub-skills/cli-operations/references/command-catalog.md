# Honcho CLI Command Catalog

This reference summarizes the `honcho` command surface that is most useful for agents debugging Honcho deployments. Use `--json` for machine consumption and add `-w`, `-p`, and `-s` explicitly unless the shell environment already scopes the command.

## Installation And Entrypoint Facts

- Published tool install: `uv tool install honcho-cli`.
- Python support: CLI package requires Python 3.11 or newer.
- Runtime entry point: `honcho` maps to `honcho_cli.main:app`.
- Core dependencies: Typer/Click for command parsing, Rich for human output, `honcho-ai` for SDK calls, and HTTPX for OAuth/device-flow transport.
- Version check: `honcho --version` prints `honcho-cli <version>`.
- Top-level `honcho` in an interactive TTY prints a curated command/welcome panel. For scriptable help, use group-specific help such as `honcho peer --help` or `honcho doctor --help`.

## Global Scoping And Output Flags

Most command groups accept these options at top, group, or command level:

| Flag | Env var | Use |
| --- | --- | --- |
| `--json` | `HONCHO_JSON=1` or `true` | Force JSON output. Non-TTY stdout also emits JSON automatically. |
| `-w`, `--workspace` | `HONCHO_WORKSPACE_ID` | Workspace scope. Required for most resource commands. |
| `-p`, `--peer` | `HONCHO_PEER_ID` | Peer scope or peer filter, depending on command. |
| `-s`, `--session` | `HONCHO_SESSION_ID` | Session scope. |

Resolution order is flag, env var, config file, default. Workspace/peer/session are intentionally per-command only; they are not persisted by `honcho init` or `honcho config`.

## Onboarding, Health, And Config

| Command | Purpose | Notes |
| --- | --- | --- |
| `honcho init` | Configure host and credentials. | Writes CLI-owned top-level keys in the shared config file. Interactive TTY can use browser/device login when the server advertises the device grant; non-interactive or `--api-key` uses manual-key setup. |
| `honcho init --api-key <token> --base-url <url>` | Non-interactive setup. | Values may also come from `HONCHO_API_KEY` and `HONCHO_BASE_URL`. With `--json`, missing URL is a structured `MISSING_VALUE` error. |
| `honcho doctor --json` | Health checklist. | Checks config file, credentials, API connectivity, and—when scoped—workspace reachability, queue health, and peer existence. Critical failures exit non-zero. |
| `honcho config --json` | Show effective config. | Redacts `api_key` and OAuth token; useful before debugging scope/auth precedence. |

## Workspace Commands

| Command | Purpose | Key flags/output |
| --- | --- | --- |
| `honcho workspace list --json` | List accessible workspaces. | Does not require workspace scope; returns array of `{id}`. |
| `honcho workspace create <id> --metadata '{...}' --json` | Create or get a workspace. | Metadata must be valid JSON. |
| `honcho workspace inspect [id] -w <workspace> --json` | Inspect a workspace. | Returns metadata, configuration, peer/session counts, and first page of peers/sessions. Positional ID overrides scope for inspection. |
| `honcho workspace search <query> -w <workspace> --limit N --json` | Search messages across workspace. | JSON preserves full content; human output truncates long content for display. |
| `honcho workspace queue-status -w <workspace> [-s <session>] [--observer <peer>] [--sender <peer>] --json` | Inspect deriver queue status. | Useful after message ingestion or when conclusions are delayed. |
| `honcho workspace delete <id> --dry-run --json` | Preview destructive workspace deletion. | Returns sessions to delete. Use before cascade deletion. |
| `honcho workspace delete <id> --cascade --yes --json` | Delete workspace and sessions. | Use only after preview/approval. Without `--yes`, prompts interactively. |

## Peer Commands

| Command | Purpose | Key flags/output |
| --- | --- | --- |
| `honcho peer list -w <workspace> --json` | List peers in a workspace. | Returns metadata/configuration and creation time. |
| `honcho peer create <peer> -w <workspace> [--observe-me/--no-observe-me] [--metadata '{...}'] --json` | Create or get a peer. | Echoes metadata/config only when caller supplied them. |
| `honcho peer inspect [peer] -w <workspace> --json` | Peer dashboard. | Returns card, peer configuration, session count, conclusion count, recent conclusions, and recent sessions. |
| `honcho peer card [peer] -w <workspace> [--target <peer>] --json` | Raw peer card. | Use before Dialectic debugging. |
| `honcho peer representation [peer] -w <workspace> [-s <session>] [--target <peer>] [--search-query <q>] [--max-conclusions N] --json` | Formatted representation. | Session scope returns session-conditioned representation. |
| `honcho peer chat "<query>" -w <workspace> -p <peer> [--target <peer>] [--reasoning minimal|low|medium|high|max] [-s <session>] --json` | Query the Dialectic about a peer. | Invalid reasoning level emits `INVALID_REASONING`. |
| `honcho peer search "<query>" -w <workspace> -p <peer> --limit N --json` | Search a peer's messages. | Peer comes from `-p` or env var. |
| `honcho peer get-metadata [peer] -w <workspace> --json` | Read peer metadata. | Peer can be positional or scoped. |
| `honcho peer set-metadata '{...}' -w <workspace> -p <peer> --json` | Replace peer metadata. | Metadata argument must be valid JSON. |

Peer commands that need a peer emit `NO_PEER` when only workspace is scoped, or `NO_SCOPE` when both workspace and peer are absent.

## Session Commands

| Command | Purpose | Key flags/output |
| --- | --- | --- |
| `honcho session list -w <workspace> [--peer <peer>] --json` | List sessions in a workspace, optionally for one peer. | Returns IDs, active state, metadata, creation time. |
| `honcho session create <session> -w <workspace> [--peers a,b] [--metadata '{...}'] --json` | Create/get session and optionally add peers. | Validates session and peer IDs before API call. |
| `honcho session inspect [session] -w <workspace> --json` | Session dashboard. | Returns peers, message count, summaries, configuration. |
| `honcho session view [session] -w <workspace> [--last N | --page N --size M | --all] [--reverse] [--ids] [-p <peer>] --json` | Transcript view. | Default tail is most recent 50 messages, oldest-at-top. `--page` is 1-indexed. `--size` requires `--page` and must be 1-100. `--last`, `--page`, and `--all` are mutually exclusive. |
| `honcho session context [session] -w <workspace> [--tokens N] [--summary/--no-summary] --json` | Agent-visible session context. | Use to debug what the agent would receive. |
| `honcho session summaries [session] -w <workspace> --json` | Short and long summaries. | Use when context seems stale or incomplete. |
| `honcho session peers [session] -w <workspace> --json` | List session peers. | Simple array of peer IDs. |
| `honcho session add-peers <session> <peer...> -w <workspace> --json` | Add peers. | Peer IDs are positional after session ID. |
| `honcho session remove-peers <session> <peer...> -w <workspace> --json` | Remove peers. | Mutating command. |
| `honcho session search "<query>" [session] -w <workspace> --limit N --json` | Search messages in a session. | JSON preserves full content. |
| `honcho session representation <peer> [session] -w <workspace> [--target <peer>] [--search-query <q>] [--max-conclusions N] --json` | Session-scoped representation. | Distinguish observer peer from optional target. |
| `honcho session get-metadata [session] -w <workspace> --json` | Read metadata. | Session can be positional or scoped. |
| `honcho session set-metadata [session] --data '{...}' -w <workspace> --json` | Replace metadata. | `--data`/`-d` is required and must be JSON. |
| `honcho session delete [session] -w <workspace> --yes --json` | Delete session and related data. | Without `--yes`, interactive confirm; human mode previews peers/message count when possible. |

Transcript specifics:

- `session view --last N` fetches newest-first pages until it has N messages, then reverses to chronological order unless `--reverse` is given.
- `session view --page N --reverse` pages from the newest end and preserves server order.
- Human transcript output preserves newlines, markup-like tags, literal Rich markup, full IDs with `--ids`, and millisecond UTC timestamps.
- When a page has more pages, human mode prints a shell-quoted `more:` continuation command that carries only flag-provided workspace/peer scope.

## Message Commands

| Command | Purpose | Key flags/output |
| --- | --- | --- |
| `honcho message list [session] -w <workspace> [--last N] [--reverse] [--brief] [-p <peer>] --json` | List recent messages. | Default `--last` is 20. `--last` must be >= 1. By default it displays the recent tail oldest-at-top; `--reverse` preserves newest-first server order. |
| `honcho message create "<content>" -w <workspace> -s <session> -p <peer> [--metadata '{...}'] --json` | Create one message. | Requires sender peer with `--peer/-p`; metadata must be JSON. |
| `honcho message get <message_id> -w <workspace> -s <session> --json` | Get one message. | Returns id, peer, content, token count, metadata, and created time. |

`message list` warns on stderr if identical message content appears with different IDs in the fetched window.

## Conclusion Commands

Conclusions are the API-facing memory atoms; many code symbols still call them observations. Observer is the peer whose memory collection is queried; observed is the target peer when using cross-peer memory.

| Command | Purpose | Key flags/output |
| --- | --- | --- |
| `honcho conclusion list -w <workspace> -p <observer> [--observer <peer>] [--observed <peer>] [--limit N] --json` | List conclusions. | `--observer` overrides scoped peer. Without observer, `-p` supplies it. |
| `honcho conclusion search "<query>" -w <workspace> -p <observer> [--observer <peer>] [--observed <peer>] [--top-k N] --json` | Semantic search over conclusions. | Use before `peer chat` when debugging recall. |
| `honcho conclusion create "<content>" -w <workspace> -p <observer> [--observer <peer>] [--observed <peer>] [-s <session>] --json` | Create a conclusion. | If content parses as JSON object, its `content` field becomes the conclusion body. Optional session ID adds context. |
| `honcho conclusion delete <id> -w <workspace> -p <observer> [--observed <peer>] --yes --json` | Delete a conclusion. | Without `--yes`, prompts with identifying fields. |

## Recommended Debugging Sequences

### Is memory formation delayed?

```bash
honcho doctor -w <workspace> -p <peer> --json
honcho workspace queue-status -w <workspace> --observer <peer> --json
honcho peer inspect <peer> -w <workspace> --json
honcho conclusion list -w <workspace> --observer <peer> --json
```

### Does the Dialectic have enough context?

```bash
honcho peer card <peer> -w <workspace> --json
honcho conclusion search "<topic>" -w <workspace> --observer <peer> --json
honcho session context <session> -w <workspace> --json
honcho peer chat "<question>" -w <workspace> -p <peer> -s <session> --reasoning medium --json
```

### Is the transcript correct?

```bash
honcho session view <session> -w <workspace> --last 100 --ids --json
honcho message get <message_id> -w <workspace> -s <session> --json
honcho session summaries <session> -w <workspace> --json
```
