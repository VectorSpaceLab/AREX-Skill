# Troubleshooting

Use this when SDK bootstrap or tracing output does not look the way you expect.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Error: Missing Traceloop API key` during `Traceloop.init()` | You are using the default Traceloop cloud endpoint with no custom exporter/processor and no API key | Set `TRACELOOP_API_KEY`, pass `api_key=...`, or switch to a local OTLP/custom exporter path |
| `Client not initialized` from `Traceloop.get()` | The singleton client was never created in this process, or `Traceloop.init()` returned early | Initialize once at app startup, or construct `Client(api_key=..., api_endpoint=...)` directly when you need a separate client |
| Warning that the exporter is ignored | Both `exporter` and `processor` were passed to `Traceloop.init()` | Wrap the exporter inside the processor, or build a default processor with `Traceloop.get_default_span_processor()` and combine it with your custom processor(s) |
| `No valid instruments set` | `instruments=set()` was passed, or the selected target libraries are not installed | Omit `instruments` to let Traceloop choose available instruments, or install the target libraries / select valid `Instruments` members |
| `Metrics are disabled` or logs never appear | Metrics are disabled by config, or you supplied a custom trace pipeline without a metrics exporter; logging is off by default unless explicitly enabled and exported | Set the relevant `TRACELOOP_METRICS_ENABLED` / `TRACELOOP_LOGGING_ENABLED` values and supply `metrics_exporter` / `logging_exporter` when you want those signals |
| Decorated inputs, outputs, or prompt content are missing | `TRACELOOP_TRACE_CONTENT=false`, `use_attributes=False` without an event logger provider, or an allow-list / redaction path is suppressing content | Enable content tracing, configure the event logger provider when using the events path, and check any allow-list or redaction callback in play |
| Re-initialization seems ignored | The `TracerWrapper` singleton already exists in this process | Initialize once per process; if you need a different tracing config, start a fresh process |
| Prompt, dataset, experiment, or guardrail calls fail | The API key or endpoint is wrong, or you are using a client surface in the wrong execution context | Call `Traceloop.get()` only after init, or build `Client(api_key=..., api_endpoint=...)` directly; `Experiment.run_in_github()` only works in GitHub Actions pull_request jobs; `from_dataframe()` needs the `datasets` extra / pandas |
| `span_postprocess_callback` never fires | You supplied your own processor or processor list, so the default processor wrapper path was bypassed | Move redaction into your custom processor, or keep the default processor path when you need the callback |

Related references:
- [`sdk-api.md`](sdk-api.md)
- [`sdk-workflows.md`](sdk-workflows.md)
- [`../../instrumentations/SKILL.md`](../../instrumentations/SKILL.md)
- [`../../semantic-conventions/SKILL.md`](../../semantic-conventions/SKILL.md)
