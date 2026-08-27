# A2A Workflows

LiteLLM supports A2A agents through proxy management/discovery endpoints, direct A2A JSON-RPC forwarding, and LiteLLM route interception for model names prefixed with `a2a/`. Direct SDK examples require the optional `a2a-sdk` package.

## Register or configure agents

Agents can be configured in proxy config or managed through the proxy agent endpoints. An agent needs a stable `agent_name`, an A2A agent card, and optional LiteLLM controls.

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
        pushNotifications: false
      defaultInputModes: [text]
      defaultOutputModes: [text]
      skills:
        - id: research
          name: Research
          description: Research public sources
          tags: [research]
    litellm_params:
      require_trace_id_on_calls_to_agent: false
    object_permission:
      mcp_servers: []
```

Agent card fields mirror the A2A card shape: `protocolVersion`, `name`, `description`, `url`, `version`, `capabilities`, input/output modes, and `skills`. Security schemes, provider metadata, additional interfaces, and authenticated extended cards can be included when the upstream agent advertises them.

## Discover and manage agents

Proxy endpoints include:

- `GET /v1/agents`: list agents allowed for the caller. `?health_check=true` filters out agents with unreachable card URLs.
- `GET /v1/agents/{agent_id}`: fetch a single agent.
- `POST /v1/agents`, `PATCH /v1/agents/{agent_id}`, and delete-style management routes: admin-only write operations.
- Public agent grouping can mark configured agents public through LiteLLM settings, but sensitive fields are redacted for non-admin users.

Example discovery:

```bash
curl -s http://localhost:4000/v1/agents \
  -H 'Authorization: Bearer <litellm-key>'
```

If the caller is not a proxy admin, LiteLLM resolves allowed agents from key object permissions, team object permissions, and access groups. Empty restrictions mean allow all; when both key and team have restrictions, the effective set is their intersection.

## Direct A2A JSON-RPC forwarding

Use `/a2a/{agent_id}` when the client speaks A2A JSON-RPC. LiteLLM looks up the agent by id or name, merges caller identity headers, and forwards JSON-RPC to the upstream agent URL.

Non-streaming example:

```bash
curl -s http://localhost:4000/a2a/research-agent \
  -H 'Authorization: Bearer <litellm-key>' \
  -H 'Content-Type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": "req-1",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"kind": "text", "text": "Summarize the release notes"}],
        "messageId": "msg-1"
      }
    }
  }'
```

Streaming clients should use the A2A streaming method and accept `text/event-stream`. LiteLLM parses upstream SSE `data:` lines and relays JSON-RPC events.

Push notification URLs must be HTTPS and pass URL validation. If an agent sets `require_trace_id_on_calls_to_agent`, inbound calls must include a trace id header accepted by LiteLLM or the request fails with HTTP 400.

## LiteLLM model routing with `a2a/`

The proxy can route ordinary LiteLLM completion/chat calls to an A2A agent when the request model starts with `a2a/`:

```json
{
  "model": "a2a/research-agent",
  "messages": [{"role": "user", "content": "What can this agent do?"}]
}
```

Routing behavior:

- LiteLLM strips the `a2a/` prefix and looks up the remaining value as an agent name.
- The registered agent must have `agent_card_params.url`.
- Non-admin callers must be allowed to use the agent by key/team permissions or access groups.
- If the agent is missing, the route behaves like model-not-found for the requested route.
- If the agent is present but disallowed, the caller receives HTTP 403 with an access-denied message for the agent.

## Provider-specific A2A behavior

LiteLLM contains A2A provider adapters for providers such as Bedrock AgentCore, Pydantic AI agents, Watsonx Orchestrate, and Langflow. Some agents speak A2A natively and expect the full JSON-RPC envelope; others need transformations for non-streaming or streaming responses. Pydantic AI/FastA2A-style servers may reject null optional fields and use root endpoints rather than `/messages`, so prefer LiteLLM's registered agent routing instead of hand-building provider-specific requests.

## Headers and identity

LiteLLM forwards safe caller identity headers to upstream agents:

- `X-LiteLLM-User-Id` when the key has a user id.
- `X-LiteLLM-Team-Id` when the key belongs to a team.
- `X-LiteLLM-Trace-Id` when the request carries `litellm_trace_id`.

Dynamic client-controlled `x-a2a-{agent}-*` style headers are sanitized in provider transformations so callers cannot override reserved `x-litellm-*` identity headers. Configure static agent headers or allowed extra headers at the agent level when an upstream agent requires specific auth or tenant metadata.

## Debugging A2A access denied

When `model: a2a/<agent-name>` fails:

1. Check `GET /v1/agents` with the same key. If the agent is missing for a non-admin caller, inspect key/team object permissions and access groups.
2. Confirm the requested suffix is the registered `agent_name`, not only the human-readable agent card `name`.
3. Confirm `agent_card_params.url` exists and is reachable. Use `GET /v1/agents?health_check=true` to filter unhealthy URL-backed agents.
4. If the route returns model-not-found, the agent may not be registered or the route may not be an A2A-intercepted LiteLLM route.
5. If direct `/a2a/{agent_id}` works but `a2a/<agent-name>` fails, compare agent id versus agent name and check permission resolution for the route.

## Validation checklist

- Confirm `a2a-sdk` is installed before running direct A2A client examples.
- Validate that every configured agent has a card URL, version, capabilities, modes, and at least one skill.
- Exercise both `GET /v1/agents` and the intended invocation path with the same key.
- For non-admin keys, document whether access comes from key object permissions, team object permissions, or access groups.
- Check proxy logs for the exact `a2a/<agent-name>` string and upstream `api_base` selected by LiteLLM.
