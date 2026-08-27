# MCP Server Contracts

## `llm-chat`

- Tool name: `chat`.
- Required input: prompt; optional system and model fields.
- Environment: `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`, `LLM_FALLBACK_MODEL`, optional server name.
- Behavior: sends an OpenAI-compatible request, returns clear missing-key or malformed-response errors, and can retry/fallback on gateway timeout.
- Verification: mocked request tests are sufficient for schema and retry behavior; they do not verify the remote endpoint.

## `minimax-chat`

- Tool name: `minimax_chat`.
- Environment: `MINIMAX_API_KEY`, optional `MINIMAX_BASE_URL`, `MINIMAX_MODEL`.
- Behavior: exposes supported MiniMax model choices and clamps temperature into the provider's accepted range.
- Verification: use mocked tests for JSON-RPC, missing key, temperature, and API errors.

## `manual-review`

- Tool calls block until a reviewer submits a response through a local browser or file workflow.
- Environment includes mode, timeout, auto-open, pending directory, debug log, and port controls.
- A pending review state includes a URL/token or file handoff. Preserve it for recovery and do not expose it in public reports.

## Claude/Gemini Review Bridges

- Claude review invokes a Claude CLI backend with configurable binary, model, system prompt, tools, timeout, and debug log.
- Gemini review supports API or CLI/AGY-style backend selection with model, timeout, workspace, and debug settings.
- Register the selected server in Codex CLI, verify the binary/API first, and restart Codex after changes.

## Feishu/Lark Bridge

- Requires `lark-oapi` plus app id, app secret, user id, and an optional bridge port.
- Pure logic includes reply registration/polling, card payloads, query parsing, and HTTP route handling.
- Keep it optional and unverified unless the user supplies the package and credentials.

## General MCP Checks

1. Confirm server process command and environment variables.
2. Confirm JSON-RPC initialize and tools/list work locally.
3. Call a harmless test tool or use a mocked request before a real review.
4. Check host logs for protocol-version negotiation or timeout errors.
5. Restart the host after registration changes.
