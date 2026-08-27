# Troubleshooting MCP Server Integration

Use this guide when MCP servers fail to connect, tools are missing, workflow endpoints do not appear, OAuth fails, or MCP primitives behave unexpectedly.

## Quick Triage

1. Run `scripts/validate_server_config.py` against the config.
2. Confirm every `server_name` used by an agent, workflow, `gen_client`, `MCPAggregator`, or stored credential matches a key in `mcp.servers` exactly.
3. Validate transport-specific fields: `command` for `stdio`; `url` for `sse`, `streamable_http`, and `websocket`.
4. List primitives before invoking them: `list_tools`, `list_resources`, `list_prompts`, and `list_roots` where supported.
5. Use `workflows-list` on app servers to discover actual exposed tool endpoints.
6. Check auth separately from transport: a bad URL/command is not an OAuth problem.

## Unknown Server Names

Symptoms:

- `Server '<name>' not found in registry.`
- Agent has no tools from the expected server.
- `workflows-store-credentials` rejects a token because `server_name` is not recognized.

Fixes:

- Compare the exact key under `mcp.servers` to every `server_names=[...]`, `gen_client("...")`, `MCPAggregator([...])`, and token `server_name` value.
- Remember that `name` inside a server entry is a display name; the registry key is what code uses.
- If a workflow adds servers dynamically, ensure it mutates `app.context.config.mcp.servers` or the active registry before opening the connection.

## Transport URL and Config Errors

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Command and args are required for stdio transport` | `transport: stdio` without `command`/`args` | Add `command` and list-style `args`. |
| `URL is required for SSE transport` | `transport: sse` without `url` | Add an HTTP(S) SSE URL. |
| `URL is required for Streamable HTTP transport` | `streamable_http` without `url` | Add an HTTP(S) MCP URL. |
| `URL is required for websocket transport` | `websocket` without `url` | Add a WS(S) URL. |
| `Unsupported transport` | Typo or unsupported alias | Use `stdio`, `sse`, `streamable_http`, or `websocket`. |
| Remote stream disconnects while idle | Read timeout too short | Increase `read_timeout_seconds`. |
| HTTP request fails quickly | HTTP timeout too short or endpoint unreachable | Increase `http_timeout_seconds` and verify URL. |

Run:

```bash
python sub-skills/mcp-server-integration/scripts/validate_server_config.py mcp_agent.config.yaml
```

## Missing Command Executables

Symptoms:

- Stdio server fails during startup.
- Error mentions missing executable, spawn failure, or file not found.

Fixes:

- Run the validator with executable checks:

```bash
python sub-skills/mcp-server-integration/scripts/validate_server_config.py mcp_agent.config.yaml --check-executables
```

- Install only the server runtime needed for the chosen transport.
- Prefer stable package runners (`uvx`, `npx`, `python -m ...`) over shell-specific aliases.
- Avoid embedding activation commands in `command`; run the app from the intended environment instead.

## OAuth Metadata, Client Secret, and Resource Parameter Issues

Symptoms:

- Browser authorization opens but token exchange fails.
- Provider says invalid client, invalid audience, invalid resource, or state mismatch.
- OAuth configured but requests are unauthenticated.
- A remote MCP server requires resource metadata.

Fixes:

- Confirm `auth.oauth.enabled: true` on the upstream server.
- Confirm global `oauth` settings are present so the app context has a token manager.
- Check `client_id` and `client_secret` come from secrets or environment placeholders.
- Set `authorization_server` when provider metadata advertises more than one authorization server.
- Set `resource` for providers that expect RFC 8707 resource indicators.
- Keep `include_resource_parameter: true` for providers that require resource metadata; set it to `false` only for providers that reject it.
- Confirm `redirect_uri_options` contains a URI registered with the OAuth provider.
- If using internal callbacks, set `oauth.callback_base_url` to the externally reachable app base URL.
- If using loopback, ensure one configured `loopback_ports` value is free and registered with the provider.

## Token Store Backend Missing Redis Extra

Symptoms:

- Redis token store import or connection errors.
- Tokens work in one process but disappear after restart or are unavailable to workers.

Fixes:

- Use `backend: memory` only for local short-lived flows.
- For Redis, install the Redis extra in the runtime environment.
- Set `oauth.token_store.redis_url` and, when sharing across apps, a deliberate `redis_prefix`.
- Verify every process uses the same token-store settings.
- Increase `refresh_leeway_seconds` if refreshes happen too close to expiry.

## App Server Workflow Tools Missing

Symptoms:

- `workflows-list` is absent.
- Decorated tools do not show up.
- Explicit workflow endpoint `workflows-<WorkflowName>-run` is missing.

Fixes:

- Ensure app logic is registered before `async with app.run() as agent_app` enters server startup.
- Call `create_mcp_server_for_app(agent_app, **kwargs)` inside the `app.run()` context.
- Let the FastMCP lifespan run; app-server workflow tools are registered during the managed lifespan.
- Use `scripts/minimal_app_server.py --mode dry-run --json` to compare the expected app-server surface without starting a network listener.
- For `@app.tool` and `@app.async_tool`, look for the declared tool name, not `workflows-<name>-run`.
- For explicit `@app.workflow` classes, look for `workflows-<WorkflowClassName>-run`.

## Decorator Tool Schema Problems

Symptoms:

- Tool schema contains `self` or internal context parameters.
- Calling a tool fails because context was not provided.
- Async tool returns IDs when the caller expected the final result.

Fixes:

- Use `@app.tool` for caller-facing synchronous results.
- Use `@app.async_tool` only when callers should poll with `workflows-get_status`.
- Use `app_ctx` for optional `mcp-agent` app context parameters in decorated functions; it is stripped from the public schema.
- If a FastMCP context is needed, annotate it as the FastMCP `Context` type or use a conventional `ctx` parameter.
- Inspect `workflows-list` to see the generated parameter schema.

## Elicitation Callback Absent

Symptoms:

- A nested server tool pauses or fails when asking the user for structured input.
- Error mentions no context/session for elicitation.
- User never sees an elicitation prompt.

Fixes:

- Construct `MCPApp(..., elicitation_callback=...)` when servers may call `elicitation/create`.
- In local console flows, use the package console elicitation handler.
- With a connected MCP client, confirm the upstream session supports elicitation.
- Keep elicitation schemas to primitive field types (`str`, `int`, `float`, `bool`).
- Handle accepted, declined, and cancelled outcomes in server tools.

## Sampling Approval Problems

Symptoms:

- A nested server requests sampling and the app errors or hangs.
- A human approval prompt is expected but never appears.

Fixes:

- Construct `MCPApp(..., human_input_callback=...)` for local approval flows.
- Confirm the app has a compatible LLM provider for local sampling.
- When a client is connected, confirm sampling requests can be proxied upstream.
- Do not auto-approve sampling in production without an explicit policy.

## Roots URI Mistakes

Symptoms:

- Config validation fails for roots.
- Server cannot access the expected file tree.
- A containerized server sees a different URI than the client declared.

Fixes:

- Every `roots[].uri` must start with `file://`.
- Every `roots[].server_uri_alias`, when present, must also start with `file://`.
- Use `server_uri_alias` for container mount paths or server-presented paths.
- Keep root access minimal and avoid broad project or home-directory roots.

## Server Tool Name Collisions

Symptoms:

- Two servers expose the same tool name.
- The agent calls the wrong backend or the aggregator reports ambiguous tools.

Fixes:

- Use `MCPAggregator`, which tracks namespaced tools, prompts, and resources by server.
- Restrict each server with `allowed_tools` so only intentional tools are visible.
- Give agents explicit instructions about which server’s namespaced tool to prefer.
- Split agents by server responsibility when a single combined surface is too confusing.

## Client Installation and Remote Exposure Safety

Before telling a user to install a client config or expose a server:

- Use dry-run validation first.
- Keep bearer tokens and OAuth client secrets in placeholders or secret files.
- Bind development app servers to loopback addresses.
- Add top-level `authorization` before exposing an app server to remote clients.
- Use `allowed_tools` for upstream servers and review decorated app tools for side effects.
- Move cloud install/deploy command details to `../cli-cloud-operations/SKILL.md` after this server integration is correct.
