# Tools and Integrations Workflows

These recipes are self-contained patterns for future agents using `google-adk` 2.3.0. They avoid network and credential side effects unless a user explicitly supplies the required runtime configuration.

## Choose the Tool Form

Use this decision order:

1. **Plain callable** for simple local logic with typed parameters and a docstring.
2. **`FunctionTool`** when confirmation, explicit wrapping, or a reusable tool object is needed.
3. **`LongRunningFunctionTool`** when the first call starts work, requests input, or returns a pending external operation.
4. **`BaseTool`** when the tool needs custom declarations, request preprocessing, response scheduling, or no normal function declaration.
5. **`BaseToolset`** when one integration exposes many tools, needs filtering/prefixing, or owns shared clients/sessions.
6. **Integration toolset** (`McpToolset`, `OpenAPIToolset`, Google/cloud toolsets) when the tool source is external.

## Function Tool Recipe

```python
from google.adk import Agent
from google.adk.tools import ToolContext


def lookup_order(order_id: str, tool_context: ToolContext) -> dict[str, str]:
  """Look up an order by id."""
  cached = tool_context.state.get(f"order:{order_id}")
  if cached:
    return {"status": "cached", "order": cached}
  return {"error": f"Order {order_id} is not loaded."}


root_agent = Agent(
    name="orders_agent",
    model="gemini-3.5-flash",
    instruction="Use tools for order lookups and explain recoverable errors.",
    tools=[lookup_order],
)
```

Validation checklist:

- Function has a docstring; ADK uses it as the tool description.
- Model-visible args are simple typed values or Pydantic models.
- `tool_context` is named exactly `tool_context` and annotated with `ToolContext` when used.
- Return value is JSON-serializable.
- Recoverable domain failures return `{"error": "..."}`; unexpected programming errors can raise and be handled by `on_tool_error_callback`.

## Confirmation Recipe

Use automatic confirmation when every call to a tool is sensitive:

```python
from google.adk import Agent
from google.adk.tools import FunctionTool, ToolContext


def close_account(account_id: str, tool_context: ToolContext) -> dict[str, str]:
  """Close an account after confirmation."""
  return {"status": "closed", "account_id": account_id}


root_agent = Agent(
    name="account_agent",
    model="gemini-3.5-flash",
    instruction="Confirm destructive account actions before tool execution.",
    tools=[FunctionTool(func=close_account, require_confirmation=True)],
)
```

Use explicit confirmation when only some arguments are sensitive:

```python
from google.adk.tools import ToolContext


def transfer_funds(amount: float, recipient: str, tool_context: ToolContext):
  """Transfer funds after confirmation for large transfers."""
  if amount >= 100 and not tool_context.tool_confirmation:
    tool_context.request_confirmation(
        hint=f"Confirm transfer of ${amount:.2f} to {recipient}.",
        payload={"amount": amount, "recipient": recipient},
    )
    tool_context.actions.skip_summarization = True
    return {"error": "This tool call requires confirmation."}
  if amount >= 100 and not tool_context.tool_confirmation.confirmed:
    return {"error": "Transfer rejected by user."}
  return {"status": "scheduled", "amount": amount, "recipient": recipient}
```

Common checks:

- `tool_context.request_confirmation()` only works during a real tool call because `function_call_id` must be set.
- The resumed call has `tool_context.tool_confirmation.confirmed` and optional `payload`.
- A confirmation request is not the same as a long-running external job; use `LongRunningFunctionTool` for pending work.

## Long-Running and Human Input Recipe

```python
from typing import Any

from google.adk import Agent
from google.adk.tools import LongRunningFunctionTool, ToolContext


def start_approval(reason: str, amount: float, tool_context: ToolContext) -> dict[str, Any]:
  """Start an approval request and return a pending ticket."""
  return {
      "status": "pending",
      "ticket_id": "approval-001",
      "reason": reason,
      "amount": amount,
  }


root_agent = Agent(
    name="approval_agent",
    model="gemini-3.5-flash",
    instruction="Start approval for large requests and wait for external completion.",
    tools=[LongRunningFunctionTool(func=start_approval)],
)
```

Use `request_input` when the agent must pause and ask the user for missing information:

```python
from google.adk import Agent
from google.adk.tools import request_input

root_agent = Agent(
    name="intake_agent",
    model="gemini-3.5-flash",
    instruction="Ask for missing required fields before using other tools.",
    tools=[request_input],
)
```

Long-running validation:

- The tool declaration warns the model not to call the tool again after a pending status.
- The tool returns a stable identifier (`ticket_id`, `operation_id`, or equivalent) when external completion is expected.
- A separate safe polling/status tool is preferable to re-calling the starter tool.
- If this is workflow-node HITL rather than tool-level HITL, route to `workflow-orchestration`.

## Tool Error Callback Recipe

Use `on_tool_error_callback` when the user asks why an exception is "swallowed" or transformed. ADK runs plugin `on_tool_error_callback` first, then agent callbacks. If any callback returns a dictionary, ADK emits that dictionary as the function response; if all return `None`, the original exception is raised.

```python
from typing import Any

from google.adk import Agent
from google.adk.tools import BaseTool, ToolContext


async def tool_error_to_response(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
    error: Exception,
) -> dict[str, str] | None:
  if tool.name == "fragile_lookup":
    return {"error": f"fragile_lookup failed: {error}"}
  return None


def fragile_lookup(key: str) -> dict[str, str]:
  """Look up a key and raise on missing backend state."""
  raise RuntimeError("backend unavailable")


root_agent = Agent(
    name="debuggable_agent",
    model="gemini-3.5-flash",
    instruction="Explain tool failures and ask for retry instructions.",
    tools=[fragile_lookup],
    on_tool_error_callback=tool_error_to_response,
)
```

If a tool itself returns `{"error": "..."}`, it is already a function response and does not require the exception callback path.

## Agent-as-Tool Recipe

```python
from google.adk import Agent
from google.adk.tools import AgentTool


helper_agent = Agent(
    name="research_helper",
    description="Looks up internal research notes and summarizes them.",
    model="gemini-3.5-flash",
    instruction="Answer only research-note lookup questions.",
)

root_agent = Agent(
    name="main_agent",
    model="gemini-3.5-flash",
    instruction="Delegate research-note questions to the helper tool.",
    tools=[AgentTool(agent=helper_agent, skip_summarization=True)],
)
```

Guidance:

- The child agent name becomes the tool name, so choose a stable name.
- The child `description` should say when to call it.
- Use `include_plugins=False` if parent observability or retry plugins should not affect the child run.
- If the goal is normal sub-agent delegation via `sub_agents`, route construction guidance to `agent-construction`.

## Transfer Tool Recipe

```python
from google.adk import Agent
from google.adk.tools import TransferToAgentTool

root_agent = Agent(
    name="router_agent",
    model="gemini-3.5-flash",
    instruction="Use transfer_to_agent only for listed specialist agents.",
    tools=[TransferToAgentTool(agent_names=["billing_agent", "support_agent"])],
)
```

Use this for explicit tool-controlled transfer with enum validation. Use normal `sub_agents` routing when ADK's agent delegation is sufficient.

## Custom Toolset Recipe

```python
from google.adk.tools import BaseTool, BaseToolset, FunctionTool


def ping_service(name: str) -> dict[str, str]:
  """Return a synthetic ping response."""
  return {"service": name, "status": "ok"}


class LocalToolset(BaseToolset):
  async def get_tools(self, readonly_context=None) -> list[BaseTool]:
    tools = [FunctionTool(ping_service)]
    return [tool for tool in tools if self._is_tool_selected(tool, readonly_context)]

  async def close(self) -> None:
    return None
```

Toolset checklist:

- Implement `get_tools()` as async.
- Respect `tool_filter` by calling `_is_tool_selected()`.
- Use `tool_name_prefix` through `get_tools_with_prefix()` when an agent may combine several toolsets with overlapping tool names.
- Release owned clients/sessions/subprocesses in `close()`.
- Override `get_auth_config()` only when ADK must populate credentials before `get_tools()` or tool execution.

## MCP Toolset Recipe

First validate optional extra availability:

```bash
python skills/adk-python/sub-skills/tools-and-integrations/scripts/inspect_tooling.py
```

Then wire MCP only after the environment has `google-adk[mcp]` and a known server command or URL:

```python
from google.adk import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="python",
            args=["-m", "my_safe_mcp_server"],
        ),
        timeout=10.0,
    ),
    tool_filter=["search", "read_item"],
    tool_name_prefix="knowledge",
)

root_agent = Agent(
    name="mcp_agent",
    model="gemini-3.5-flash",
    instruction="Use MCP tools only for knowledge-base lookups.",
    tools=[mcp_toolset],
)
```

Remote OAuth-protected MCP shape:

```python
from fastapi.openapi.models import OAuth2, OAuthFlowAuthorizationCode, OAuthFlows
from google.adk.auth.auth_credential import AuthCredential, AuthCredentialTypes, OAuth2Auth
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool import McpToolset

auth_scheme = OAuth2(
    flows=OAuthFlows(
        authorizationCode=OAuthFlowAuthorizationCode(
            authorizationUrl="https://example.com/oauth/authorize",
            tokenUrl="https://example.com/oauth/token",
            scopes={"read": "Read access"},
        )
    )
)
auth_credential = AuthCredential(
    auth_type=AuthCredentialTypes.OAUTH2,
    oauth2=OAuth2Auth(client_id="...", client_secret="..."),
)
mcp_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(url="https://mcp.example.com/mcp"),
    auth_scheme=auth_scheme,
    auth_credential=auth_credential,
    credential_key="example_mcp_oauth",
)
```

MCP safety boundaries:

- Do not start arbitrary `npx`, `uvx`, shell, or Docker MCP servers unless the user approves that command.
- Use `StdioConnectionParams` instead of raw `StdioServerParameters` when timeout matters.
- For `No module named 'mcp'`, install/select an environment with `google-adk[mcp]`; do not rewrite imports to private source paths.
- For remote servers, keep tokens in credential services, environment variables, or caller-supplied secrets; do not embed credentials in skill content.
- Call `await toolset.close()` for manually managed toolsets outside normal runner lifecycle.

## OpenAPI Toolset Recipe

```python
from google.adk import Agent
from google.adk.tools.openapi_tool.openapi_spec_parser.openapi_toolset import OpenAPIToolset

openapi_toolset = OpenAPIToolset(
    spec_str=openapi_yaml_string,
    spec_str_type="yaml",
    tool_filter=["listBookings", "createBooking"],
    tool_name_prefix="hotel",
    preserve_property_names=True,
)

root_agent = Agent(
    name="hotel_agent",
    model="gemini-3.5-flash",
    instruction="Use hotel API tools for booking operations.",
    tools=[openapi_toolset],
)
```

With bearer/API-key style auth, create `AuthCredential` and `AuthScheme` through `google.adk.tools.openapi_tool.auth.auth_helpers` when possible. With OAuth/OIDC, pass `auth_scheme`, `auth_credential`, and a stable `credential_key` so ADK/client credential flow can resume.

OpenAPI validation:

- Confirm the spec parses locally before running an agent.
- Use `tool_filter` to avoid exposing destructive or irrelevant endpoints.
- Use `tool_name_prefix` when combining multiple APIs.
- Use `preserve_property_names=True` if the backend rejects snake_case-converted parameter names.
- Use `ssl_verify` or `httpx_client_factory` for enterprise TLS/proxy/signing requirements.

## Google API and Cloud Toolsets Recipe

Google API discovery toolsets:

```python
from google.adk import Agent
from google.adk.tools.google_api_tool.google_api_toolsets import CalendarToolset

calendar_tools = CalendarToolset(
    client_id="...",
    client_secret="...",
    tool_filter=["calendar_events_list", "calendar_events_insert"],
    tool_name_prefix="calendar",
)

root_agent = Agent(
    name="calendar_agent",
    model="gemini-3.5-flash",
    instruction="Use calendar tools only after the user has authorized access.",
    tools=[calendar_tools],
)
```

Cloud toolsets:

- BigQuery discovery convenience: `google.adk.tools.google_api_tool.google_api_toolsets.BigQueryToolset`.
- ADK data/cloud toolsets: `DataAgentToolset`, `PubSubToolset`, `BigtableToolset`, `SpannerToolset`, `SpannerAdminToolset`.
- Enterprise/API toolsets: `APIHubToolset`, `ApplicationIntegrationToolset`, `ToolboxToolset`.

Cloud integration checklist:

- Install/select the matching extra (`tools`, `gcp`, `extensions`, `toolbox`, or `agent-identity`).
- Identify credential mode: OAuth client, service account object, Application Default Credentials, user auth flow, API key, or connector resource.
- Filter tools to least privilege before exposing them to a model.
- Keep destructive admin actions out of default tool lists unless the user explicitly requests and confirmation is added.
- Run local import/signature probes before cloud calls; cloud calls may need billing, IAM, network, and quota.

## A2A Exposure and Remote Agent Recipe

Converting a local ADK agent or workflow into an A2A Starlette app requires `google-adk[a2a]`:

```python
from google.adk import Agent
from google.adk.a2a.utils.agent_to_a2a import to_a2a

root_agent = Agent(
    name="public_agent",
    description="Answers public questions over A2A.",
    model="gemini-3.5-flash",
    instruction="Answer concise public questions.",
)

app = to_a2a(root_agent, host="localhost", port=8000)
```

Using a remote A2A agent in an agent tree:

```python
from google.adk import Agent
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH, RemoteA2aAgent

remote_agent = RemoteA2aAgent(
    name="prime_agent",
    description="Checks whether numbers are prime.",
    agent_card=f"http://localhost:8001/a2a/prime{AGENT_CARD_WELL_KNOWN_PATH}",
)

root_agent = Agent(
    name="math_router",
    model="gemini-3.5-flash",
    instruction="Delegate prime checks to prime_agent.",
    sub_agents=[remote_agent],
)
```

A2A boundaries:

- Hosting `app` with `uvicorn` and deployment commands route to `cli-configuration-deployment`.
- Persistent A2A task stores and database lifecycle route to `runtime-services`.
- A2A import errors usually mean `google-adk[a2a]` is missing.

## Difficult Case: MCP Import Failure

When the user says "I added an MCP toolset and get `No module named 'mcp'`":

1. Run `inspect_tooling.py` to confirm core ADK imports work and `mcp` is absent.
2. Explain that base `google-adk` does not include MCP; select/install `google-adk[mcp]` in the active runtime.
3. Keep the code import path as `from google.adk.tools.mcp_tool import McpToolset`; do not import from the source checkout.
4. Choose the connection type: stdio with an approved server command, SSE, or Streamable HTTP.
5. Add `tool_filter` and `tool_name_prefix` before exposing server tools to the model.
6. If the server needs auth, configure `auth_scheme`, `auth_credential`, and `credential_key`; avoid embedding tokens.
7. Provide a safe fallback if MCP remains unavailable, such as a local `FunctionTool` with limited read-only behavior.

## Difficult Case: Tool Failure Looks Swallowed

When the user says "my tool failed but the agent continued":

1. Determine whether the tool returned `{"error": "..."}` or raised an exception.
2. If it returned `{"error": "..."}`, ADK emitted a normal function response that the model may summarize or recover from.
3. If it raised, check plugin `on_tool_error_callback` and agent `on_tool_error_callback`; any non-`None` dictionary replaces the exception with a function response.
4. Check `after_tool_callback` for response replacement after successful or callback-handled execution.
5. Inspect event parts for `function_call` followed by `function_response` to see exactly what the model saw.
6. If exceptions should fail the run, make error callbacks return `None` for that tool.
7. If user-visible recovery is desired, return a dictionary with an `error` field and a clear retry/credential/action hint.
