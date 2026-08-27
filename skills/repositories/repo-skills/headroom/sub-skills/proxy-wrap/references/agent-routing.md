# Agent routing map

Use this reference when the user names a coding agent, editor, or provider and asks how to route it through Headroom.

## Claude Code

- Foreground route: `ANTHROPIC_BASE_URL=http://127.0.0.1:8787 claude`
- Durable route: `headroom wrap claude`
- Important bypass warning: if Claude Code is configured in its own Bedrock mode, it can ignore `ANTHROPIC_BASE_URL`. The proxy only sees traffic when Claude runs in normal Anthropic mode.

## Codex

- Foreground route: `headroom wrap codex`
- Durable route: `headroom init codex` or equivalent durable setup for the target profile
- The wrapper must preserve the correct auth or backend path based on whether the user is using ChatGPT auth or API-key-style access.

## GitHub Copilot

- Foreground route: `headroom wrap copilot`
- VS Code route: `headroom wrap vscode` or `headroom wrap vscode-claude`
- Durable setup may write user-level settings or proxy URLs depending on the target.
- Subscription workflows need special handling because the client may carry OAuth or subscription tokens rather than a standard API key.

## OpenClaw

- Route: `headroom wrap openclaw`
- The plugin install path and launcher discovery can vary by local npm bin, global npm, PATH, or Python fallback.
- Use the plugin when the user wants in-process routing inside OpenClaw, not just a shell wrapper.

## OpenCode

- Route: `headroom wrap opencode`
- The wrapper can inject provider config and MCP entries.
- If the user already has a running proxy, wrapping may only need configuration injection rather than launching a new proxy.

## Grok / Kimi / Vibe / Continue / Cline / Goose / OpenHands / Cursor

These wrappers are mostly about launching with the right proxy base URL, provider env, or config file:

- `grok` and `grok-build` may write Grok-specific config or model registry data.
- `kimi`, `vibe`, `goose`, and `openhands` generally need a running proxy plus a launcher env.
- `cline` and `continue` usually require editor-specific config updates.
- `cursor` is often instructions-only rather than a durable write.
- `cursor`, `grok-build`, `openclaw`, and `opencode` should be routed carefully if the user asks for a permanent change versus a one-off shell session.

## How to choose between this sub-skill and `ops`

- If the user is asking how to make an agent talk through Headroom, use this sub-skill.
- If the user is asking how to install or update Headroom itself, use `ops`.
- If the user is asking about memory or learning after the agent is already routed, use `memory`.
