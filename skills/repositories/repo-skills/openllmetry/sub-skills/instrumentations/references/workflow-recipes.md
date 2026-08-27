# Workflow Recipes

Use this reference when you need to pick the right wrapper path, wire it into an app that already has OpenTelemetry providers, or verify that an instrumentation package is doing anything at all.

See also:

- [Instrumentation catalog](instrumentation-catalog.md)
- [Troubleshooting](troubleshooting.md)

## Choose the path first

| Situation | Pick | Why |
| --- | --- | --- |
| You already own the tracer, meter, or logger provider | Direct instrumentor | Keeps your existing provider stack intact and lets you instrument only one package. |
| You want the SDK to enable several wrappers from the installed package set | SDK `Instruments` selection | One call can activate many package families and skip missing ones. |
| You want to avoid nested provider calls being wrapped twice | Suppression key or `block_instruments` | Prevents duplicate spans, metrics, or events. |

## Direct wrapper recipe: custom tracer provider

Use a direct instrumentor when your application already owns the OpenTelemetry provider stack.

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.instrumentation.openai import OpenAIInstrumentor

provider = TracerProvider()
provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
trace.set_tracer_provider(provider)

OpenAIInstrumentor().instrument(tracer_provider=provider)

# Build or reuse the OpenAI client after instrumentation.
```

Notes:

- Create client objects after calling `.instrument()`.
- If you also want metrics or logs, pass `meter_provider` and `logger_provider` as well.
- If the app needs content as span events instead of span attributes, construct the instrumentor with the package's `use_attributes=False` switch and provide a logger provider.

## Direct wrapper recipes by category

### Provider / router

```python
from opentelemetry.instrumentation.openai import OpenAIInstrumentor
from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor
from opentelemetry.instrumentation.bedrock import BedrockInstrumentor
from opentelemetry.instrumentation.litellm import LiteLLMInstrumentor

OpenAIInstrumentor().instrument()
AnthropicInstrumentor().instrument()
BedrockInstrumentor().instrument()
LiteLLMInstrumentor().instrument()
```

### Vector DB

```python
from opentelemetry.instrumentation.chromadb import ChromaInstrumentor
from opentelemetry.instrumentation.qdrant import QdrantInstrumentor
from opentelemetry.instrumentation.pinecone import PineconeInstrumentor

ChromaInstrumentor().instrument()
QdrantInstrumentor().instrument()
PineconeInstrumentor().instrument()
```

### Framework / agent / protocol

```python
from opentelemetry.instrumentation.langchain import LangchainInstrumentor
from opentelemetry.instrumentation.llamaindex import LlamaIndexInstrumentor
from opentelemetry.instrumentation.mcp import McpInstrumentor
from opentelemetry.instrumentation.openai_agents import OpenAIAgentsInstrumentor

LangchainInstrumentor().instrument()
LlamaIndexInstrumentor().instrument()
McpInstrumentor().instrument()
OpenAIAgentsInstrumentor().instrument()
```

### Local model / service

```python
from opentelemetry.instrumentation.ollama import OllamaInstrumentor
from opentelemetry.instrumentation.transformers import TransformersInstrumentor

OllamaInstrumentor().instrument()
TransformersInstrumentor().instrument()
```

## SDK selection recipe

Use the SDK when you want OpenLLMetry to choose the installed instrumentations for you.

```python
from traceloop.sdk import Traceloop
from traceloop.sdk.instruments import Instruments

Traceloop.init(
    instruments={
        Instruments.OPENAI,
        Instruments.LANGCHAIN,
        Instruments.QDRANT,
        Instruments.MCP,
    },
    block_instruments={
        Instruments.REQUESTS,
        Instruments.URLLIB3,
    },
    disable_batch=True,
    use_attributes=False,
)
```

Use this pattern when:

- the app does not already own the provider stack,
- you want one call to select multiple instrumented libraries, or
- you want the SDK to skip packages that are not installed.

Do not mix this pattern with a direct wrapper for the same client unless you intentionally want duplicate spans or metrics.

## Content, event, and suppression mode

### Content as span attributes

- Default path for most packages.
- Prompts, completions, and embeddings stay on the span.
- Best for simple tracing and most offline inspection.

### Content as log events

- Some instrumentors expose `use_attributes=False` / `use_legacy_attributes=False`.
- This sends message content to OTEL log events instead of span attributes.
- You need a logger provider/exporter if you want to see those events.

### Content disabled entirely

- Set `TRACELOOP_TRACE_CONTENT=false` when the package honors the content flag.
- Use this when you want spans but no payload capture.

### Nested language-model suppression

Use the language-model suppression key when a framework would otherwise trigger nested provider instrumentation and double count the same call.

```python
from opentelemetry import context as context_api
from opentelemetry.semconv_ai import SUPPRESS_LANGUAGE_MODEL_INSTRUMENTATION_KEY

ctx = context_api.set_value(SUPPRESS_LANGUAGE_MODEL_INSTRUMENTATION_KEY, True)
token = context_api.attach(ctx)
try:
    # Call the nested provider or framework action here.
    pass
finally:
    context_api.detach(token)
```

## Validation steps

1. Run [scripts/inspect_instrumentors.py](../scripts/inspect_instrumentors.py) with `--help` and `--repo-root` to confirm the package mapping you expect.
2. Install or activate only the target client libraries you actually need.
3. Instrument before you build client objects.
4. Exercise the code path once and inspect spans, metrics, or events with an in-memory or console exporter.
5. For VCR-backed integrations, replay existing cassettes before trying to record new traffic.
6. For local services, make sure the daemon or model cache is already running or populated.

## When a direct example still emits nothing

- The target client may have been imported before instrumentation.
- The wrong wrapper package may be installed for the client version.
- A suppression key or `TRACELOOP_TRACE_CONTENT=false` may be disabling content capture.
- The package may require a logger or meter provider before its events or metrics become visible.
- The client library may need a version that matches the cataloged support range.
