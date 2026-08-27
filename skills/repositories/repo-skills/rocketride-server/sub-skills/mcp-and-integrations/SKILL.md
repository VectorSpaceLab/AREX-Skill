---
name: mcp-and-integrations
description: "Expose RocketRide pipelines through MCP assistants and n8n/webhook
  integrations."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# MCP and Integrations

Use this sub-skill when RocketRide must talk to an assistant, MCP client, n8n
workflow, webhook endpoint, or external automation tool. Keep this focused on
integration edges; route ordinary SDK calls, runtime startup, and general `.pipe`
authoring to the neighboring sub-skills.

## Use this for

- Configuring `rocketride-mcp` for Claude Desktop, Cursor, Claude Code, or another
  MCP-compatible assistant.
- Explaining how running RocketRide pipelines become MCP tools and how the
  built-in `RocketRide_Document_Processor` convenience tool works.
- Reading MCP resources (`rocketride://pipelines`, `rocketride://status`,
  `rocketride://nodes`) or using MCP prompt templates.
- Connecting n8n to RocketRide through the community action node, HTTP Request
  nodes, RocketRide Trigger nodes, or RocketRide `tool_n8n` pipeline nodes.
- Debugging auth variables, webhook activation, `localhost`/container reachability,
  IPv6 loopback, public/private host boundaries, and 16 MB payload limits.

## Do not use for

- Generic Python/TypeScript SDK start, upload, status, CLI, or token lifecycle
  details → `../sdk-clients/SKILL.md`.
- General pipeline JSON structure, lanes, control wiring, or provider selection →
  `../pipeline-authoring/SKILL.md`.
- Starting the RocketRide engine, Docker/Helm deployment, or WebSocket protocol
  operations → `../runtime-deployment/SKILL.md`.
- Node/service-definition maintenance outside integration nodes →
  `../nodes-catalog/SKILL.md`.

## Operating order

1. Identify the direction: assistant → MCP → RocketRide, n8n → RocketRide,
   RocketRide → n8n, or a round trip that combines both directions.
2. For MCP, validate only environment/config first. Do not start `rocketride-mcp`,
   `rocketride-mcp-sse`, an engine, or a client app unless the user explicitly
   asks for that runtime action.
3. For MCP tools, confirm the target RocketRide pipeline is already running and
   that the assistant will pass a local `filepath` to the tool.
4. For n8n, distinguish three credentials: RocketRide MCP engine auth
   (`ROCKETRIDE_AUTH`/`ROCKETRIDE_APIKEY`), RocketRide HTTP gateway public `pk_…`
   keys for n8n action nodes, and n8n public API keys (`ROCKETRIDE_N8N_KEY`).
5. Check where each process runs before blaming auth: container `localhost`, IPv6
   `localhost` (`::1`), private Cloud-inaccessible hosts, and missing reverse-proxy
   `WEBHOOK_URL` explain many failures.

## Safe checks

Use the bundled smoke script for config-only MCP validation:

```bash
python scripts/mcp_config_smoke.py
python scripts/mcp_config_smoke.py --check-current-env
python scripts/mcp_config_smoke.py --client-config ./mcp.json --server-name rocketride
```

The script imports only the `rocketride_mcp.config` loader when available, never
starts a server, and never connects to a RocketRide engine.

## Reference map

- [MCP server](references/mcp-server.md) — package behavior, env vars, client
  config blocks, dynamic tools, resources, prompts, and stdio/SSE notes.
- [n8n and webhooks](references/n8n-and-webhooks.md) — n8n action/trigger nodes,
  RocketRide `tool_n8n`, HTTP request settings, and round-trip recipes.
- [Troubleshooting](references/troubleshooting.md) — auth, command discovery,
  filepath, webhook, payload, TLS, and network-boundary failures.

## What good output looks like

- Uses the correct port/protocol for the integration edge (`ws://…:5565` for MCP
  engine access; `http://…:5567/webhook` for HTTP gateway calls).
- Names the correct auth variable or credential for that edge.
- Avoids hardcoded secrets and uses environment placeholders in reusable snippets.
- Does not claim n8n, MCP clients, Docker, Cloud, or external providers are
  verified unless they were explicitly run with the user's services and secrets.
