# API Reference

## Public entry points

| Surface | What it covers | Notes |
| --- | --- | --- |
| `@strands-agents/sdk` | Agent, tools, models, hooks, middleware, interventions, plugins, memory, session, storage, sandbox, telemetry, retry, conversation manager, and multi-agent orchestration | Main consumer entry point |
| `@strands-agents/sdk/models/bedrock` | Bedrock model provider | Node-friendly provider with prompt caching and guardrail support |
| `@strands-agents/sdk/models/openai` | OpenAI model provider | Supports Responses API by default and Chat Completions via `api: 'chat'` |
| `@strands-agents/sdk/models/anthropic` | Anthropic model provider | Separate provider surface with its own token-count and message mapping rules |
| `@strands-agents/sdk/models/google` | Google model provider | Dedicated Google subpath export |
| `@strands-agents/sdk/models/vercel` | Vercel LanguageModelV3 adapter | Wraps a Vercel-compatible provider instance |
| `@strands-agents/sdk/multiagent` | Graph, Swarm, nodes, state, and multi-agent events | Multi-agent orchestration surface |
| `@strands-agents/sdk/telemetry` | OpenTelemetry setup helpers | `setupTracer()` and `setupMeter()` |
| `@strands-agents/sdk/storage` | Storage interface and implementations | In-memory, local file, and S3 backends |
| `@strands-agents/sdk/sandbox` | Sandbox interface and shell-oriented implementations | Command execution and file I/O abstraction |
| `@strands-agents/sdk/vended-tools` | Built-in tool bundles | Node-safe and browser-aware splits matter here |
| `@strands-agents/sdk/vended-plugins` | Built-in plugins | Context, goal, skills, and related plugin bundles |
| `@strands-agents/sdk/vended-memory-stores` | Bundled memory stores | Specialized memory-store subpaths |

## Agent surface

### Core constructor config

`AgentConfig` is the main object-shape API. The important fields are:

- `model`: a `Model` instance or a Bedrock model ID string
- `messages`, `tools`, `systemPrompt`: conversation setup
- `appState`, `modelState`: application and provider state
- `printer`, `conversationManager`, `contextManager`: runtime behavior
- `plugins`, `retryStrategy`, `interventions`, `structuredOutputSchema`: extensibility and control
- `sessionManager`, `memoryManager`, `storage`, `sandbox`: persistence and execution support
- `traceAttributes`, `name`, `description`, `id`, `toolExecutor`, `checkpointing`

### Main methods and properties

- `initialize()`
- `invoke(args, options?)`
- `stream(args, options?)`
- `asTool(options?)`
- `takeSnapshot(options)` / `loadSnapshot(snapshot)`
- `cancel()` / `cancelSignal`
- `tools`, `toolRegistry`, `toolExecutor`, `metrics`, `isInvoking`, `tool`

### Input and output shapes

- `invoke()` and `stream()` accept strings, content blocks, messages, and interrupt-resume content.
- `stream()` yields `AgentStreamEvent` values and returns `AgentResult`.
- `tool` is a direct-call proxy for registered tools.
- `takeSnapshot()` and `loadSnapshot()` are the persistence boundary for serializable agent state.

### Direct-tool calling

`agent.tool.<name>.invoke()` and `agent.tool.<name>.stream()` bypass model inference.

Use them when you need deterministic tool execution, not when you want the model to choose a tool.

## Tools

### `tool()` factory

`tool()` is the preferred factory when you want one API that accepts either:

- a Zod schema, with typed input validation
- a JSON Schema object, with runtime-agnostic input handling

### Tool classes and types

- `Tool`: abstract streaming base
- `FunctionTool`: wraps sync, async, or async-generator callbacks
- `ZodTool`: validates with Zod and delegates to `FunctionTool`
- `ToolContext`: agent, toolUse, invocationState, and interrupt access
- `ToolStreamEvent`: streamed tool-progress event
- `ToolSpec`: name, description, input schema, and optional output schema
- `ToolChoice`: `auto`, `any`, or specific tool

### Tool rules

- Prefer `interface` for config objects and `type` only for unions.
- Keep tool names valid and stable.
- Use direct tool calls for tests or deterministic helper flows.
- Return JSON-serializable values from tool callbacks.

## Models

### Base contract

`Model` defines:

- `updateConfig(modelConfig)`
- `getConfig()`
- `stream(messages, options?)`
- `countTokens(messages, options?)`
- `estimateUtilization(inputTokens)`
- `stateful` for server-side conversation tracking

### Provider rules

- Translate vendor stop reasons into SDK stop reasons.
- Translate provider throttling and overflow errors into SDK error types.
- Preserve the original error in `cause` when possible.
- Keep provider-specific message conversion private.
- Keep provider credentials and client objects on the provider boundary, not in the consumer-facing config unless the API already expects them.

### Provider-specific entry points

- `BedrockModel` for AWS Bedrock Converse / ConverseStream
- `OpenAIModel` for Responses or Chat Completions
- `AnthropicModel` for Anthropic Messages
- `GoogleModel` for Gemini-style integration
- `VercelModel` for generic LanguageModelV3 providers

## MCP

`McpClient` is the main object for Model Context Protocol servers.

Key responsibilities:

- connect and disconnect
- list tools
- expose filtered and prefixed tool names
- call tools directly or through task polling
- handle elicitation callbacks
- manage optional transport, URL, OAuth, and custom headers

`McpClient.loadServers()` turns a server config into ready clients.

## Hooks, middleware, interventions, plugins

### Hooks

Hook events are the main lifecycle and data-event surface. Important mutable fields include:

- `cancel` on before events
- `retry` on after events
- `selectedTool` and `toolUse` on tool-call events
- `resume` on invocation completion
- `endTurn` on after-tools events

### Middleware

Use middleware when you want to intercept a stage rather than a lifecycle callback.

Stages:

- `InvokeModelStage`
- `ExecuteToolStage`
- `AgentStreamStage` is internal and not part of the stable public contract

### Interventions

`InterventionHandler` returns policy actions such as proceed, deny, guide, confirm, and transform.

Use interventions when you need policy decisions, human approval, or guided redirection rather than low-level event mutation.

### Plugins

Use plugins to bundle reusable hook/tool behavior behind a `name` and init method.

## Memory, session, storage

### Memory

`MemoryManager` manages one or more memory stores and can provide:

- search tools
- add tools
- retrieval injection
- extraction triggers
- direct programmatic `search()` and `add()` access

### Session

`SessionManager` persists snapshots and can work with agents and multi-agent orchestrators.

It owns save-latest behavior and restoration semantics.

### Storage

`Storage` is the minimal bytes-under-key interface.

Shipped implementations include:

- `InMemoryStorage`
- `LocalFileStorage`
- `S3Storage`

Use `namespace()` or a namespaced storage view when a subsystem needs its own prefix.

## Sandbox

`Sandbox` abstracts command execution and file operations.

Use it when a tool needs runtime execution support without binding to a specific backend.

Node defaults are registered separately from the browser-safe barrel.

## Telemetry

`setupTracer()` and `setupMeter()` configure OpenTelemetry once, then `Agent` and the orchestration layers emit traces and metrics automatically.

`AgentTrace` and `AgentMetrics` are the local convenience wrappers exposed by the SDK.

## Multi-agent orchestration

### Graph

Use `Graph` for dependency-driven orchestration:

- nodes plus edges
- explicit source nodes
- concurrency and timeout controls
- interrupt/resume support
- session persistence support

### Swarm

Use `Swarm` for sequential handoff orchestration:

- one agent hands off to the next with structured output
- configurable max-step and timeout limits
- interrupt/resume support
- session persistence support

### Shared node/state types

- `Node`, `AgentNode`, `MultiAgentNode`
- `NodeResult`, `MultiAgentResult`
- `Status`
- `MultiAgentState`

## Maintenance rule of thumb

When you rename, move, or split a public API, update the relevant barrel/export path and the tests that prove the surface still exists.
