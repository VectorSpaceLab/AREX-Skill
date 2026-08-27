# Mem0 CLI Configuration

The Mem0 CLI uses local config plus environment and per-command flags to authenticate against the hosted Mem0 Platform API and choose default entity scopes.

## Config Location

| Path | Permission intent | Purpose |
| --- | --- | --- |
| `~/.mem0/` | owner-only directory (`0700`) | Stores CLI state/config. |
| `~/.mem0/config.json` | owner read/write (`0600`) | Stores API key, base URL, defaults, telemetry ID, and Agent Mode metadata. |

Do not commit this file and do not paste it into chat. Use `mem0 config show` because it redacts keys.

## Current Config Shape

The checked Python and Node implementations share this logical schema:

```json
{
  "version": 1,
  "defaults": {
    "user_id": "",
    "agent_id": "",
    "app_id": "",
    "run_id": ""
  },
  "platform": {
    "api_key": "",
    "base_url": "https://api.mem0.ai",
    "user_email": "",
    "agent_mode": false,
    "created_via": "",
    "agent_caller": "",
    "claimed_at": "",
    "default_user_id": ""
  },
  "telemetry": {
    "anonymous_id": ""
  },
  "agent_rush": {
    "acknowledged_at": ""
  }
}
```

The CLI spec also declares `defaults.enable_graph` and `MEM0_ENABLE_GRAPH`, while live command/config handlers may lag behind that spec. Treat graph defaults as version-sensitive and check `mem0 help --json`, `mem0 config show --output json`, and `mem0 <command> --help` on the installed CLI before automating graph toggles.

## Precedence

Configuration values resolve in this order:

1. CLI flags such as `--api-key`, `--base-url`, `--user-id`, `--agent-id`, `--app-id`, `--run-id`.
2. Environment variables such as `MEM0_API_KEY` and `MEM0_USER_ID`.
3. `~/.mem0/config.json`.
4. Built-in defaults, including default base URL `https://api.mem0.ai`.

Example: if config has `defaults.user_id = "bob"`, the shell has `MEM0_USER_ID=charlie`, and the command passes `--user-id alice`, the effective user is `alice`.

## Environment Variables

| Variable | Config path | Purpose |
| --- | --- | --- |
| `MEM0_API_KEY` | `platform.api_key` | Hosted Platform API key. Overrides stored key. |
| `MEM0_BASE_URL` | `platform.base_url` | Hosted/custom API base URL. |
| `MEM0_USER_ID` | `defaults.user_id` | Default user scope when no explicit scope flags are passed. |
| `MEM0_AGENT_ID` | `defaults.agent_id` | Default agent scope. |
| `MEM0_APP_ID` | `defaults.app_id` | Default app scope. |
| `MEM0_RUN_ID` | `defaults.run_id` | Default run scope. |
| `MEM0_ENABLE_GRAPH` | Spec-level default graph toggle | Declared in CLI spec/docs; confirm installed implementation support before relying on it. |

Safe shell setup:

```bash
export MEM0_API_KEY="m0-..."
export MEM0_USER_ID="alice"
mem0 status --output json
```

Avoid inline secrets such as `mem0 add ... --api-key m0-...` in shared shell history. Use env vars or config for routine use.

## Scope Resolution

Scope flags are not merged one-by-one with defaults. Instead:

- If no explicit scope flags appear, the CLI applies all configured defaults that are set.
- If any explicit scope flag appears, the CLI uses only explicit IDs and treats omitted scope IDs as unset.

This prevents accidental over-filtering when a default `agent_id` or `run_id` exists.

Examples:

```bash
# Uses configured defaults for user/agent/app/run.
mem0 search "preferences"

# Uses only user_id=alice; does not also include configured agent_id/run_id.
mem0 search "preferences" --user-id alice

# Uses user_id=alice and agent_id=support-bot only.
mem0 list --user-id alice --agent-id support-bot
```

Debugging tip: use agent mode and inspect the `scope` field:

```bash
mem0 --agent search "preferences" --user-id alice
```

## `mem0 init` Flows

### Interactive Human Setup

```bash
mem0 init
```

Prompts for API key and default user ID, validates the key, then writes config.

### Non-interactive API Key Setup

```bash
mem0 init --api-key "$MEM0_API_KEY" --user-id alice --force
```

Use this for CI or scripted setup. `--force` avoids overwrite prompts when a config file already exists.

### Email Code Login

```bash
mem0 init --email alice@example.com
mem0 init --email alice@example.com --code 482901
```

`--email` requests a code; adding `--code` makes the flow non-interactive.

### Agent Mode Bootstrap

```bash
mem0 init --agent --agent-caller codex --json
```

This starts unattended Agent Mode signup. The key is represented in config with Agent Mode metadata such as `platform.agent_mode`, `platform.created_via`, `platform.agent_caller`, and `platform.default_user_id`. If `--agent-caller` was omitted, run:

```bash
mem0 identify codex
```

After a human claims the account with email login, the existing API key should continue working and memories are preserved.

## Config Commands

```bash
mem0 config show
mem0 config show --output json
mem0 config get platform.api_key
mem0 config get defaults.user_id
mem0 config set defaults.user_id alice
mem0 config set platform.base_url https://api.mem0.ai
```

Supported key forms include dotted paths and short aliases.

| Short alias | Dotted path |
| --- | --- |
| `api_key` | `platform.api_key` |
| `base_url` | `platform.base_url` |
| `user_email` | `platform.user_email` |
| `user_id` | `defaults.user_id` |
| `agent_id` | `defaults.agent_id` |
| `app_id` | `defaults.app_id` |
| `run_id` | `defaults.run_id` |

Python and Node source both implement type coercion in `config set`: boolean-like fields accept `true`, `1`, and `yes`; integer fields parse as integers; strings store as given. Current public keys are mostly strings, so quote values normally in shell scripts.

## Redaction Rules

Displayed API keys are redacted:

| Key length | Display |
| --- | --- |
| empty | `(not set)` |
| `<= 8` | first 2 characters plus `***` |
| `> 8` | first 4 characters, `...`, last 4 characters |

`config show`, `config get platform.api_key`, and status-style displays must never reveal a full API key. If raw JSON from a different source contains secrets, redact before sharing.

## Base URL Guidance

Use default `https://api.mem0.ai` unless the user explicitly has a custom Platform endpoint. Self-hosted server/OpenMemory deployment issues belong in `../self-hosted-openmemory/SKILL.md`, not in CLI config docs, except that a CLI command can point at a compatible custom base URL with `--base-url` or `MEM0_BASE_URL`.

## Config And Plugin Sync Side Effects

When saving a config that contains an API key, the CLI best-effort syncs that key to existing ecosystem touchpoints, such as previously configured editor plugin environment injection or shell rc exports. The sync is intended to update existing entries and swallow errors; config file remains authoritative. Route plugin setup or hook behavior to `../integrations-plugins/SKILL.md`.

## Safe Automation Patterns

Use a temporary HOME when testing config behavior:

```bash
TMP_HOME="$(mktemp -d)"
HOME="$TMP_HOME" mem0 config show --output json
rm -rf "$TMP_HOME"
```

Use env vars for CI:

```bash
: "${MEM0_API_KEY:?set MEM0_API_KEY}"
mem0 init --api-key "$MEM0_API_KEY" --user-id ci-bot --force
mem0 --agent status
```

When diagnosing defaults, compare these in order:

```bash
mem0 config show --output json
env | grep '^MEM0_' | sed 's/=.*/=<redacted if secret>/'
mem0 --agent search "scope check" --user-id explicit-user
```

## Common Misconfiguration Signals

| Symptom | Likely cause | First check |
| --- | --- | --- |
| `No API key configured.` | No config key and no `MEM0_API_KEY`. | `mem0 config show`, then `echo "$MEM0_API_KEY"` without printing value in logs. |
| Auth failure after setting config | Expired/invalid key or env var overriding a good stored key. | Temporarily unset `MEM0_API_KEY` and rerun `mem0 status`. |
| Query ignores stored default user | A different explicit scope flag was passed. | Inspect agent-mode `scope`. |
| Command uses wrong API host | `MEM0_BASE_URL` or `--base-url` override. | `mem0 status --output json`. |
| Graph setting not honored | Spec/docs and installed command implementation differ. | `mem0 help --json` and `mem0 <command> --help`; route backend graph config to `provider-configuration`. |
