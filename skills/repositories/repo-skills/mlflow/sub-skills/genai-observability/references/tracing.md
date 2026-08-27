# Tracing

## Core APIs

- `@mlflow.trace` instruments sync, async, generator, async-generator, classmethod, and staticmethod functions; it captures inputs, outputs, exceptions, span type, attributes, optional sampling override, and optional trace destination.
- `mlflow.start_span(name=..., attributes=...)` creates manual child spans in the current trace; call `span.set_inputs(...)`, `span.set_outputs(...)`, `span.set_attribute(...)`, and related span methods for explicit structure.
- `mlflow.get_current_active_span()` and `mlflow.get_last_active_trace_id(thread_local=False)` help connect code paths to the current or last trace.
- `mlflow.get_trace(trace_id, flush=True)` retrieves a trace after forcing async logging flush when supported.
- `mlflow.search_traces(...)` retrieves traces as a DataFrame by default or list when requested by the installed API; use `locations`/experiment ids and filter strings for precise retrieval.
- `mlflow.MlflowClient` exposes lower-level trace controls: `start_trace`, `start_span`, `end_span`, `end_trace`, `get_trace`, `search_traces`, `set_trace_tag`, `delete_trace_tag`, and `log_assessment` where supported.

## Manual Instrumentation Pattern

Use this shape for offline-safe tests and examples:

```python
import mlflow

mlflow.set_tracking_uri("sqlite:////tmp/mlflow-tracing.db")
mlflow.set_experiment("local-tracing")

@mlflow.trace(span_type="CHAIN", attributes={"component": "retriever"})
def retrieve(question: str) -> list[str]:
    return ["MLflow traces capture spans"]

@mlflow.trace(name="rag_answer", span_type="CHAIN")
def answer(question: str) -> str:
    docs = retrieve(question)
    with mlflow.start_span("compose", attributes={"doc_count": len(docs)}) as span:
        span.set_inputs({"question": question, "docs": docs})
        response = f"Answer from {len(docs)} docs"
        span.set_outputs(response)
        return response

answer("What is tracing?")
trace = mlflow.get_trace(mlflow.get_last_active_trace_id(), flush=True)
```

## Search, Tags, And Metadata

- Prefer setting meaningful trace tags/metadata at trace creation or through client tag methods so later `search_traces` calls can separate environments, prompt versions, datasets, and app variants.
- Typical filters include timestamp bounds, trace/request metadata, tags, status/state, and experiment location. Confirm exact filter grammar against the installed MLflow version when constructing advanced nested metadata filters.
- Use `max_results` in examples and tests to keep trace scans bounded.
- If search returns no traces, check tracking URI, active experiment, trace destination, async flush, and whether the trace was sampled.

## Assessments, Feedback, And Expectations

- `mlflow.log_feedback`, `mlflow.log_expectation`, and `mlflow.log_assessment` attach human/model assessments to traces when available in the installed version.
- Feedback is suited for ratings and comments about observed outputs; expectations are suited for ground-truth/reference values used later by scorers.
- When using client-level assessment APIs, ensure the trace has already been exported to the backend and keep assessment source names stable for evaluation.

## OpenTelemetry And Distributed Tracing

- `mlflow.tracing.configure`, `mlflow.tracing.enable`, `disable`, `reset`, and `set_destination` control tracing provider behavior.
- OpenTelemetry ingestion/export paths depend on installed OpenTelemetry packages and endpoint configuration. Validate OTLP protocol, headers, auth, and endpoint URL before debugging MLflow application code.
- For service-to-service propagation, use `mlflow.tracing.get_tracing_context_headers_for_http_request()` and `set_tracing_context_from_http_request_headers(...)` around HTTP boundaries.
- Databricks monitoring/Unity Catalog trace locations require workspace configuration and are not equivalent to a local SQLite smoke-test store or legacy file tracking store.

## Provider Autologging

- `mlflow.openai.autolog()`, `mlflow.anthropic.autolog()`, `mlflow.bedrock.autolog()`, `mlflow.gemini.autolog()`, `mlflow.langchain.autolog()`, `mlflow.llama_index.autolog()`, and `mlflow.dspy.autolog()` add provider/framework spans when the related package is installed.
- Provider examples are credentialed/networked workflows. Keep CI and local smoke tests on manual spans unless credentials, package extras, and network policy are explicitly provided.
- Token and cost attribution can be incomplete when providers omit usage fields, stream partial chunks, use wrappers, or return nonstandard response schemas.
