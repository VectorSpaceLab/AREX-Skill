# Troubleshooting

## Missing Extras Or Imports

- Provider autologging requires the provider package plus compatible MLflow integration code. Install the relevant extra/package before debugging spans.
- Third-party scorer integrations such as Ragas, Deepeval, TruLens, Phoenix, or Guardrails may require optional packages and provider credentials.
- If `mlflow.genai.datasets` raises a Databricks agents import error, either install the Databricks agents package for workspace-backed datasets or use a local tracking URI workflow.

## Credentials, Network, And Backends

- OpenAI, Anthropic, Bedrock, Gemini, and judge models require provider credentials and network access. Do not run provider examples in offline validation.
- Databricks review apps, labeling sessions, scheduled scorers, Unity Catalog trace locations, and managed judge defaults can require workspace auth and backend feature availability.
- For Databricks tracking URIs, ensure host/token/profile and registry/tracking URI settings are deliberate; local SQLite or legacy file tracking behavior is not a proxy for workspace features.

## Trace Destination And Experiment Mismatch

- Empty trace search usually means the tracking URI, active experiment, trace destination, or search `locations` do not match where traces were logged.
- Set `mlflow.set_tracking_uri(...)` and `mlflow.set_experiment(...)` before instrumentation in tests.
- If using `mlflow.tracing.set_destination(...)` or experiment trace locations, verify root spans target the intended experiment or UC schema.
- Sampling can drop traces; check sampling configuration and per-function `sampling_ratio_override`.

## Async Flush And Export

- Async trace logging can make immediate assertions flaky. Use `mlflow.get_trace(trace_id, flush=True)`, `mlflow.flush_trace_async_logging(...)`, or backend-specific waits.
- OpenTelemetry exporters may buffer spans; confirm batch processor shutdown/flush semantics before concluding spans are missing.
- Streaming generators are logged only after consumption; consume streams fully before searching traces.

## OTLP Endpoint Headers

- Check OTLP endpoint URL, protocol, auth headers, TLS/proxy configuration, and collector logs.
- Header formatting errors often look like missing traces rather than authentication failures inside application code.
- Ensure service-to-service propagation uses MLflow tracing context helper APIs at HTTP ingress and egress boundaries.

## Prompt, Dataset, And Evaluation Pitfalls

- Prompt alias mistakes are common: verify alias target version after reassignment and bypass caches in tests.
- Chat prompt templates must include `role` and `content`; invalid message schemas fail at registration or formatting time.
- Evaluation data must match scorer signatures. A scorer requiring `expectations` will fail or produce weak results if expectation keys are absent.
- Token/cost attribution may be missing for streamed, wrapped, or nonstandard provider responses. Treat usage metrics as best-effort unless validated against provider payloads.
- LLM judges can be nondeterministic; control model, inference parameters, prompt instructions, and feedback value type when comparing results across runs.
