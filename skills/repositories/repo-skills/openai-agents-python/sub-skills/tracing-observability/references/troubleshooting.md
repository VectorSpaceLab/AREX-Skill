# Tracing & Observability Troubleshooting

## Missing Trace API Key

Symptoms:

- Logs contain `OPENAI_API_KEY is not set, skipping trace export`.
- Runs succeed but no traces appear in the OpenAI traces dashboard.
- Third-party model calls work, but OpenAI trace export does not.

Checks and fixes:

1. Confirm tracing is not disabled with `OPENAI_AGENTS_DISABLE_TRACING`, `set_tracing_disabled(True)`, or `RunConfig(tracing_disabled=True)`.
2. Provide an OpenAI tracing key through `OPENAI_API_KEY`, `set_tracing_export_api_key(...)`, or per-run `RunConfig(tracing={"api_key": ...})`.
3. If a custom model client/provider should not be used for trace export, configure that client with `use_for_tracing=False` and set a dedicated tracing key.
4. Never print or persist the key while debugging; use [../../models-providers/SKILL.md](../../models-providers/SKILL.md) for provider/model key selection.

Run `scripts/check_tracing_config.py --json` to confirm whether a key is present without revealing its value.

## Tracing Unexpectedly Disabled

Symptoms:

- No spans are produced.
- Processor callbacks are not invoked.
- Debug logs mention no-op traces or disabled tracing.

Likely causes:

| Cause | Resolution |
| --- | --- |
| `OPENAI_AGENTS_DISABLE_TRACING=1` or `true` is set before first provider use. | Unset it or set it to `0` / `false` before process startup. |
| `set_tracing_disabled(True)` was called. | Call `set_tracing_disabled(False)` during startup or isolate the disabling call to tests. |
| `RunConfig(tracing_disabled=True)` is passed. | Remove it or make it conditional on privacy/export policy. |
| Parent trace was created with `disabled=True`. | Create the parent trace enabled, or remove the wrapper. |
| `set_trace_processors([])` replaced all processors. | Re-register the desired processors or use `add_trace_processor()` instead. |

The default provider reads the env disable flag lazily on first tracing use. Manual `set_tracing_disabled(...)` then takes precedence.

## Sensitive Payload Leakage

Symptoms:

- Trace spans include model prompts, model outputs, tool arguments, or tool results.
- Logs include raw prompts, tool payloads, or exception text containing secrets.
- A custom processor/exporter writes sensitive values to another system.

Fixes:

1. Set `RunConfig(trace_include_sensitive_data=False)` for sensitive runs.
2. Set `OPENAI_AGENTS_TRACE_INCLUDE_SENSITIVE_DATA=0` before startup to change the default for new `RunConfig` instances.
3. Keep `OPENAI_AGENTS_DONT_LOG_MODEL_DATA=1` and `OPENAI_AGENTS_DONT_LOG_TOOL_DATA=1`, which are the protective defaults.
4. Remove raw user input, API keys, tenant IDs that are considered secret, and local paths from `trace_metadata`.
5. Audit custom processors for logging, metrics tags, exception handling, and side-channel exports.
6. Redact application exceptions and tracebacks separately. Suppressing trace payload capture does not rewrite exception objects, exception chains, or log records.

If tool failures are returned to the model, also check any custom `tool_error_formatter` and tool implementation exceptions under the tool/guardrail sub-skill.

## Processor or Exporter Errors

Symptoms:

- Logs contain `Error in trace processor ...`, `Tracing: exporter raised ...`, client errors, server errors, or retry exhaustion.
- Agent runs continue, but observability data is missing or incomplete.

Facts verified from source/tests:

- The multi-processor wrapper catches processor callback exceptions and logs them.
- The batch processor catches exporter exceptions and drops the failed batch rather than killing agent execution.
- The default backend exporter retries transient failures and does not retry most 4xx client errors.
- Queue overflow logs warnings and drops new trace/span items.

Fixes:

1. Keep processor callbacks short, non-blocking, and internally exception-safe.
2. Move network export work into a background queue or use `BatchTraceProcessor`.
3. Implement `force_flush()` and `shutdown()` for custom processors.
4. Increase `max_queue_size`, reduce callback latency, or sample traces if queue overflow occurs.
5. Use `add_trace_processor()` for secondary processors so default export remains in place; use `set_trace_processors()` only when replacement is intentional.
6. For local-only diagnostics, replace processors with a counting processor and no external exporter.

## Async Flush and Shutdown

Symptoms:

- A short-lived job exits before traces appear.
- Background worker traces show up after a delay.
- Shutdown hangs or logs timeout warnings.

Guidance:

- The default `BatchTraceProcessor` exports every few seconds, at queue thresholds, and during process shutdown.
- Call `flush_traces()` after the `trace()` context exits when a job needs immediate delivery.
- Do not flush before a trace is closed if a complete trace is required.
- For blocking exporters, implement deadline-aware shutdown if possible and keep network timeouts bounded.
- In async applications, call the synchronous `flush_traces()` from a safe boundary where blocking briefly is acceptable, such as final cleanup of a background job.

## Graphviz Visualization Extra Missing

Symptoms:

- `ImportError: No module named graphviz` when importing `agents.extensions.visualization`.
- Rendering fails even though the Python package imports.
- No PNG is produced from `draw_graph(..., filename=...)`.

Fixes:

1. Install the optional visualization dependency for the SDK environment, such as `openai-agents[viz]`.
2. Install the system Graphviz executable (`dot`) if PNG/SVG rendering fails.
3. In CI or headless environments, inspect `draw_graph(agent).source` instead of opening a viewer.
4. Avoid using original repository visualization tests as runtime dependencies; distill the topology pattern into local code.

Run `scripts/check_tracing_config.py --check-processor --json` to report Python package availability and whether the `dot` executable is present.

## Usage Counts Are Zero or Incomplete

Symptoms:

- `result.context_wrapper.usage.total_tokens` is zero.
- `request_usage_entries` is empty.
- Streaming adapter calls lack usage details.

Checks and fixes:

1. Confirm the model/provider actually returns usage data.
2. For streamed Chat Completions or third-party adapters, try `ModelSettings(include_usage=True)`.
3. Read usage after the run finishes; each `Runner.run()` call has its own usage object even when a session persists conversation history.
4. Route adapter-specific behavior to [../../models-providers/SKILL.md](../../models-providers/SKILL.md).

## Traces Not Grouped as Expected

Symptoms:

- Related runs appear as separate workflows.
- Resumed or multi-step tasks do not share the intended trace metadata.

Fixes:

- Set a stable `workflow_name` and `group_id` in `RunConfig` for every run in the conversation or job.
- Wrap multi-call workflows in one `with trace(...):` block when they should be part of a single trace.
- Use `gen_trace_id()` if manually supplying `trace_id` values.
- Avoid creating nested traces unless intentionally starting a separate logical workflow.
