# Troubleshooting

Use this when an instrumentation package imports but does not emit spans, or when the import fails because the target client is missing.

See also:

- [Instrumentation catalog](instrumentation-catalog.md)
- [Workflow recipes](workflow-recipes.md)

## Missing target client package or wrong install extra

If `import opentelemetry.instrumentation.<name>` fails with `ModuleNotFoundError`, the target client library is usually missing.

| Symptom | Likely package | Install extra / target library |
| --- | --- | --- |
| `No module named 'botocore'` | Bedrock or SageMaker | `boto3` |
| `No module named 'google.genai'` | Google Generative AI | `google-genai` |
| `No module named 'qdrant_client'` | Qdrant | `qdrant-client` |
| `No module named 'pymilvus'` | Milvus | `pymilvus` |
| `No module named 'pinecone'` | Pinecone | `pinecone` |
| `No module named 'weaviate'` | Weaviate | `weaviate-client` |
| `No module named 'chromadb'` | Chroma | `chromadb` |
| `No module named 'llama_index'` | LlamaIndex | `llama-index` |
| `No module named 'langchain'` or `langchain_core` | LangChain | `langchain` |
| `No module named 'transformers'` | Transformers | `transformers` |
| `No module named 'writerai'` | Writer | `writer` |
| `No module named 'anthropic'` | Anthropic | `anthropic` |
| `No module named 'openai'` | OpenAI | `openai` |
| `No module named 'groq'` | Groq | `groq` |
| `No module named 'mistralai'` | Mistral AI | `mistralai` |
| `No module named 'replicate'` | Replicate | `replicate` |
| `No module named 'together'` | Together AI | `together` |

If the package name is unclear, check the catalog or run [scripts/inspect_instrumentors.py](../scripts/inspect_instrumentors.py).

## Duplicate spans, metrics, or events

Common causes:

- You used both the SDK selection path and a direct instrumentor for the same client.
- A framework wrapper and a direct provider wrapper both touched the same call chain.
- OpenAI Agents kept its own built-in processor in addition to the OpenTelemetry processor.

Fixes:

- Choose one path per client unless you explicitly want duplicates.
- Use `block_instruments` when the SDK should skip a package.
- For OpenAI Agents, use the package option that replaces existing processors when you want only the OpenTelemetry processor.
- For nested provider calls inside frameworks, use the language-model suppression key.

## No spans after calling `.instrument()`

Check these in order:

1. Call `.instrument()` before creating the client object.
2. Make sure the wrapper package and target client version are compatible.
3. Confirm you did not suppress instrumentation for the current call path.
4. Confirm the call actually exercises an instrumented method, not an unrelated helper.
5. If the package uses post-import hooks, import the target library only after instrumentation or recreate the client after wrapping.

Package-specific examples:

- `OpenAIInstrumentor` auto-selects v0 or v1 wrappers based on the installed OpenAI client.
- `AnthropicInstrumentor` imports streaming internals at module load time, so missing `anthropic` can fail before any instrumentation runs.
- `McpInstrumentor` uses post-import hooks and session wrapping; instrument before the MCP client/server modules are loaded.
- `WeaviateInstrumentor` probes both v3 and v4 APIs, so a version mismatch can show up as missing spans rather than an import error.

## Content or event mode looks wrong

Symptoms:

- You expected prompt/completion payloads but only saw empty spans.
- You expected events, but only span attributes appeared.
- You expected content to disappear, but it still shows up.

Likely causes and fixes:

- `TRACELOOP_TRACE_CONTENT=false` disables payload capture for packages that honor the content flag.
- `use_attributes=True` keeps content on span attributes.
- `use_attributes=False` or `use_legacy_attributes=False` routes content to log events.
- If you use events, provide a logger provider/exporter.
- Some wrappers only emit content for specific operation types, such as chat, completion, query, or stream events.

## Metrics or logs are missing

Check that:

- You passed the right `meter_provider` or `logger_provider` when the package expects one.
- `TRACELOOP_METRICS_ENABLED` is enabled for packages that gate metrics.
- The specific operation you exercised is one that emits metrics.
- You are looking at the right signal. Some packages emit traces only; others emit traces plus metrics; a smaller set also emits log events.

## VCR, live service, and local service problems

### VCR-backed runs

- `--record-mode=none` requires an existing cassette.
- Replay failures usually mean the recorded payload changed or the client version moved.
- Re-record only when you have the needed credentials and the service behavior really changed.

### Live cloud or hosted service runs

- Missing credentials are expected for hosted providers and vector DBs.
- Do not blame the wrapper until the replay or offline path has been ruled out.

### Local services or local model caches

- Ollama needs a running local server.
- Local vector DB tests may need a running local client, an in-memory mode, or a writable data directory.
- Transformers-based examples may need the model already cached or the environment prepared to download it.

## When the problem is really a selection mistake

If the issue is about choosing the wrapper path rather than fixing the wrapper itself, return to the catalog and decide again:

- direct instrumentor for one client and one provider stack,
- SDK `Instruments` selection for many installed packages,
- `block_instruments` when you need to subtract one wrapper family from the SDK set.
