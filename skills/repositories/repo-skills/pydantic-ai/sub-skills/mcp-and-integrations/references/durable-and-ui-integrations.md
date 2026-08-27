# Durable and UI Integrations

Use this reference when an agent needs to run inside a durable workflow backend, expose an A2A/ASGI service, or translate Pydantic AI event streams to AG-UI, Vercel AI, or built-in web UI protocols.

## Durable Execution Overview

Pydantic AI provides public-interface wrappers for durable execution engines. These wrappers preserve agent semantics across workflow boundaries and wrap models/toolsets/MCP where needed so external calls become engine-managed activities/tasks/steps.

| Backend | Primary APIs | Use when | Hard requirements |
| --- | --- | --- | --- |
| Temporal | `TemporalAgent`, `PydanticAIPlugin`, `AgentPlugin`, `TemporalRunContext`, `PydanticAIWorkflow` | Long-running workflows, replay, activity isolation, worker deployment. | Temporal SDK/runtime, worker/client setup, stable agent name, stable leaf toolset IDs. |
| Prefect | `PrefectAgent`, `PrefectModel`, `PrefectFunctionToolset`, `PrefectMCPServer`, `DEFAULT_PYDANTIC_AI_CACHE_POLICY` | Prefect flows/tasks and cached task semantics. | Prefect installed/configured, stable agent name, runtime model set at construction inside flows. |
| DBOS | `DBOSAgent`, `DBOSModel`, `DBOSMCPServer`, `StepConfig`, `DBOSParallelExecutionMode` | DBOS workflows/steps, human-in-the-loop workflow events. | DBOS installed/configured/launched, stable agent name, model set at construction for workflow runs. |
| Restate or external durable SDKs | External integration package plus Pydantic AI public APIs | Deployment standardizes on another durable engine. | Follow the same identity/serialization/lifecycle rules as official wrappers. |

Durable wrappers are not just convenience decorators. They constrain what can be dynamic at run time because deterministic replay and activity scheduling need stable names, IDs, and serializable boundaries.

## Durable Design Rules

Before wrapping an agent:

- Give the base agent a unique stable `name`; wrappers use it for activities, flows, workflows, steps, and instance registration.
- Set the model at agent construction when running inside durable workflows; arbitrary non-wrapper model overrides inside a workflow are rejected.
- Give leaf toolsets stable `id` values. MCP servers/toolsets and dynamic toolsets particularly need stable IDs for activity/task names.
- Prefer wrapper-provided model/toolset conversions over manual network calls inside workflow code.
- Keep deps, metadata, tool args, output, and deferred-tool results serializable for the backend.
- Configure event streaming as a handler where the backend requires it; several wrappers reject `run_stream_events()` or streaming inside workflow code.
- Treat MCP tool list caches carefully. Durable wrappers may cache tool definitions across activities/steps; disable all relevant caches when a server mutates tools during a workflow.

## Temporal Notes

`TemporalAgent` wraps an agent and registers activities for model requests and toolset operations. `PydanticAIPlugin` configures the Temporal worker with Pydantic payload conversion and sandbox passthrough modules for Pydantic AI, provider SDKs, FastMCP/MCP, HTTP clients, Logfire, and related dependencies.

Important restrictions:

- `agent.run_sync()` cannot be used inside a Temporal workflow; use `await agent.run()`.
- `agent.run_stream()` and `agent.run_stream_events()` are limited inside workflows; use `event_stream_handler` on the agent and `agent.run()` where streaming observations are needed.
- `agent.iter()` is restricted inside workflow code when it would bypass durable-managed execution.
- Toolsets, tools, native tools, and model overrides cannot be set dynamically inside Temporal workflow code; set them on the wrapped agent at construction time.
- Non-Pydantic payload converters may be replaced or warned about; use Pydantic-compatible converters for clean serialization.

## Prefect Notes

`PrefectAgent` wraps `run`, model requests, function toolsets, and MCP servers as Prefect flows/tasks where possible.

Important restrictions:

- A unique agent `name` becomes the flow/task name prefix.
- `run_stream()` is not available inside a Prefect flow; use event stream handlers and `run()` when observing events.
- `run_stream_events()` is restricted inside Prefect flows.
- Non-Prefect model overrides inside a flow are rejected; configure the wrapped model at construction.
- `DEFAULT_PYDANTIC_AI_CACHE_POLICY` and Prefect cache helpers strip or replace unstable inputs so task caching does not depend on unserializable runtime objects.

## DBOS Notes

`DBOSAgent` wraps `run` as DBOS workflows and model/MCP calls as DBOS steps where appropriate. It can run tool calls with a configured `DBOSParallelExecutionMode` such as ordered parallel events or sequential behavior.

Important restrictions:

- A unique agent `name` is required for DBOS configured instance registration.
- A model must be set on the agent before wrapping; setting a non-DBOS model at run time inside workflows is rejected.
- `run_stream()` is not available inside a DBOS workflow; use event handlers and `run()`.
- `run_stream_events()` is not available with DBOS; use an `event_stream_handler` on the agent and `run()` instead.
- Some function tools are not automatically wrapped as DBOS steps; define DBOS steps explicitly when tool execution itself must be durable.
- Human-in-the-loop tools can use DBOS workflow events to exchange `DeferredToolRequests` and `DeferredToolResults`.

## A2A Integration

Current guidance is to use the external `fasta2a` Pydantic AI bridge directly for new code. The older `Agent.to_a2a()` / `pydantic_ai._a2a.agent_to_a2a` path is deprecated in this checkout and points users to `fasta2a[pydantic-ai]`.

Conceptual mapping:

- A2A task/context storage persists task state and conversation context.
- Pydantic AI message history is stored in context storage so subsequent A2A tasks can continue the conversation.
- String outputs become text artifacts.
- Structured outputs become data artifacts with serialized result data and schema metadata.
- A2A-compliant task history contains visible messages/artifacts, while full Pydantic AI history can preserve tool calls and provider metadata internally.

Use A2A when a server must expose an agent to other agents through the A2A protocol. Do not use it for ordinary HTTP chat endpoints where AG-UI, Vercel AI, or the built-in web UI fits better.

## UI Adapter Selection

| Need | Prefer | Notes |
| --- | --- | --- |
| Existing AG-UI frontend with streaming events, activities, interrupts, and frontend tools | `pydantic_ai.ui.ag_ui.AGUIAdapter` | Requires AG-UI and Starlette dependencies. Deprecated top-level `pydantic_ai.ag_ui` wrappers should be replaced. |
| Vercel AI SDK UI messages and streaming chunks | `pydantic_ai.ui.vercel_ai.VercelAIAdapter` | `sdk_version=6` enables tool approval streaming; version 5 remains the default for compatibility. |
| Quick hosted web chat around one agent | `Agent.to_web()` / web app helpers | Requires web dependencies and an ASGI server; runtime may fetch/cache UI HTML unless a local `html_source` is supplied. |
| CLI web chat | `clai web` | Route command-line operation to `../cli-and-apps/SKILL.md`. |

All UI adapters transform frontend request bodies into `Agent.run_stream_events()` arguments, then transform Pydantic AI events into protocol-specific streaming responses. They are protocol adapters, not authentication, authorization, or persistence layers.

## UI Security Defaults

Keep these defaults unless the frontend is trusted and audited:

- `manage_system_prompt='server'`: server-side system prompt is authoritative; client-supplied system prompt parts are stripped and server prompt is reinjected.
- `allowed_file_url_schemes=frozenset({'http', 'https'})`: non-HTTP file URLs can cause provider/server credentials to fetch protected cloud/internal resources.
- `allowed_file_url_force_download=frozenset()`: client requests for server-side download or local-network access are reset unless explicitly allowed.
- `preserve_file_data=False`: client-uploaded file references are dropped so a hostile frontend cannot cause the server/provider to read arbitrary stored files.

If the frontend is trusted and file round-trip fidelity matters, enable `preserve_file_data=True` deliberately and document why the trust boundary is acceptable.

## AG-UI Adapter Notes

Use `from pydantic_ai.ui.ag_ui import AGUIAdapter` for new code. The compatibility module `pydantic_ai.ag_ui` emits a deprecation warning and its helper functions are being removed.

AG-UI specifics:

- `ag_ui_version` controls event shape. Older protocol versions use `THINKING_*`; newer versions use `REASONING_*` with encrypted metadata and typed multimodal input.
- `AGUIAdapter.toolset` exposes frontend-provided tools as an external toolset for deferred frontend execution.
- `AGUIAdapter.deferred_tool_results` maps interrupt resume entries to approval results and denies malformed or missing approvals by default.
- `RunAgentInput.threadId` becomes the Pydantic AI `conversation_id`.
- `StateDeps` can carry frontend state into agent dependencies when using stateful UI flows.
- Activity message types prefixed with `pydantic_ai_` are reserved for internal file/message round-trip behavior.

## Vercel AI Adapter Notes

Use `from pydantic_ai.ui.vercel_ai import VercelAIAdapter` for Vercel AI UI message protocols.

Vercel specifics:

- `sdk_version=5` is the compatibility default.
- `sdk_version=6` enables tool approval streaming and extraction of approval responses into `DeferredToolResults`.
- The top-level request `id` becomes the Pydantic AI `conversation_id`.
- Message IDs are generated from provider response IDs, run IDs, or deterministic UUID5 fallbacks.
- Provider metadata is round-tripped in message metadata where the protocol supports it.

## Built-in Web UI Notes

The web UI creates a Starlette app with API routes and a chat UI page. Use it for a quick application shell or demo, then graduate to AG-UI/Vercel/custom APIs for production-specific UX.

Operational notes:

- Install web dependencies before using web app helpers.
- Pass an explicit `models=` list or mapping when users should choose among models.
- Native tools configured on the agent are included; additional UI-selectable native tools can be passed separately.
- The `memory` native tool is not supported through the built-in web UI path; configure memory directly on the agent if needed.
- Provide a local `html_source` for offline or enterprise environments; the default path may fetch and cache UI HTML.

## Integration Test Strategy

Use deterministic local checks first:

- Import-check optional groups with `scripts/integration_import_check.py`.
- Use `TestModel` for agent behavior when provider credentials are not part of the task.
- Use in-process FastMCP servers for MCP tool/resource behavior rather than external services.
- Use Starlette request objects or adapter parsing directly for UI mapping tests.
- Skip durable backend tests unless the corresponding service/runtime is installed and configured.
