# Tools and Integrations Troubleshooting

Start with safe local checks:

```bash
python skills/adk-python/sub-skills/tools-and-integrations/scripts/inspect_tooling.py
python skills/adk-python/sub-skills/tools-and-integrations/scripts/inspect_tooling.py --json
```

The script reports core signatures and optional-extra availability without network access, credential reads, subprocess launches, or destructive writes.

## Missing Optional Extras

### `ModuleNotFoundError: No module named 'mcp'`

Cause: the base install does not include the MCP SDK.

Fix:

1. Select or install an environment with `google-adk[mcp]`.
2. Keep imports on public paths such as `from google.adk.tools.mcp_tool import McpToolset`.
3. Re-run `inspect_tooling.py` and confirm `optional_modules.mcp.available` is true.
4. Validate connection params before running the agent: `StdioConnectionParams`, `SseConnectionParams`, or `StreamableHTTPConnectionParams`.
5. Do not start arbitrary local MCP commands (`npx`, `uvx`, Docker, shell scripts) without explicit user approval.

### `Please install with: pip install "google-adk[extensions]"`

Cause: extension-backed helpers are not included in base install. Common affected areas include retrieval helpers, `load_web_page`, CrewAI/LangChain-style adapters, Docker/Kubernetes/sandbox helpers, Firestore services, and some toolbox-related dependencies.

Fix:

1. Confirm the requested class belongs to an extension-backed module.
2. Install/select `google-adk[extensions]`, or choose a base-install alternative.
3. Re-run a minimal import probe; do not treat this as a source-code bug.

### Missing cloud client packages

Symptoms include missing `google.cloud.bigquery`, `google.cloud.bigtable`, `google.cloud.spanner`, `google.cloud.pubsub`, `google.cloud.discoveryengine`, `google.cloud.storage`, or telemetry exporters.

Fix:

1. Use `google-adk[gcp]` for Google Cloud toolsets and clients.
2. Use `google-adk[tools]` for Google API discovery (`google-api-python-client`).
3. Confirm IAM, billing, project, location, API enablement, and quota separately from import availability.
4. For database persistence extras (`sqlalchemy`, `sqlalchemy-spanner`), route service-lifecycle work to `runtime-services`.

### A2A import errors

Cause: `a2a-sdk` is optional.

Fix:

1. Install/select `google-adk[a2a]`.
2. For local exposure, use `to_a2a(...)` only after import succeeds.
3. For hosting, server commands, ports, and deployment, route to `cli-configuration-deployment`.

## Tool Schema Conversion Issues

Symptoms:

- Model sees the wrong tool arguments.
- Pydantic argument conversion fails.
- `ToolContext` appears as a model-visible parameter.
- Function declaration has unexpected snake_case/camelCase names.

Checks and fixes:

- Name the context parameter exactly `tool_context` and annotate with `ToolContext`.
- Add type hints to all model-visible parameters; avoid untyped `*args` and `**kwargs` for LLM-called tools.
- Keep parameter types JSON-schema friendly: `str`, `int`, `float`, `bool`, lists, dictionaries, enums, and Pydantic models.
- For OpenAPI tools, set `preserve_property_names=True` when the target API requires original property names.
- For required argument errors, inspect the `{"error": "mandatory input parameters are not present"}` response; ADK intentionally returns this to let the model retry.
- If a docstring is missing, the tool description is weak; add a concise action-oriented docstring.

## Confirmation Confusion

Symptoms:

- Tool keeps asking for confirmation.
- `request_confirmation requires function_call_id`.
- User approval is ignored.
- Confirmation and long-running behavior are conflated.

Fixes:

- `tool_context.request_confirmation()` only works inside a tool invocation where `function_call_id` is set.
- For always-sensitive tools, prefer `FunctionTool(func=..., require_confirmation=True)`.
- For conditional sensitivity, check `if not tool_context.tool_confirmation`, call `request_confirmation()`, set `skip_summarization` if needed, and return an error-like pending response.
- On resumed calls, inspect `tool_context.tool_confirmation.confirmed`; if false, return a rejection response.
- Use `LongRunningFunctionTool` for pending external work, not for simple approve/reject confirmation.
- For multiple simultaneous sensitive tools, expect separate function-call ids and confirmation payloads.

## Long-Running Tool Problems

Symptoms:

- Model starts the same operation repeatedly.
- Pending job result is summarized as final success.
- Human input tool never resumes.

Fixes:

- Wrap starter functions in `LongRunningFunctionTool`; the declaration tells the model not to call it repeatedly after pending status.
- Return stable identifiers such as `operation_id` or `ticket_id`.
- Add a separate status/read tool for polling instead of reusing the starter tool.
- Ensure client/runtime supports long-running tool resume or request-input flow.
- For workflow graph `RequestInput` or node resume behavior, route to `workflow-orchestration`.

## Tool Errors Returned as Function Responses

Symptoms:

- A tool raises, but the agent continues.
- A tool returns `{"error": "..."}` and the model treats it as recoverable.
- `on_tool_error_callback` appears to hide exceptions.

How ADK behaves:

- If a tool returns a dictionary with an `error` key, ADK emits it as a normal function response and marks a tool-error type for telemetry.
- If a tool raises, ADK runs plugin `on_tool_error_callback` first, then agent `on_tool_error_callback` callbacks.
- Any callback that returns a non-`None` dictionary replaces the exception with a function response.
- If callbacks return `None`, the original exception is raised.

Fixes:

- To fail fast, make `on_tool_error_callback` return `None` for that tool.
- To recover, return `{"error": "clear user-visible message", "retryable": true}` or another documented dictionary.
- Inspect event streams for `function_call` and `function_response` parts to see what the model actually received.
- Check `after_tool_callback` as well; it can alter successful or callback-handled tool responses.

## Auth and Credential Errors

Symptoms:

- `Credential service is not initialized`.
- OAuth flow keeps restarting.
- API returns 401/403 even though credentials were supplied.
- `service_account_credential is required when use_default_credential is False`.
- `audience is required when use_id_token is True`.

Fixes:

- Use `AuthConfig(auth_scheme=..., raw_auth_credential=..., credential_key="stable_key")` for interactive or reusable flows.
- Use a runner/app with a credential service when tools call `load_credential`, `save_credential`, or `request_credential`.
- Do not call `request_credential()` outside a real tool call; it requires `function_call_id`.
- For OAuth/OIDC, make sure the scheme endpoints, scopes, redirect URI/client behavior, and client id/secret match.
- For service accounts, choose exactly one viable mode: full service account JSON or `use_default_credential=True`.
- For ID tokens, set `audience` to the receiving service URL.
- Distinguish import success from IAM success; 403s usually require IAM/API/billing changes, not code changes.
- Never log or embed token values, private keys, client secrets, or local credential file paths.

## MCP Session and Resource Errors

Symptoms:

- MCP server command hangs.
- SSE/Streamable HTTP times out.
- Tools list once but fail later.
- Resource loading fails.
- Progress callback never fires.

Fixes:

- Use `StdioConnectionParams(..., timeout=...)` rather than legacy raw `StdioServerParameters` when launching local servers.
- Confirm server command, args, and working-directory assumptions with the user before running local subprocesses.
- Use `tool_filter` to expose only expected tool names.
- Use `tool_name_prefix` when combining multiple MCP servers.
- For remote servers, validate URL scheme, auth headers, TLS/proxy settings, and `sse_read_timeout`.
- If using `use_mcp_resources=True`, verify the server actually implements resource listing/reading.
- Call `await toolset.close()` when manually managing a toolset outside the runner lifecycle.
- Treat cancellation during teardown as normal in async runtimes unless it masks a repeated connection failure.

## OpenAPI and HTTP Tool Errors

Symptoms:

- Spec parse fails.
- Endpoint tools have confusing names.
- API rejects request body/parameter casing.
- TLS/proxy errors occur.
- Auth is missing from requests.

Fixes:

- Pass exactly one of `spec_dict` or `spec_str`/`spec_str_type` and confirm JSON/YAML type.
- Use `tool_filter` to trim the exposed operation set.
- Use `tool_name_prefix` to avoid collisions.
- Use `preserve_property_names=True` when the backend expects camelCase or original names.
- Use `ssl_verify` for custom CA bundles, or `httpx_client_factory` for proxies, HTTP/2, custom transports, or signing.
- Use OpenAPI auth helpers or explicit `AuthConfig`/`AuthCredential` pairs; set a stable `credential_key` for resumable auth.
- Confirm whether a 4xx response is API semantics, expired credentials, missing scopes, or IAM.

## Google API and Cloud Integration Errors

Symptoms:

- Discovery conversion fails.
- Cloud client import is missing.
- ADC is not found.
- API returns permission/quota/billing errors.
- Tool exposes too many destructive operations.

Fixes:

- Confirm the required extra: `google-adk[tools]` for discovery clients, `google-adk[gcp]` for cloud clients, `google-adk[agent-identity]` for identity connector credentials.
- For discovery-based toolsets, pass `additional_scopes` when default discovery scopes are insufficient.
- For Application Integration/API Hub, confirm project, location, resource names, and service account/connector auth mode.
- For admin toolsets such as Spanner admin, add `tool_filter` and confirmation around destructive operations.
- Separate local import/signature checks from real cloud calls; cloud calls require network, enabled APIs, IAM, billing, and quota.

## A2A Errors

Symptoms:

- `a2a` imports fail.
- Agent card generation fails.
- Remote agent cannot connect.
- Task state disappears.

Fixes:

- Install/select `google-adk[a2a]`.
- Ensure the local object passed to `to_a2a()` is a `BaseAgent` or `Workflow` with a name and useful description.
- If using a custom agent card path, validate the JSON before startup.
- For remote agents, confirm the agent-card URL and well-known path.
- In-memory task stores are volatile; persistent task stores and database lifecycle route to `runtime-services`.
- Server launch, ports, TLS, CORS, and deployment route to `cli-configuration-deployment`.

## Safe Debugging Sequence

1. Run `inspect_tooling.py` and record core signatures plus missing extras.
2. Isolate whether the failure is import-time, construction-time, tool-listing-time, tool-call-time, callback-time, or model-summarization-time.
3. For imports, install/select the correct extra rather than rewriting public import paths.
4. For construction, print or inspect constructor signatures and validate required parameters.
5. For tool-listing, check `tool_filter`, auth config, and resource/session setup.
6. For tool-call failures, inspect function responses, exceptions, and `on_tool_error_callback` behavior.
7. For external integrations, verify credentials and network only after local import/config checks pass.
8. Keep secrets out of logs and never add local machine paths to reusable skill content.
