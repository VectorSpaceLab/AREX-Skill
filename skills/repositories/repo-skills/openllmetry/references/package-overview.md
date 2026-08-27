# Package Overview

## Purpose

Read this when you need the shape of the OpenLLMetry Python package suite before choosing a sub-skill. OpenLLMetry is an OpenTelemetry-based observability stack for LLM applications. The repository contains one SDK package, one semantic-convention package, many instrumentation packages, and a sample application package used as workflow evidence.

## Package families

| Family | Distributions | Use |
| --- | --- | --- |
| SDK | `traceloop-sdk` | Initialize tracing/exporters/processors, select multiple instruments, create workflow/task/agent/tool spans, report manual LLM spans, and use Traceloop client surfaces such as datasets, experiments, prompts, feedback, and guardrails. |
| Semantic conventions | `opentelemetry-semantic-conventions-ai` | Shared `opentelemetry.semconv_ai` constants/enums for GenAI, vector DB, workflow/task, event, and legacy alias compatibility. |
| Provider instrumentations | OpenAI, Anthropic, Bedrock, Cohere, Google GenAI, Groq, Mistral, Ollama, Replicate, SageMaker, Together, Vertex AI, VoyageAI, Watsonx, Writer, Aleph Alpha | Patch provider SDK calls and emit GenAI spans, metrics, and message attributes/events. |
| Vector DB instrumentations | Chroma, LanceDB, Marqo, Milvus, Pinecone, Qdrant, Weaviate | Patch vector database clients and emit `db.*`/vector attributes and query/search events. |
| Framework, agent, and protocol instrumentations | Agno, CrewAI, Haystack, LangChain, LiteLLM, LlamaIndex, MCP, OpenAI Agents, Transformers | Capture chains, agents, tools, MCP sessions, local pipeline calls, and framework-level spans. |
| Sample app | `sample-app` | Evidence for real integration recipes. Most examples require provider keys, cloud/vector services, local daemons, or data fixtures and should be treated as recipes, not default checks. |

## Public routes

- Use [`../sub-skills/sdk-and-tracing/SKILL.md`](../sub-skills/sdk-and-tracing/SKILL.md) for application bootstrap and SDK APIs.
- Use [`../sub-skills/instrumentations/SKILL.md`](../sub-skills/instrumentations/SKILL.md) when selecting or debugging an instrumentation package.
- Use [`../sub-skills/semantic-conventions/SKILL.md`](../sub-skills/semantic-conventions/SKILL.md) when validating span attributes or migrating constants.
- Use [`../sub-skills/repo-development/SKILL.md`](../sub-skills/repo-development/SKILL.md) when working in a checkout.

## Installation model

The simplest application install is:

```bash
pip install traceloop-sdk
```

Direct instrumentation package installs follow this pattern:

```bash
pip install 'opentelemetry-instrumentation-<name>[instruments]'
```

The `instruments` extra usually installs the target client library, such as `openai`, `anthropic`, `qdrant-client`, or `langchain`. Some packages have extra names or target import names that differ from their distribution name; use the instrumentation catalog before guessing.

## Runtime prerequisites

| Workflow | Prerequisites |
| --- | --- |
| Offline SDK smoke or semantic-convention check | Python with `traceloop-sdk` or `opentelemetry-semantic-conventions-ai`; no provider credentials. |
| SDK exporting to Traceloop | `TRACELOOP_API_KEY` or explicit `api_key`; optional endpoint/header overrides. |
| SDK exporting to a custom OpenTelemetry destination | A configured `SpanExporter`, `SpanProcessor`, OTLP endpoint, or collector. |
| Direct provider instrumentation | Instrumentation package plus target provider client library; provider calls require credentials/cassettes if executed. |
| Vector DB instrumentation | Instrumentation package plus target vector client; local/in-memory clients may be no-network, hosted services require credentials/network. |
| Framework/agent instrumentation | Framework package plus any nested provider/vector dependencies used by the app. |
| Transformers/Ollama/local service workflows | Target package, possible model cache/download, and for Ollama a running local daemon. |
| Checkout maintenance | Node/npm for Nx, `uv` for Python packages, package-local dependencies, and VCR cassettes or credentials for integration tests. |

## Verification stance

Default to safe checks first:

1. Import the SDK, semantic-convention package, or selected instrumentor.
2. Inspect metadata and signatures.
3. Run bundled no-network helpers.
4. Use VCR cassettes with `--record-mode=none` only after the generated guidance is integrated.
5. Re-record cassettes or run live cloud/vector/service examples only when the user provides credentials and explicitly approves the side effect.
