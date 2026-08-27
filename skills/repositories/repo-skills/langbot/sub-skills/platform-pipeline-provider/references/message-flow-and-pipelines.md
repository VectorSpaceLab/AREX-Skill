# Message Flow and Pipelines

## Runtime Graph

LangBot message processing is best understood as:

```text
Platform adapter
  -> RuntimeBot
  -> MessageAggregator
  -> QueryPool
  -> Controller
  -> RuntimePipeline
  -> PipelineStage chain
  -> RequestRunner / ToolManager / PluginRuntimeConnector / BoxService
  -> adapter response
```

HTTP and MCP management surfaces are parallel entry points into service-layer
state; user messages normally enter via platform adapters or embed/WebSocket
surfaces.

## Pipeline Ownership

Pipeline code owns conversation processing and should contain business logic
that is independent of platform vendor payloads. Important pieces:

- `QueryPool` stores pending and cached in-flight queries.
- `Controller` enforces global and per-session concurrency.
- `RuntimePipeline` materializes database config into stage containers.
- Stage families include response rules, banned sessions, content filters,
  preprocessors, rate limits, message truncation, long text, response back,
  command handling, and wrappers.
- `ChatMessageHandler` is the main LLM/tool/plugin conversation handler.

When adding a stage, use the existing preregistration/decorator patterns rather
than creating a parallel registry.

## Message Aggregation

LangBot can merge multiple user messages before one pipeline turn. If replies
feel delayed or grouped unexpectedly, inspect pipeline aggregation config and
session identity before blaming the provider. HTTP Bot intentionally relies on
this pipeline-native N-to-1 behavior.

## Validation Choices

- Fake message flow smoke tests validate factory/provider/platform basics.
- Pipeline full-flow integration tests validate stage interactions with fake
  providers, no real LLM credentials.
- Focused stage unit tests are best for small behavior changes.
