# Tools and Integrations API Reference

This reference targets `google-adk` 2.3.0, import root `google.adk`, Python 3.10+. Base installs include core tool abstractions but intentionally omit some integration extras.

## Core Tool Imports

Use these public imports first:

```python
from google.adk.tools import AgentTool
from google.adk.tools import BaseTool
from google.adk.tools import FunctionTool
from google.adk.tools import LongRunningFunctionTool
from google.adk.tools import ToolContext
from google.adk.tools import TransferToAgentTool
from google.adk.tools import transfer_to_agent
```

Other useful direct imports:

```python
from google.adk.tools.base_toolset import BaseToolset, ToolPredicate
from google.adk.tools.authenticated_function_tool import AuthenticatedFunctionTool
from google.adk.tools._request_input_tool import request_input
from google.adk.auth.auth_tool import AuthConfig, AuthToolArguments
from google.adk.auth.auth_credential import AuthCredential, AuthCredentialTypes, OAuth2Auth, ServiceAccount
from google.adk.auth.auth_schemes import AuthScheme, AuthSchemeType, OpenIdConnectWithConfig, ExtendedOAuth2
```

## `FunctionTool`

`FunctionTool(func: Callable[..., Any], *, require_confirmation: bool | Callable[..., bool] = False)` wraps a Python callable.

- `func.__name__` becomes the tool name; the docstring becomes the tool description.
- Parameters named or typed as `ToolContext` are ignored in the model-visible schema and injected at runtime.
- `input_stream` is also ignored for streaming tool internals.
- Missing mandatory args return an `{"error": "..."}` response instead of invoking the callable.
- Pydantic `BaseModel` arguments and `list[BaseModel]` values are validated/coerced from JSON dictionaries before invocation.
- A synchronous or async callable is supported.
- If `require_confirmation` is true or returns true, ADK requests `ToolConfirmation`; rejected calls return `{"error": "This tool call is rejected."}`.
- A returned dictionary containing an `error` key is detected as `TOOL_ERROR` for telemetry and callbacks.

Use `FunctionTool` explicitly for confirmation, custom metadata inherited from `BaseTool`, or when a future reader needs tool-object clarity. Otherwise an `Agent(..., tools=[callable])` path can be enough.

## `LongRunningFunctionTool` and Input Requests

`LongRunningFunctionTool(func: Callable)` subclasses `FunctionTool` and sets `is_long_running = True`.

- Its function declaration description includes a note that the model must not call it again after it returns pending/intermediate status.
- It is appropriate for external approvals, asynchronous jobs, or human-in-the-loop pauses.
- `request_input` is a prebuilt `LongRunningFunctionTool` that asks a user question with `message: str` and optional `response_schema: dict`; it returns `None` to trigger the interruption mechanism.
- Long-running tool responses are tracked by function-call id; avoid inventing a second call to poll unless your tool contract explicitly exposes a safe polling tool.

## `BaseTool`

Subclass `BaseTool` when a callable wrapper is insufficient:

```python
class MyTool(BaseTool):
  def __init__(self):
    super().__init__(name="my_tool", description="Do one safe thing.")

  async def run_async(self, *, args: dict[str, Any], tool_context: ToolContext) -> Any:
    return {"result": args}
```

Constructor fields and behavior:

- `BaseTool(name, description, is_long_running=False, custom_metadata=None, response_scheduling=None)`.
- Override `_get_declaration()` when the tool should add a model-visible `FunctionDeclaration`.
- Override `run_async(args=..., tool_context=...)` for client-side execution.
- Override `process_llm_request(tool_context=..., llm_request=...)` for tools that mutate outgoing LLM requests instead of or in addition to normal function declarations.
- `custom_metadata` must be JSON-serializable.
- `response_scheduling` applies to Live API asynchronous function response scheduling (`SILENT`, `WHEN_IDLE`, `INTERRUPT`) and may be ignored by models that do not support it.

## `BaseToolset`

`BaseToolset(*, tool_filter: ToolPredicate | list[str] | None = None, tool_name_prefix: str | None = None)` groups tools and can manage shared resources.

Implementations must provide:

- `async get_tools(readonly_context: ReadonlyContext | None = None) -> list[BaseTool]`.
- `async close() -> None` when the toolset owns sessions, clients, subprocesses, or sockets.

Framework helpers:

- `get_tools_with_prefix()` applies `tool_name_prefix` to returned tool names and function declarations.
- `tool_filter` can be a list of tool names or a predicate `(tool, readonly_context) -> bool`.
- `process_llm_request()` lets a toolset alter outgoing LLM requests once per turn.
- `get_auth_config() -> AuthConfig | None` should be overridden when tool listing or tool calling needs ADK-managed credentials.
- `from_config()` must be implemented by toolsets that support YAML/config loading.

## `ToolContext`

`ToolContext` is an alias for `google.adk.agents.context.Context` during tool execution. The model does not fill this argument.

Frequently used members:

- `tool_context.state`: delta-aware session state mapping.
- `tool_context.actions`: event actions, including transfer, state delta, artifact delta, requested credentials, and requested confirmations.
- `tool_context.function_call_id`: current tool call id; required for credential and confirmation requests.
- `tool_context.tool_confirmation`: populated when a confirmation response resumes the call.
- `tool_context.request_confirmation(hint=None, payload=None)`: asks the client/user to approve or reject the current tool call.
- `tool_context.request_credential(auth_config)`: asks the client/user for credentials for the current tool call.
- `tool_context.get_auth_response(auth_config)`: reads a credential response from session state.
- `tool_context.load_credential(auth_config)` / `save_credential(auth_config, credential)`: use the configured credential service.
- `tool_context.save_artifact(...)`, `load_artifact(...)`, `list_artifacts(...)`: artifact service helpers when a service is configured.
- `tool_context.search_memory(query)`: memory service helper when a service is configured.
- `tool_context.run_node(node, node_input=..., use_sub_branch=...)`: workflow/agent node helper for advanced composition.

`request_confirmation()` and `request_credential()` raise `ValueError` outside an actual tool call because `function_call_id` is missing.

## Agent Tools and Transfer Tools

`AgentTool(agent, skip_summarization=False, *, include_plugins=True, propagate_grounding_metadata=False)` exposes an ADK agent as a tool.

- The wrapped agent name and description become the tool name and description.
- If the wrapped agent has `input_schema`, it is used for tool parameters; otherwise the model sends a `request` string or JSON object.
- The child agent runs with in-memory session and memory services, forwarded artifacts, and the parent credential service.
- Parent session state is forwarded to the child except internal `_adk` keys; child state deltas are merged back.
- `skip_summarization=True` marks the tool response as not needing another model summary.
- `include_plugins=False` isolates the child runner from parent plugins.
- `propagate_grounding_metadata=True` stores child grounding metadata in parent temp state.

`TransferToAgentTool(agent_names: list[str])` is a specialized `FunctionTool` around `transfer_to_agent(agent_name, tool_context)`.

- Prefer `TransferToAgentTool` over bare `transfer_to_agent` when you need enum constraints over valid agent names.
- The transfer implementation sets `tool_context.actions.transfer_to_agent = agent_name`.
- Agent construction and sub-agent descriptions belong to `agent-construction`; this reference only covers the tool mechanics.

## Auth Models

`AuthConfig(auth_scheme, raw_auth_credential=None, exchanged_auth_credential=None, credential_key=None)` is the value passed through ADK credential flows.

- `auth_scheme` is an OpenAPI `SecurityScheme`, `OpenIdConnectWithConfig`, or `CustomAuthScheme` union.
- `raw_auth_credential` holds initial credentials such as API key, OAuth client id/secret, or service account configuration.
- `exchanged_auth_credential` is filled by ADK/client flow with ready-to-use credentials.
- `credential_key` controls credential-service lookup; if omitted, ADK derives a stable key from scheme and raw credential.

`AuthCredential(auth_type=..., api_key=..., http=..., oauth2=..., service_account=..., resource_ref=...)` supports:

- `AuthCredentialTypes.API_KEY` with `api_key`.
- `AuthCredentialTypes.HTTP` with `HttpAuth(scheme="bearer" | "basic" | other, credentials=HttpCredentials(...))`.
- `AuthCredentialTypes.OAUTH2` with `OAuth2Auth(client_id=..., client_secret=..., auth_uri=..., access_token=..., refresh_token=...)`.
- `AuthCredentialTypes.OPEN_ID_CONNECT` with `OAuth2Auth` fields.
- `AuthCredentialTypes.SERVICE_ACCOUNT` with `ServiceAccount`.

`ServiceAccount` requires either `use_default_credential=True` or a full `service_account_credential`; when `use_id_token=True`, `audience` is required.

`AuthenticatedFunctionTool(func=..., auth_config=..., response_for_auth_required=...)` is experimental. It requests credentials through a `CredentialManager`, returns a pending response if user authorization is needed, and injects a `credential` argument into the callable when present.

## OpenAPI Tooling

Import:

```python
from google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset import OpenAPIToolset
from google.adk.tools.openapi_tool.auth import auth_helpers
```

`OpenAPIToolset(...)` constructor highlights:

- `spec_dict` or `spec_str` plus `spec_str_type="json" | "yaml"`.
- `auth_scheme`, `auth_credential`, `credential_key` for all generated tools.
- `tool_filter`, `tool_name_prefix` for selection and naming collisions.
- `ssl_verify` for certificate verification options.
- `header_provider(readonly_context) -> dict[str, str]` for dynamic headers.
- `httpx_client_factory` for custom async clients, proxies, HTTP/2, or signing.
- `preserve_property_names=True` when an API requires original camelCase/non-snake names.

Methods:

- `await get_tools(readonly_context=None) -> list[RestApiTool]`.
- `get_tool(tool_name) -> RestApiTool | None`.
- `configure_ssl_verify_all(...)`.
- `await close()`.

OpenAPI auth helpers create paired scheme/credential values for API keys, bearer tokens, service accounts, OIDC discovery, and related flows. Do not hard-code secrets in skill guidance; use environment variables or credential services.

## MCP Tooling

Install extra: `google-adk[mcp]` supplies `mcp>=1.24,<2`.

Imports:

```python
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from mcp import StdioServerParameters
```

`McpToolset(...)` constructor highlights:

- Required `connection_params`: `StdioConnectionParams`, `SseConnectionParams`, `StreamableHTTPConnectionParams`, or legacy `StdioServerParameters`.
- `tool_filter`, `tool_name_prefix` for selection and collision avoidance.
- `auth_scheme`, `auth_credential`, `credential_key` for ADK-managed auth.
- `require_confirmation` applies confirmation to all tools returned by the MCP server.
- `header_provider(readonly_context) -> dict[str, str]` for request headers.
- `progress_callback` for server progress notifications.
- `use_mcp_resources=True` adds `load_mcp_resource` and resource context.
- `sampling_callback` and `sampling_capabilities` enable MCP server-side sampling.

Connection params:

- `StdioConnectionParams(server_params=StdioServerParameters(command=..., args=[...]), timeout=5.0)`.
- `SseConnectionParams(url=..., headers=None, timeout=5.0, sse_read_timeout=300.0, httpx_client_factory=...)`.
- `StreamableHTTPConnectionParams(url=..., headers=None, timeout=5.0, sse_read_timeout=300.0, terminate_on_close=True, httpx_client_factory=...)`.

`MCPToolset` and `MCPTool` are compatibility aliases; prefer `McpToolset` and `McpTool`.

## Google API and Cloud Toolsets

These surfaces usually require `google-adk[tools]`, `google-adk[gcp]`, `google-adk[extensions]`, or integration-specific credentials.

Google API discovery:

```python
from google.adk.tools.google_api_tool.google_api_toolset import GoogleApiToolset
from google.adk.tools.google_api_tool.google_api_toolsets import CalendarToolset, GmailToolset, BigQueryToolset
```

`GoogleApiToolset(api_name, api_version, client_id=None, client_secret=None, tool_filter=None, service_account=None, tool_name_prefix=None, *, additional_headers=None, additional_scopes=None, discovery_url=None)` converts Google discovery docs to OpenAPI tools with OIDC auth. Convenience subclasses include `BigQueryToolset`, `CalendarToolset`, `GmailToolset`, `YoutubeToolset`, `SlidesToolset`, `SheetsToolset`, and `DocsToolset`.

API Hub and Application Integration:

```python
from google.adk.tools.apihub_tool.apihub_toolset import APIHubToolset
from google.adk.tools.application_integration_tool.application_integration_toolset import ApplicationIntegrationToolset
```

- `APIHubToolset(apihub_resource_name=..., access_token=None, service_account_json=None, name="...", description="...", lazy_load_spec=False, auth_scheme=None, auth_credential=None, tool_filter=None)` retrieves specs from API Hub and exposes OpenAPI-backed tools.
- `ApplicationIntegrationToolset(project=..., location=..., integration=..., triggers=..., connection=..., entity_operations=..., actions=..., tool_name_prefix=..., service_account_json=None, auth_scheme=None, auth_credential=None, tool_filter=None)` builds tools from Application Integration resources and connection specs.

Cloud/database toolsets:

- `DataAgentToolset(tool_filter=None, credentials_config=None, data_agent_tool_config=None)`.
- `PubSubToolset(tool_filter=None, credentials_config=None, pubsub_tool_config=None)`.
- `BigtableToolset(tool_filter=None, credentials_config=None, bigtable_tool_settings=None)`.
- `SpannerToolset(tool_filter=None, credentials_config=None, spanner_tool_settings=None)`.
- `SpannerAdminToolset(tool_filter=None, credentials_config=None, spanner_tool_settings=None)`.
- `ToolboxToolset(server_url=..., toolset_name=None, tool_names=None, auth_token_getters=None, bound_params=None, credentials=None, additional_headers=None)` uses the MCP Toolbox SDK (`google-adk[toolbox]`).

Built-in model/native tools include `google_search`, `enterprise_web_search`, `url_context`, `VertexAiSearchTool`, and `DiscoveryEngineSearchTool`; confirm model/backend support before combining multiple built-in tools.

## A2A Helpers

Install extra: `google-adk[a2a]` supplies `a2a-sdk`.

Imports:

```python
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.a2a.utils.agent_card_builder import AgentCardBuilder
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
```

`to_a2a(agent, *, host="localhost", port=8000, protocol="http", agent_card=None, push_config_store=None, task_store=None, runner=None, lifespan=None, agent_executor_factory=None)` converts a `BaseAgent` or `Workflow` into a Starlette app. If no runner is supplied it creates in-memory artifact, session, memory, and credential services.

`AgentCardBuilder(agent=..., rpc_url=None, capabilities=None, doc_url=None, provider=None, agent_version=None, security_schemes=None).build()` derives an A2A `AgentCard` from agent/workflow descriptions, tools, examples, planner, code executor, and child nodes.

`RemoteA2aAgent` is used as a remote sub-agent in an agent tree; network hosting and deployment commands route to `cli-configuration-deployment`.

## Optional Extras Map

Base install can import core tools, but these extras may be needed:

- `google-adk[mcp]`: `mcp` SDK, `McpToolset`, MCP sessions and resources.
- `google-adk[extensions]`: Anthropic/LiteLLM model extras, retrieval helpers, `load_web_page`, CrewAI/LangChain-style integrations, Docker/Kubernetes/sandbox helpers, Firestore service support, Toolbox SDK dependency.
- `google-adk[gcp]`: Google Cloud clients for BigQuery, Bigtable, Spanner, Pub/Sub, GCS, Discovery Engine, Agent Engine, telemetry exporters, and related cloud integrations.
- `google-adk[tools]`: `google-api-python-client` for Google API discovery-based toolsets.
- `google-adk[a2a]`: A2A SDK for A2A app and remote agent helpers.
- `google-adk[agent-identity]`: Google agent identity and IAM connector credentials.
- `google-adk[slack]`: Slack Bolt integration.
- `google-adk[toolbox]`: MCP Toolbox SDK.
- `google-adk[db]`: SQLAlchemy and Spanner SQLAlchemy support; persistence details route to `runtime-services`.
- `google-adk[eval]`: evaluation dependencies; route evaluation design to `evaluation-debugging`.

## Safe Validation Checks

Run only local probes before network/credential work:

```bash
python skills/adk-python/sub-skills/tools-and-integrations/scripts/inspect_tooling.py --help
python skills/adk-python/sub-skills/tools-and-integrations/scripts/inspect_tooling.py
python - <<'PY'
from google.adk.tools import FunctionTool

def ping(name: str) -> dict[str, str]:
  """Return a greeting."""
  return {"hello": name}

print(FunctionTool(ping).name)
PY
```

The bundled script intentionally does not create sessions, open network connections, read credential files, or start MCP subprocesses.
