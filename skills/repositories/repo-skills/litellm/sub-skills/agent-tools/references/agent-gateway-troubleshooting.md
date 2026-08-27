# Agent Gateway Troubleshooting

Use this guide when MCP tools, A2A agents, Claude Code, Cursor, or agent SDK clients fail through LiteLLM.

## Optional dependency failures

Symptoms:

- Import errors for `mcp`, `mcp.client.streamable_http`, or `mcp.types`.
- Import errors for `a2a` or `a2a.types`.
- Proxy starts, but MCP or A2A routes fail only when exercised.

Fix:

- Install LiteLLM with proxy MCP support before using MCP gateway features.
- Install `a2a-sdk` before running direct A2A client examples.
- Keep basic LiteLLM routing independent from these extras; only MCP/A2A workflows need them.

## MCP server URL or label mismatch

Symptoms:

- `list_tools` returns no tools or tools from the wrong server.
- Server-scoped path returns not found.
- Upstream auth header seems ignored.

Checks:

- Match `alias`, `server_name`, `x-mcp-servers`, and path segment exactly in intent. Header matching is case-insensitive, but humans should still keep one canonical lowercase label.
- For server-specific auth, use `x-mcp-<alias>-authorization` when an alias exists; LiteLLM checks alias before server name.
- For scoped paths, try both common shapes if a client is opinionated: `/mcp/<server>` and `/<server>/mcp`.
- If multiple servers are visible, call namespaced tools such as `<server>-<tool>` unless the route scopes to one server.

## MCP auth precedence surprises

Symptoms:

- The proxy sends a stale configured token even though the client sent a header.
- The wrong server receives a shared legacy header.
- OAuth users keep seeing 401 after reauth.

Resolution order:

1. Server-specific request header, for example `x-mcp-github-authorization`.
2. Legacy `x-mcp-auth` if no server-specific header matched.
3. Stored per-user OAuth or BYOK credential when required.
4. Configured `auth_value` / `authentication_token`.

Troubleshooting actions:

- Prefer server-specific headers when two MCP servers need different upstream credentials.
- For `auth_type: authorization`, include the full header value, such as `Bearer token`.
- For OAuth, test with a fresh user or clear/update the stored credential to rule out cached per-user tokens.
- For client-credentials OAuth, ensure `oauth2_flow: client_credentials` is explicitly set.
- For upstream-delegated OAuth, use `delegate_auth_to_upstream` only with `auth_type: oauth2`.
- For OAuth pass-through, require all three settings: `auth_type: none`, `extra_headers: [Authorization]`, and `oauth_passthrough: true`.

## Tool approval and policy blocks

Symptoms:

- The model emits a tool call but LiteLLM blocks it.
- Claude Code reports a tool approval/policy failure.
- MCP tools disappear after enabling filters.

Checks:

- Inspect `tool_permission` guardrail rules. Match exact tool names and wildcard patterns. MCP tool names in client UIs may include prefixes like `mcp__github_*`.
- Inspect server `allowed_tools`, `disallowed_tools`, `allowed_params`, and key/team `mcp_tool_permissions`.
- Temporarily disable `mcp_semantic_filter` or broaden its threshold/config to determine whether semantic filtering hid the required tool.
- Check whether the client requires local approval for tool execution in addition to LiteLLM proxy approval.

## Claude Code base URL confusion

Symptoms:

- Claude Code connects but asks for a model LiteLLM does not know.
- Claude Code can call the LLM but MCP tools do not appear.
- Requests hit `/v1/messages` or Anthropic-compatible routes but MCP client traffic never reaches `/mcp`.

Fix:

- Configure Claude Code's LLM gateway base URL separately from MCP server URLs.
- Ensure LiteLLM `model_name` entries include exactly what Claude Code requests. Claude Code can cache model selections; explicitly pass a model if environment defaults do not take effect.
- For extended context model suffixes, check proxy logs for the model string that actually reached LiteLLM.
- For MCP, add a separate MCP server URL pointing at `http://localhost:4000/mcp/<server>` or `http://localhost:4000/mcp` plus the required headers.
- Use the same LiteLLM key in the client auth setting that the proxy route expects.

## Cursor gateway confusion

Symptoms:

- Cursor works with OpenAI-compatible chat but MCP tools fail.
- Cursor sends requests to the LLM base URL when the intended target was MCP.
- Cursor reports unauthorized even though the LiteLLM key works with curl.

Fix:

- Use the OpenAI-compatible LiteLLM base URL for Cursor model traffic and a separate MCP server config for MCP traffic.
- Keep `Authorization: Bearer <litellm-key>` for LiteLLM proxy auth, then add server-specific `x-mcp-<server>-authorization` only for upstream MCP server auth.
- Verify whether Cursor expects `/v1` in the LLM base URL. MCP URLs should not be rewritten to `/v1`.

## A2A `a2a/<agent-name>` access denied

Symptoms:

- `model: a2a/research-agent` returns HTTP 403.
- Admin keys work, non-admin keys fail.
- `/v1/agents` does not show the agent for the same key.

Fix:

- Check key object permissions, team object permissions, and access groups. If both key and team restrict agents, the effective set is the intersection.
- Confirm permissions list the agent id expected by LiteLLM, not only the display name from the agent card.
- If the caller should inherit team access, remove conflicting key-level restrictions or include the agent in both places.
- If no restrictions are intended, verify the key's object permission table is empty for agents rather than populated with an unrelated list.

## A2A request shape failures

Symptoms:

- Direct `/a2a/{agent_id}` returns JSON-RPC errors.
- Streaming returns no chunks.
- Push notification setup fails.

Fix:

- Use `message/send` for non-streaming and a streaming A2A method for SSE clients.
- Include `jsonrpc`, `id`, `method`, and `params.message` with `role`, `parts`, and `messageId`.
- Set `Accept: text/event-stream` for streaming.
- Push notification URLs must be HTTPS.
- If an agent requires trace ids, include a LiteLLM-recognized trace id header or request field.

## Web search and code interpreter interception

LiteLLM can intercept provider-native tool requests for web search or code interpreter and route them through configured proxy tools. Typical configs define `search_tools` or `sandbox_tools`, then enable callbacks such as `websearch_interception` or `code_interpreter_interception` under `litellm_settings`.

Troubleshooting actions:

- Confirm `enabled_providers` matches the provider prefix actually used by the routed model.
- Confirm `search_tool_name` or `sandbox_tool_name` matches the configured tool entry.
- Confirm required provider credentials are present in the runtime environment, not hardcoded in config.
- Check that the target model supports the tool style the client is requesting.

## Safe reproduction sequence

1. Validate static JSON with `scripts/inspect_mcp_tools.py` if tool metadata is available.
2. Curl `GET /v1/agents` or connect to `/mcp` with `initialize` and `list_tools` using the same key as the failing client.
3. Add one upstream auth mechanism at a time: configured token, then server-specific request header, then OAuth/BYOK.
4. Re-enable filters and guardrails after the raw connection succeeds.
5. Compare proxy logs against the client configuration for exact model name, MCP server label, A2A agent name, and route path.
