# Observability and Integration Troubleshooting

## Quick Diagnostic Order

1. Validate YAML shape with `python scripts/check_observability_config.py --config mcp_agent.config.yaml --secrets mcp_agent.secrets.yaml --json`.
2. Confirm logger transports and OTEL exporters use supported names only: logger `console`, `file`, `http`, `none`; OTEL `console`, `file`, `otlp`.
3. Separate optional-extra import errors from credential errors before attempting live provider calls.
4. Inspect a tiny JSONL event file with `python scripts/summarize_event_log.py path/to/log.jsonl --limit 20`.
5. Route cloud log tailing and hosted collector commands to `../cli-cloud-operations/SKILL.md`.

## Missing Provider SDK vs Missing API Key

Symptoms and fixes:

- `ModuleNotFoundError: No module named 'openai'`: install the OpenAI extra before importing OpenAI, Ollama, or LM Studio wrappers that use the OpenAI SDK.
- `ModuleNotFoundError: No module named 'anthropic'`: install the Anthropic extra before importing Anthropic wrappers.
- `ModuleNotFoundError: No module named 'langchain_core'`: install the LangChain extra before importing `from_langchain_tool`.
- `ModuleNotFoundError: No module named 'crewai'`: install the CrewAI extra before importing `from_crewai_tool`.
- `AuthenticationError`, `PermissionDeniedError`, 401, or 403 after the wrapper imports: package exists, but credentials, endpoint, account permissions, or model deployment are wrong.
- `NotFoundError` or model-not-found after authentication: the `default_model`, deployment name, local loaded model, or provider-specific model id is wrong.

Avoid eager provider imports in generic checks. Use config inspection first, then import only the wrapper needed for the selected provider.

## OTEL Endpoint and Headers

Common issues:

- `OTLP exporter is enabled but no endpoint is provided`: add `endpoint` under the `otlp` exporter mapping.
- Spans do not appear in the backend: verify the endpoint path matches the collector protocol, often `/v1/traces` for OTLP HTTP traces.
- Authentication failures: confirm headers are configured under `otel.exporters[].otlp.headers`, but never print resolved token values.
- Duplicate spans or global-provider warnings: tracer provider setup is process-global; avoid configuring multiple unrelated apps in one process unless intentional.
- High volume or cost: reduce `otel.sample_rate` or use fewer exporters.

Safe OTLP snippet:

```yaml
otel:
  enabled: true
  service_name: "my-agent"
  sample_rate: 0.25
  exporters:
    - otlp:
        endpoint: "https://collector.example.com/v1/traces"
        headers:
          Authorization: "Bearer ${OTEL_TOKEN}"
```

## Invalid File Log JSONL

mcp-agent file transport writes one compact JSON object per line. Problems usually come from manual edits, partial writes, or mixing console output into the same file.

Use:

```bash
python scripts/summarize_event_log.py logs/mcp-agent.jsonl --strict
```

If it reports malformed lines:

- Check whether a command redirected console output into the JSONL file.
- Inspect only the first few bad line numbers, not the whole log, to avoid exposing sensitive payloads.
- Rotate or truncate the file outside the app only while the app is stopped.
- Keep `logger.path_settings.path_pattern` unique by `timestamp` or `session_id` for concurrent runs.

## Token Counter Not Enabled or Empty

Token tracking requires:

- Runtime inside `MCPApp.run()` or another context that has `context.token_counter`.
- AugmentedLLM methods decorated with token tracking.
- Provider responses that include usage fields, or explicit calls to `record_usage` for custom providers.
- Non-Temporal-replay execution; token tracking intentionally skips Temporal replay.

If summaries are empty, confirm the LLM call completed, the provider response exposed usage, and the code is asking the same running app/context for the summary.

## Progress Display in Non-TTY or Automated Runs

`logger.progress_display: true` is best for interactive terminals. In CI, notebooks, background workers, or redirected output:

- Set `logger.progress_display: false`.
- Use `logger.transports: [file]` and inspect JSONL afterward.
- Avoid interactive replay scripts; use `summarize_event_log.py`.
- If Rich display appears stuck, ensure event bus shutdown is awaited before process exit.

## LangChain and CrewAI Adapter Failures

LangChain:

- Use objects with `.func`, `._run`, `.run`, or direct callability.
- Signature preservation depends on `inspect.signature`; dynamic tools may fall back to generic wrappers.
- If conversion mutates a `StructuredTool.func` name/docstring, wrap or copy the tool first if the original metadata must remain unchanged elsewhere.

CrewAI:

- Class-based tools need `args_schema` with Pydantic `model_fields` and a matching `_run` method.
- Required schema fields are placed before optional fields in the generated callable signature.
- Names with spaces become lowercase underscores unless overridden.
- Invalid objects raise `ValueError` before FastMCP registration.

## LM Studio and Local OpenAI-Compatible Endpoints

Checklist:

- Local server is running and responds at the configured `base_url`, normally `http://localhost:1234/v1` for LM Studio.
- `default_model` exactly matches a loaded model id from `/v1/models`.
- OpenAI SDK extra is installed because LM Studio uses the OpenAI-compatible client.
- The selected local model supports the requested features: tool calling, structured output, long context, or JSON reliability.
- For other local endpoints, set `openai.base_url`, an API-key placeholder if required by the client, and a model name known to that server.

Typical mismatch: the endpoint is reachable but returns model-not-found because the config uses a display name instead of the loaded API model id.

## Streaming Callback Misuse

Use `generate_stream()` when you need progress, tool calls, usage, or errors. Common mistakes:

- Treating every event as text; only `TEXT_DELTA` has incremental text.
- Ignoring `ERROR` events and outer exceptions.
- Performing slow blocking I/O inside the async loop; buffer or hand off work instead.
- Assuming every provider has the same streaming semantics.
- Using `generate_str_stream()` and then expecting tool-call or usage events.

Safe pattern:

```python
async for event in llm.generate_stream(prompt):
    if event.type.name == "TEXT_DELTA":
        render(event.content)
    elif event.type.name == "ITERATION_END":
        logger.info("iteration.done", data={"usage": event.usage})
    elif event.type.name == "ERROR":
        logger.error("stream.error", data=event.content or {})
        break
```

## Usage Telemetry

`usage_telemetry.enabled` defaults to true in settings, with `enable_detailed_telemetry` defaulting false. If an environment prohibits product telemetry, explicitly set:

```yaml
usage_telemetry:
  enabled: false
```

Do not enable detailed telemetry for sensitive prompts or regulated data unless the user explicitly approves it.
