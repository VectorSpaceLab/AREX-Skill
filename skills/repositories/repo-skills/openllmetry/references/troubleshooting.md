# Cross-cutting Troubleshooting

## Missing API key during `Traceloop.init()`

**Symptoms**

- Initialization prints a missing Traceloop API key message.
- `Traceloop.get()` raises that the client was not initialized.

**Likely causes**

- You are using the default Traceloop cloud endpoint without `TRACELOOP_API_KEY`, `api_key`, custom headers, exporter, or processor.
- You expected `Traceloop.init()` to return a client while using a custom exporter/processor.

**Recovery**

- For local/debug checks, pass an in-memory or console exporter and avoid cloud delivery.
- For Traceloop cloud, set `TRACELOOP_API_KEY` or pass `api_key=...`.
- For OTLP/collector delivery, pass the right exporter/processor or endpoint/headers and do not expect `Traceloop.get()` unless a Traceloop client was created.
- Read [`../sub-skills/sdk-and-tracing/references/troubleshooting.md`](../sub-skills/sdk-and-tracing/references/troubleshooting.md).

## Instrumentor import fails with a missing provider module

**Symptoms**

- `ModuleNotFoundError: No module named 'openai'`, `anthropic`, `qdrant_client`, `chromadb`, `botocore`, `llama_index`, `transformers`, or another target client.
- The instrumentation distribution appears installed, but the instrumentor module cannot import.

**Likely causes**

- The instrumentation package was installed without its target client dependency.
- The distribution name, entry-point name, and import name differ.

**Recovery**

- Install the target library or the package's `instruments` extra.
- Use [`../sub-skills/instrumentations/references/instrumentation-catalog.md`](../sub-skills/instrumentations/references/instrumentation-catalog.md) to map the distribution to target clients and entry points.
- Run [`../sub-skills/instrumentations/scripts/inspect_instrumentors.py`](../sub-skills/instrumentations/scripts/inspect_instrumentors.py) against a checkout or installed environment.

## No spans are emitted

**Likely causes**

- The target library was imported/called before instrumentation was applied.
- The wrong instrument was selected or all selected instruments are blocked.
- The app uses a custom tracer provider that is not connected to the exporter you are inspecting.
- Suppression context or duplicate wrapping prevents nested spans.

**Recovery**

- For SDK workflows, initialize `Traceloop.init(...)` before the first provider/client call.
- For direct wrappers, call `Instrumentor().instrument()` before creating or using the client when the wrapper requires it.
- For custom providers/processors, start with `InMemorySpanExporter` and a minimal bundled smoke script.
- Check SDK routing in [`../sub-skills/sdk-and-tracing/SKILL.md`](../sub-skills/sdk-and-tracing/SKILL.md) and wrapper routing in [`../sub-skills/instrumentations/SKILL.md`](../sub-skills/instrumentations/SKILL.md).

## Prompt or completion content is missing

**Likely causes**

- `TRACELOOP_TRACE_CONTENT=false` disables content capture.
- `use_attributes=False` routes content through the event/log path, but no event/log provider is configured.
- The provider wrapper intentionally treats some metadata, such as finish reasons, separately from content.

**Recovery**

- Decide whether privacy or debuggability is more important for the current run.
- Use `TRACELOOP_TRACE_CONTENT=false` for privacy-sensitive production flows.
- For event mode, configure an OpenTelemetry event/logger provider before expecting message events.
- Use [`../sub-skills/semantic-conventions/SKILL.md`](../sub-skills/semantic-conventions/SKILL.md) when validating exact message/finish-reason attributes.

## VCR cassette or live-service test fails

**Likely causes**

- The cassette is missing or incompatible with the requested request/response shape.
- A test is running in record mode without required API keys.
- A cloud/vector/local service is not available.

**Recovery**

- Prefer `--record-mode=none` for replay-only checks.
- Re-record only when API interactions intentionally changed and credentials are available.
- Scrub secrets before committing cassettes.
- Read [`../sub-skills/repo-development/references/testing-vcr-and-nx.md`](../sub-skills/repo-development/references/testing-vcr-and-nx.md).

## Semantic-convention assertions drift

**Likely causes**

- Upstream OpenTelemetry GenAI semantic conventions changed.
- Code uses deprecated `gen_ai.system` or legacy `SpanAttributes.LLM_*` names incorrectly.
- Message JSON does not match the expected parts schema.

**Recovery**

- Run [`../sub-skills/semantic-conventions/scripts/check_semconv_constants.py`](../sub-skills/semantic-conventions/scripts/check_semconv_constants.py) for a no-network constant check.
- Read [`../sub-skills/semantic-conventions/references/migration-notes.md`](../sub-skills/semantic-conventions/references/migration-notes.md) before renaming constants.
