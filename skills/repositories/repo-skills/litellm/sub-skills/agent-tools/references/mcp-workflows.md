# MCP Workflows

LiteLLM can act as an MCP gateway in front of HTTP, SSE, and stdio MCP servers. Use it when a single proxy key should control MCP discovery, tool calls, upstream auth headers, tool permissions, logging, and model-provider routing.

## Configuration shape

Define MCP servers in proxy config under `mcp_servers`. A server entry commonly uses these fields:

```yaml
mcp_servers:
  github:
    url: https://api.example.invalid/mcp
    transport: http
    auth_type: authorization
    alias: github
    server_name: github
    allowed_tools: [search_repositories, get_issue]
    extra_headers: [Authorization]
```

Important fields:

- `transport`: `http`, `sse`, or `stdio`.
- `url`: required for HTTP/SSE servers; stdio uses `command`, `args`, and optional `env`.
- `auth_type`: `none`, `api_key`, `bearer_token`, `basic`, `authorization`, `oauth2`, `aws_sigv4`, `token`, or `oauth2_token_exchange`.
- `alias` and `server_name`: stable labels used by paths, `x-mcp-servers`, and server-specific auth headers.
- `allowed_tools` / `disallowed_tools`: server-level tool filtering before tools are exposed to clients.
- `allowed_params`: per-tool argument allowlists for tighter tool-call control.
- `static_headers` and `extra_headers`: admin-controlled fixed headers and caller-forwarded header names.
- `oauth2_flow: client_credentials`: opt-in for machine-to-machine OAuth2. Client id/secret alone does not imply client credentials flow.
- `delegate_auth_to_upstream`: for OAuth2 servers where the upstream server, not LiteLLM, should complete auth.
- `oauth_passthrough`: for non-oauth2 servers that explicitly pass client `Authorization` upstream and should preserve upstream OAuth discovery/401 behavior.
- `is_byok`: require each user to provide stored credentials for that MCP server.

The MCP optional dependency is part of the proxy extra. If imports fail for `mcp`, install a LiteLLM distribution with proxy MCP extras before using these workflows.

## Connecting MCP clients

The proxy exposes streamable MCP endpoints. Use these patterns:

- All allowed servers: `http://localhost:4000/mcp`.
- Header-scoped servers: `http://localhost:4000/mcp` plus `x-mcp-servers: github,docs`.
- Path-scoped server: `http://localhost:4000/mcp/github` or `http://localhost:4000/github/mcp` depending on the MCP client URL shape.

Always include the LiteLLM proxy key in `Authorization: Bearer <litellm-key>` unless the route is intentionally public. For scoped access, the value in `x-mcp-servers` must match a known server name, alias, or access-group-derived server.

A Python MCP SDK smoke test looks like this:

```python
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async with streamablehttp_client(
    url="http://localhost:4000/mcp",
    headers={"Authorization": "Bearer <litellm-key>", "x-mcp-servers": "github"},
) as (read, write, _):
    async with ClientSession(read, write) as session:
        await session.initialize()
        tools = await session.list_tools()
```

## Auth header precedence

LiteLLM supports both configured MCP auth and caller-supplied upstream auth. The practical precedence is:

1. Server-specific request headers such as `x-mcp-github-authorization` or `x-mcp-zapier-x-api-key`.
2. Legacy broad `x-mcp-auth` when no server-specific header matches.
3. OAuth per-user or BYOK credentials from LiteLLM storage when that server requires them.
4. Configured `auth_value` / `authentication_token` for the server.

Server-specific header matching is case-insensitive. If a server has both `alias` and `server_name`, LiteLLM checks the alias first, then server name. For `auth_type: authorization`, send the complete Authorization value in the server-specific header, such as `Bearer upstream-token` or `Token custom-token`. For `auth_type: bearer_token`, configured tokens are rendered as `Authorization: Bearer <token>`. For `auth_type: api_key`, LiteLLM renders `X-API-Key: <value>`.

## OAuth and BYOK patterns

Use the narrowest OAuth mode that matches the upstream server:

- Interactive per-user OAuth: `auth_type: oauth2` with authorization/token metadata and no `oauth2_flow: client_credentials`. LiteLLM stores and caches user credentials; stale cache can cause a user to keep failing until the stored credential is refreshed.
- Client credentials OAuth: `auth_type: oauth2`, `oauth2_flow: client_credentials`, and client credential fields. This is shared machine-to-machine auth.
- OAuth token exchange: `auth_type: oauth2_token_exchange` with `token_exchange_endpoint` or `token_url`, `audience`, and client credentials.
- Upstream-delegated OAuth2: `delegate_auth_to_upstream: true` only for `auth_type: oauth2` servers that should manage the client flow themselves.
- OAuth pass-through: `auth_type: none`, `extra_headers: [Authorization]`, and `oauth_passthrough: true` when the upstream server owns OAuth discovery and challenge semantics.
- BYOK: `is_byok: true` when each LiteLLM user must bring a credential. Missing BYOK credentials produce an auth challenge rather than silently calling upstream.

Do not place private tokens in public skill content or examples. Use environment references such as `os.environ/GITHUB_TOKEN` in configs.

## Tool discovery and naming

When multiple servers expose tools, LiteLLM namespaces tool names by server label, such as `math_stdio-add` and `math_streamable_http-add`. If only one server is scoped, the client may see unprefixed tool names depending on the route and server configuration. Display names and descriptions can be overridden with `tool_name_to_display_name` and `tool_name_to_description`.

Use `scripts/inspect_mcp_tools.py` to validate saved tool JSON before wiring a client:

```bash
python sub-skills/agent-tools/scripts/inspect_mcp_tools.py tools.json
python sub-skills/agent-tools/scripts/inspect_mcp_tools.py server.json --format mcp-server
```

The script does not connect to external servers. It validates shape only.

## Permissions and filters

LiteLLM applies several layers of MCP control:

- Server exposure: key/team `object_permission.mcp_servers` and `mcp_access_groups` restrict which MCP servers a caller can see.
- Tool exposure: `mcp_tool_permissions` maps server ids to allowed tool names; toolsets can resolve to server/tool permissions.
- Server-level controls: `allowed_tools`, `disallowed_tools`, and `allowed_params` filter available tools and arguments.
- Tool permission guardrail: the `tool_permission` guardrail can allow or deny tool names such as `Bash`, `Read`, or `mcp__github_*` after model output.
- Semantic MCP filter: the `mcp_semantic_filter` hook can reduce visible MCP tools based on semantic relevance, but it needs model/embedding configuration and can hide tools unexpectedly if configured too aggressively.

A guardrail example:

```yaml
guardrails:
  - guardrail_name: tool-permission-guardrail
    litellm_params:
      guardrail: tool_permission
      mode: post_call
      default_on: true
      rules:
        - id: allow_github_mcp
          tool_name: mcp__github_*
          decision: allow
      default_action: deny
      on_disallowed_action: block
```

## Agent and coding-tool clients

Claude Agent SDK can use LiteLLM-hosted MCP by setting an MCP server URL such as `http://localhost:4000/mcp/deepwiki2` and passing proxy auth headers. Claude Code and Cursor need the base URL for their LLM gateway plus any separate MCP server URL the client expects. Keep these separate: the LLM gateway URL is usually an Anthropic/OpenAI-compatible proxy route, while MCP traffic goes to `/mcp` or a scoped MCP path.

## Validation checklist

- Run the proxy with a config containing `mcp_servers` and a master key.
- Connect with an MCP client and call `initialize` then `list_tools`.
- Confirm tool names and prefixes match the intended server scope.
- Send server-specific auth headers when upstream auth differs by server.
- Use proxy logs to confirm `x-mcp-servers`, selected server, and auth mode.
- If OAuth is involved, test a fresh user or cleared credential cache to distinguish bad config from stale stored credentials.
