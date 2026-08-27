# Editor and Agent Plugins

Use this reference for Mem0 integrations with Claude Code/Cowork, Cursor, Codex, OpenCode, Antigravity, OpenClaw, and Pi Agent.

## Shared Concepts

Most editor/agent integrations expose a Mem0 memory layer through some combination of:

- Remote MCP server at `https://mcp.mem0.ai/mcp` with 9 tools: `add_memory`, `search_memories`, `get_memories`, `get_memory`, `update_memory`, `delete_memory`, `delete_all_memories`, `delete_entities`, and `list_entities`.
- Full plugin install with skills/slash commands and lifecycle hooks.
- `MEM0_API_KEY` from the Mem0 Platform, usually an API key beginning with `m0-`.
- Project/user/session scope based on `user_id`, `app_id`, and `run_id` metadata.

MCP-only setup gives memory tools. Full plugin setup adds lifecycle hooks, slash commands/skills, onboarding, and automatic capture/retrieval where the host supports it.

## Claude Code and Claude Cowork

Full plugin path:

```text
/plugin marketplace add mem0ai/mem0
/plugin install mem0@mem0-plugins
```

MCP-only path:

```json
{
  "mcpServers": {
    "mem0": {
      "type": "http",
      "url": "https://mcp.mem0.ai/mcp/",
      "headers": { "Authorization": "Token ${MEM0_API_KEY}" }
    }
  }
}
```

After full plugin install, run `/mem0:onboard` to verify the key/MCP connection, import project context files where appropriate, install coding categories, and show identity/project scope. Claude hooks include session start, user prompt, pre-tool, post-tool, and pre-compact handling.

## Cursor

MCP-only options include one-click deeplink, `npx mcp-add`, or manual `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "mem0": {
      "url": "https://mcp.mem0.ai/mcp/",
      "headers": { "Authorization": "Token ${env:MEM0_API_KEY}" }
    }
  }
}
```

Full Cursor Marketplace install adds lifecycle hooks, the Mem0 SDK skill, and automatic memory capture. Remove any existing manual `mem0` MCP entry before installing the marketplace plugin to avoid duplicate tools.

## Codex

Direct MCP uses TOML, because the Codex CLI MCP add helper supports stdio servers rather than HTTP servers:

```toml
[mcp_servers.mem0]
url = "https://mcp.mem0.ai/mcp"
bearer_token_env_var = "MEM0_API_KEY"
```

Full plugin path registers MCP from the plugin manifest and includes skills/hooks metadata. Do not combine a full plugin install with a manual `[mcp_servers.mem0]` block; that creates duplicate registrations.

Codex lifecycle hooks are opt-in in current plugin workflows. The source installer rewrites hook commands with absolute plugin paths and merges entries into the user hooks file; because that mutates user config, this generated skill does not bundle it. Validate config first with `scripts/validate_mcp_config.py`, then only edit hook config with user approval.

Codex hooks require a feature flag:

```toml
[features]
codex_hooks = true
```

## OpenCode

Recommended plugin install:

```bash
opencode plugin @mem0/opencode-plugin
```

The OpenCode plugin registers native SDK-backed memory tools, hooks, and skills through OpenCode’s plugin hooks; it does not require an MCP server for the full install path. Standalone MCP is still possible in `opencode.json`:

```json
{
  "mcp": {
    "mem0": {
      "type": "remote",
      "url": "https://mcp.mem0.ai/mcp/",
      "headers": { "Authorization": "Token {env:MEM0_API_KEY}" },
      "oauth": false
    }
  }
}
```

OpenCode memory scopes are project, session, and global. Project scope is the default and derives `app_id` from git remote or repository root. Global deletes require explicit global scope; do not infer global deletes from default scope changes.

## Antigravity

Recommended install copies the plugin into Antigravity’s plugin directory:

```bash
npx degit mem0ai/mem0/integrations/mem0-plugin ~/.gemini/config/plugins/mem0
```

The plugin includes MCP config, hooks, scripts, and slash commands. Hook commands use the host plugin-root token rather than fixed local paths. If MCP auth fails because environment interpolation is unsupported in a specific Antigravity build, configure the token through the host’s supported secret mechanism; avoid pasting secrets into shared files.

## Plugin Slash Commands and Skills

The full Mem0 editor plugin includes commands such as:

- `/mem0:onboard` for setup and identity verification.
- `/mem0:health` for connectivity, API key, and read/write checks.
- `/mem0:remember`, `/mem0:peek`, `/mem0:tour`, `/mem0:stats`, `/mem0:dream`, `/mem0:pin`, `/mem0:forget`, `/mem0:export`, `/mem0:import`, `/mem0:list-projects`, `/mem0:switch-project`, `/mem0:memory-reviewer`, and `/mem0:context-loader`.

Treat destructive commands (`forget`, delete-all style tool calls, entity deletion) as requiring explicit confirmation and precise scope.

## Lifecycle Hooks

Observed hook responsibilities across editor plugins:

- Session start: load prior memories and show status.
- User prompt: search relevant memories before the turn.
- Pre-tool: block writes to `MEMORY.md` and enforce metadata defaults on Mem0 tool calls.
- Post-tool: track memory tool stats and use bash errors as search triggers.
- Pre-compact/compaction: preserve a session summary before context compaction.
- Stop/end: summarize and capture session learnings.

Hooks are intentionally side-effectful. Use plugin-supported install/update/uninstall flows and restart the host after changes.

## OpenClaw Plugin

Package facts:

- Package: `@mem0/openclaw-mem0` version `1.0.13`.
- Requires OpenClaw `>= 2026.4.25` for full support.
- Uses `mem0ai` TypeScript SDK dependency `3.0.7` in the package.
- OpenClaw memory plugins load through an exclusive `plugins.slots.memory` slot; install alone does not activate the plugin.

Platform config pattern:

```json5
{
  "plugins": {
    "slots": { "memory": "openclaw-mem0" },
    "entries": {
      "openclaw-mem0": {
        "enabled": true,
        "config": {
          "apiKey": "${MEM0_API_KEY}",
          "userId": "alice",
          "skills": {
            "triage": { "enabled": true },
            "recall": { "enabled": true, "tokenBudget": 1500, "rerank": true, "keywordSearch": true },
            "dream": { "enabled": true },
            "domain": "companion"
          }
        }
      }
    }
  }
}
```

Open-source mode is available through `openclaw mem0 init --mode open-source`; provider and vector-store details route to `../provider-configuration/SKILL.md` unless the task is specifically OpenClaw CLI setup. OpenClaw exposes eight tools such as `memory_search`, `memory_add`, `memory_get`, `memory_list`, `memory_update`, `memory_delete`, `memory_event_list`, and `memory_event_status`.

## Pi Agent Plugin

Package facts:

- Package: `@mem0/pi-agent-plugin` version `0.1.2`.
- Install: `pi install npm:@mem0/pi-agent-plugin`.
- Depends on `mem0ai` TypeScript SDK `^3.0.7` and Pi peer packages.
- Provides automatic capture, semantic search, project/session/global scoping, monorepo-aware git-root project detection, dream consolidation, eight slash commands, eight skills, and an agent tool.

Optional config file shape:

```json
{
  "apiKey": "m0-your-key-here",
  "userId": "your-username",
  "autoCapture": true,
  "defaultScope": "project",
  "searchThreshold": 0.3,
  "dream": { "enabled": true, "auto": true, "minHours": 24, "minSessions": 5, "minMemories": 20 }
}
```

Environment variables `MEM0_API_KEY` and `MEM0_USER_ID` override config-file values. The `mem0_memory` tool supports `search`, `add`, `get_all`, `delete`, and `delete_all`, with optional `scope` (`project`, `session`, or `global`).

Pi slash commands include `/mem0-remember`, `/mem0-forget`, `/mem0-search`, `/mem0-tour`, `/mem0-dream`, `/mem0-pin`, `/mem0-scope`, and `/mem0-status`.

## Config Validation

Run the bundled read-only validator on MCP/plugin config files before changing them:

```bash
python scripts/validate_mcp_config.py --kind auto ~/.codex/config.toml .cursor/mcp.json .mcp.json opencode.json
```

It reports Mem0 server entries, likely duplicate registrations, remote MCP URL mismatches, auth/header shape, Codex hook feature flag hints, and secret-looking literal tokens without printing token values.
