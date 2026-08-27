# Integration Troubleshooting

Use this reference when an integration fails before or during runtime. Start with no-network import/signature checks, then isolate optional dependencies, provider-native-vs-local execution, lifecycle, identity, and external service requirements.

## Fast Diagnostics

Run the bundled diagnostic script first:

```bash
python scripts/integration_import_check.py --all
```

The script reports import availability and constructor signatures only. It never starts MCP servers, opens URLs, launches ASGI apps, connects to durable backends, validates credentials, or prints secret values.

## Optional Dependency Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ImportError` mentioning `mcp` when importing `pydantic_ai.mcp` | MCP optional dependencies are missing. | Install the MCP extra for local MCP client/server wrappers. |
| `ImportError` mentioning `fastmcp` or `fastmcp-slim[client]` | FastMCP client dependency is missing or only the bare MCP SDK is installed. | Install the MCP extra or the full FastMCP package when using `MCPToolset`/FastMCP inputs. |
| `FastMCPToolset` import works but warnings appear | `FastMCPToolset` is deprecated. | Migrate to `pydantic_ai.mcp.MCPToolset`. |
| `ImportError` for `ag_ui`, `starlette`, `fasta2a`, `temporalio`, `prefect`, `dbos`, or `logfire` | Optional integration group is not installed. | Install only the extra/package for the integration being used. Do not install all provider/backend extras blindly. |
| Local web search/fetch fallback fails | `duckduckgo` or `web-fetch` optional extras are missing. | Install the specific common-tool extra or pass `local=False` to require provider-native support. |

Do not treat a missing optional extra as a Pydantic AI core failure. Most integrations intentionally import lazily or behind optional groups.

## MCP Native vs Client-Executed Confusion

The most common MCP mistake is mixing provider-native MCP with local MCP toolsets.

Check these questions:

- Should the model provider call the MCP server directly? Use `MCP(..., native=True)` and verify the selected provider/model supports native MCP.
- Should the application call the MCP server and send tool results back to the model? Use `MCPToolset(...)` or `MCP(..., native=False/local=True)` with the MCP extra installed.
- Does the MCP server require private network access only available to the application host? Prefer local `MCPToolset`; provider-native calls may not reach it.
- Does the server require provider-side credentials or hosted OAuth? Native may fit better, but verify provider support.
- Are headers/tokens different between native and local paths? Ensure `authorization_token`/`headers` are safe and appropriate for both.

Warnings and migration signals:

- `MCP()` default behavior warns because v2 changes the native/local default. Pass `native=True` to keep native-preferred behavior, or `native=False` for local-first behavior.
- `MCP(local='...')` accepts only HTTP(S) URLs. For script paths, transports, in-process servers, or pre-built clients, pass `local=MCPToolset(...)`.
- `MCPServer*`, `load_mcp_servers()`, and `FastMCPToolset` are deprecated compatibility paths.

## MCP Lifecycle and Tool Catalog Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Server subprocess starts/stops repeatedly | Toolset/server is entered implicitly per operation. | Wrap a run block with `async with agent:` or `async with toolset:`. |
| Tool names conflict across MCP servers | Two servers expose the same tool name. | Prefix or rename toolsets before combining; `MCPToolset` suggests `.prefixed('...')`. |
| Tool list is stale | Server changed tools without sending list-change notifications or durable wrapper cached definitions. | Set `cache_tools=False` and check durable wrapper caching. |
| Server instructions are missing | `include_instructions=False` or toolset not initialized yet. | Set `include_instructions=True` and enter the toolset/agent lifecycle before reading instructions. |
| `MCPError` from resources/prompts | Server did not advertise capability or returned an MCP error. | Check `server_capabilities`, handle missing resource/prompt support, and surface the server error code. |
| Sampling through MCP fails | Server requested sampling but client did not provide sampling support/model. | Configure `sampling_model`/sampling handler on the client path, or avoid server-side sampling. |
| Stdio server cannot see environment variables | `MCPServerStdio` does not inherit parent env by default. | Pass explicit `env=` values; avoid broad `os.environ` unless intentional. |

## Deferred Capability ID Stability

Symptoms:

- A resumed conversation forgets a capability was loaded.
- The model calls `load_capability` repeatedly after history replay.
- Hooks/tools from an on-demand capability do not activate after resume.

Fixes:

- Set stable explicit `id=` on every deferred capability, especially `MCP`, `WebSearch`, `WebFetch`, and custom `Capability`/`Hooks` instances.
- Reconstruct the resumed agent with the same capabilities and IDs.
- Do not derive IDs from class names, local paths, or environment-specific URLs when history is persisted.
- Remember that loaded capability state lives in message history; definitions live in code.

## Hook Ordering and State Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Hook sees empty `ctx.tools` or old request parameters | Hook fires before current request assembly. | Move logic to `before_model_request` or later if it needs current tool/native-tool/request state. |
| Deferred hook does not fire | Its owning capability has not been loaded. | Keep enforcement hooks always-on when they must run before load, or inspect `ctx.loaded_capability_ids` from another capability. |
| Run wrapper does not apply after mid-run capability load | Run hooks are bound at run start. | Resume with history after the capability has loaded, or keep the run wrapper always available. |
| `after_*` order is surprising | `after_*` hooks run in reverse order; wrappers nest. | Use `CapabilityOrdering` or consolidate dependent hooks into one capability. |
| Hook timeout aborts work | Hook exceeded configured timeout. | Increase timeout only for bounded work; avoid network or long-running side effects in hooks. |
| Error hook does not catch `ModelRetry` | `ModelRetry` is control flow for retries. | Catch expected validation/tool errors before raising `ModelRetry`, or handle retry exhaustion separately. |

## Logfire and OTel Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `logfire` import fails | Logfire optional dependency is missing. | Install the Logfire extra/package or use plain OTel setup. |
| No traces appear | SDK/backend not configured or agent instrumentation not enabled. | Configure Logfire/OTel provider and call instrumentation setup or add `Instrumentation()` capability. |
| Sensitive content appears in traces | Content capture is enabled. | Disable content/binary capture through instrumentation settings and review backend retention policy. |
| Durable Temporal Logfire plugin errors | Temporal worker/plugin dependencies or sandbox passthrough setup mismatch. | Use the durable integration plugin rather than ad hoc imports inside workflow code. |

## Durable Backend Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Import fails for `temporalio`, `prefect`, or `dbos` | Backend package not installed. | Install only the selected backend integration dependency. |
| Backend service connection fails | Workflow service/server is not running or not configured. | Start/configure the backend outside Pydantic AI; the wrappers do not provision services. |
| Agent wrapper requires unique name | Durable backend needs stable workflow/activity/step names. | Set `Agent(..., name='stable-name')` or pass wrapper `name=`. |
| Toolset ID error in Temporal/durable wrappers | Leaf toolset lacks stable `id`. | Assign `id=` to `FunctionToolset`, `MCPToolset`, dynamic toolsets, or relevant wrappers. |
| Non-wrapper model override rejected inside workflow | Durable replay cannot accept arbitrary runtime model changes. | Configure model before wrapping; use wrapper model provided by the backend integration. |
| Streaming rejected in workflow | Backend wrapper cannot preserve stream semantics inside workflow code. | Use `event_stream_handler` plus `agent.run()` where supported. |
| DBOS duplicate instance registration | Same wrapper name registered twice. | Use unique names and avoid recreating module-level configured instances with the same name. |

## UI Adapter Message and Security Issues

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Client system prompt is ignored | `manage_system_prompt='server'` strips frontend system prompts. | Keep this for untrusted clients; switch to `'client'` only when the frontend owns prompts safely. |
| Uploaded files or non-HTTP file URLs are dropped | Adapter sanitization protects server/provider credentials. | Use HTTPS URLs or explicitly allow schemes/file preservation after frontend audit. |
| AG-UI thinking/reasoning events differ by environment | Installed AG-UI protocol version changes event thresholds. | Set `ag_ui_version` deliberately and test frontend handling. |
| AG-UI interrupt approval denied unexpectedly | Resume payload did not include explicit `approved: true`. | Send a valid resume payload; malformed entries deny by default. |
| Vercel tool approvals do not resume | `sdk_version` is less than 6. | Use `sdk_version=6` for tool approval streaming. |
| Frontend tools do not execute server-side | UI adapters expose frontend tools as external/deferred tools. | Resume with matching `DeferredToolResults`; route generic deferred-tool design to tools-and-toolsets. |
| Built-in web UI cannot use memory native tool | That native tool is unsupported via web UI options. | Configure memory directly on the agent or build a custom UI endpoint. |
| Web UI fetches UI HTML unexpectedly | Default web app may fetch/cache UI assets. | Provide local `html_source` for offline/enterprise environments. |

## Credentials and Services Boundaries

Credentials and backend services are outside safe bundled diagnostics.

Do not claim success until the actual deployment has verified:

- provider API keys or OAuth setup for native tools, model calls, and provider-native MCP;
- MCP server availability, auth headers, TLS settings, and network reachability from the actual caller;
- durable backend service availability and worker registration;
- ASGI server deployment, CORS/auth/session handling, and frontend trust boundaries;
- Logfire/OTel backend configuration and content-capture policy.

Keep public guidance focused on configuration names and required extras. Never print or persist credential values in logs, traces, test artifacts, or generated skill files.
