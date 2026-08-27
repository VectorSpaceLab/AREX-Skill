---
name: genai-observability
description: "Use for MLflow GenAI observability work: tracing, trace
  search/export, OpenTelemetry, prompts, GenAI datasets/evaluation,
  scorers/judges, review queues, assessments, and provider autologging. Routes
  classic experiment/run logging to tracking-and-registry, model flavor
  packaging to models-and-flavors, and deployment/server/MCP commands to
  serving-and-projects."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# GenAI Observability

Use this sub-skill when the task involves MLflow traces, GenAI evaluation, prompts, datasets, feedback, expectations, labeling/review, or provider tracing integrations.

## Route First

- For local app instrumentation, use `@mlflow.trace`, `mlflow.start_span`, `mlflow.get_trace`, `mlflow.search_traces`, and `mlflow.MlflowClient` trace methods; see `references/tracing.md`.
- For evaluation, use `mlflow.genai.evaluate`, `@mlflow.genai.scorers.scorer`, built-in scorers, `mlflow.genai.make_judge`, and trace/dataset-backed evaluation; see `references/genai-evaluation.md`.
- For prompt and dataset lifecycle, use `mlflow.genai.register_prompt`, `load_prompt`, aliases/tags/model config, and `create_dataset`/`search_datasets`; see `references/prompts-and-datasets.md`.
- For OpenAI, Anthropic, Bedrock, Gemini, LangChain, LlamaIndex, and DSPy tracing, prefer provider autologging only when package extras and credentials are installed; keep offline tests on manual tracing.
- For review queues, labeling sessions, feedback, expectations, and assessments, distinguish local tracking-store support from Databricks-only review app features.
- For deployment, auth, AI Gateway, MCP, agent server, and serving commands, route to `serving-and-projects`; for classic run metrics/artifacts/model registry, route to `tracking-and-registry`.

## Safe Workflow

1. Set a tracking URI/experiment deliberately before generating traces or prompts.
2. Instrument deterministic code with manual tracing first; add provider autologging only after extras, credentials, and network access are confirmed.
3. Retrieve traces with `mlflow.get_last_active_trace_id()`, `mlflow.get_trace(..., flush=True)`, or `mlflow.search_traces(...)` before wiring evaluation.
4. Use datasets/prompts as versioned inputs to evaluation; pin prompt aliases or versions explicitly.
5. Add feedback/expectations or custom scorers to make evaluation outcomes inspectable and reproducible.
6. For async/provider traces, flush async logging or wait for export before assertions.

## Bundled Probe

Run the local smoke probe when validating basic tracing without credentials:

```bash
python skills/mlflow/sub-skills/genai-observability/scripts/tracing_smoke.py
```

The script uses a temporary local tracking store, creates nested spans, searches the resulting trace, and emits JSON with the trace id and span count.
