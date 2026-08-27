---
name: agent-tools
description: "Use when configuring LiteLLM for MCP tools, A2A agents, Claude
  Code/Cursor agent gateway traffic, MCP auth/OAuth, tool permissions, semantic
  filtering, or agent-specific proxy routes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Agent Tools

Use this sub-skill for LiteLLM workflows that expose tools or agents through the proxy. Route generic proxy setup to `../proxy-server/SKILL.md`, provider endpoint details to `../providers-and-endpoints/SKILL.md`, and SDK-only `tools` or `tool_choice` completion parameters to `../sdk-core/SKILL.md`.

## Choose the workflow

- MCP gateway for tools: configure `mcp_servers`, start the proxy, connect MCP-aware clients to `/mcp` or a scoped `/mcp/{server}` / `/{server}/mcp` endpoint, then validate tool discovery and auth headers with `references/mcp-workflows.md`.
- A2A agents: register or configure agents, discover them at `/v1/agents`, call JSON-RPC through `/a2a/{agent_id}`, or call a registered agent from LiteLLM routes with model name `a2a/<agent-name>`; see `references/a2a-workflows.md`.
- Claude Code and Cursor gateway traffic: make the client base URL point at the LiteLLM proxy endpoint that matches the client protocol, ensure requested model names match proxy `model_name` entries, and troubleshoot base URL/header confusion with `references/agent-gateway-troubleshooting.md`.
- Tool approval and policy: use proxy guardrails such as `tool_permission`, MCP server `allowed_tools` / `disallowed_tools`, key/team `mcp_tool_permissions`, and optional MCP semantic filtering before enabling broad tool access.
- Offline inspection: use `scripts/inspect_mcp_tools.py` to validate a JSON file containing OpenAI-format tool definitions or MCP server metadata without connecting to any external MCP server.

## Minimal MCP gateway config

```yaml
model_list:
  - model_name: claude-3-5-sonnet
    litellm_params:
      model: anthropic/claude-3-5-sonnet-20241022
      api_key: os.environ/ANTHROPIC_API_KEY

mcp_servers:
  docs:
    url: https://example.invalid/mcp
    transport: http
    auth_type: authorization
    alias: docs

general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
```

Start the proxy with `litellm --config config.yaml`, then point an MCP client at `http://localhost:4000/mcp` with `Authorization: Bearer <litellm-key>` and `x-mcp-servers: docs`. For per-server upstream auth, prefer `x-mcp-docs-authorization: Bearer <upstream-token>` over a broad legacy `x-mcp-auth` header.

## Minimal A2A agent config

```yaml
agents:
  - agent_name: research-agent
    agent_card_params:
      name: Research Agent
      description: Answers research questions
      url: https://agent.example.invalid/
      version: "1.0.0"
      protocolVersion: "0.3.0"
      capabilities:
        streaming: true
      defaultInputModes: [text]
      defaultOutputModes: [text]
      skills:
        - id: research
          name: Research
          description: Research public information
          tags: [research]
    litellm_params: {}
```

Clients can discover with `GET /v1/agents`, send A2A JSON-RPC to `/a2a/research-agent`, or call LiteLLM chat/completion routes with `model: a2a/research-agent` when the agent is registered and the key/team is allowed to use it.

## Validation checklist

- Confirm optional dependencies before using advanced flows: MCP needs the proxy MCP extra; direct A2A examples require `a2a-sdk`.
- Keep server identity consistent: `server_name`, `alias`, path-scoped MCP endpoint, `x-mcp-servers`, and `x-mcp-<server>-authorization` must refer to the same server label. Header matching is case-insensitive and checks alias before server name.
- Check auth precedence: server-specific MCP auth headers override legacy `x-mcp-auth`; OAuth per-user headers can override configured static tokens; config `auth_value` / `authentication_token` is used when no request header supplies auth.
- Verify agent permissions: non-admin keys can be denied for `a2a/<agent-name>` if key/team object permissions or access groups do not include the agent id.
- Inspect proxy logs for the exact model, MCP server, or agent name requested by Claude Code, Cursor, or an A2A client.

## References

- `references/mcp-workflows.md`: MCP gateway setup, clients, auth, OAuth, permissions, semantic filtering, and offline inspection.
- `references/a2a-workflows.md`: A2A registration, discovery, direct JSON-RPC, LiteLLM `a2a/` routing, and key/team permissions.
- `references/agent-gateway-troubleshooting.md`: Claude Code, Cursor, MCP/A2A failures, OAuth cache, semantic filters, and common access-denied paths.
