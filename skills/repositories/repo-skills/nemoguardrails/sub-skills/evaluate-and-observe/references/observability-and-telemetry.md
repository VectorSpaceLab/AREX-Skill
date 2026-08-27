# Observability and Telemetry

This reference distinguishes logging, tracing, metrics, and anonymous usage telemetry.

## Signals at a glance

| Signal | Answers | Main control | Scope |
| --- | --- | --- | --- |
| Logging | What happened in one request? | `verbose`, `explain()`, `options.log` | local debugging and per-request inspection |
| Tracing | Which rails and model calls ran? | `tracing.enabled` and adapters | per-request OpenTelemetry or local trace files |
| Metrics | How is the system behaving over time? | `metrics.enabled` plus an IORails engine | aggregate request and LLM-call metrics |
| Telemetry | What deployment patterns are in use? | anonymous usage collection with opt-out | product usage reporting, not request observability |

## Logging and debugging

The logging package gives you several layers of detail:

- `LLMRails(..., verbose=True)` for console output during generation
- `rails.explain()` for a compact summary of the last run
- `generate(..., options={"log": ...})` for structured per-request data
- `output_vars` for selected context values
- `simplify` formatting to make noisy logs easier to read

Useful CLI and runtime switches include:

- `nemoguardrails chat --verbose`
- `nemoguardrails chat --verbose-no-llm`
- `nemoguardrails chat --verbose-simplify`
- `nemoguardrails chat --debug-level ...`
- `nemoguardrails eval rail topical --verbose`
- `nemoguardrails eval check-compliance --verbose`

The logging package is split into focused modules: `verbose.py`, `explain.py`, `processing_log.py`, `llm_tracker.py`, `stats.py`, and `simplify_formatter.py`.

## Tracing

Tracing is enabled in config:

```yaml
tracing:
  enabled: true
  span_format: opentelemetry
  adapters:
    - name: OpenTelemetry
```

Common adapter choices:

- `FileSystem` for local trace files
- `OpenTelemetry` for production backends
- custom adapters when you need a specialized sink

Important tracing rules:

- Configure the host application's OpenTelemetry `TracerProvider` before constructing rails.
- If the provider is missing, spans are typically dropped and the adapter may warn once.
- `FileSystem` writes JSONL traces to a local file path; the async path needs `aiofiles`.
- `opentelemetry` span format is the recommended one; `legacy` exists only for backward compatibility.
- Tracing content capture is privacy-sensitive. Leave it off unless you need prompt/response text in spans.

### OpenTelemetry caveat

The library depends on the OpenTelemetry API only. The host application owns the SDK, exporters, processors, and resources.

Use the same `service.name` resource for traces and metrics if you want the backend to correlate them cleanly.

## Metrics

Metrics are separate from tracing and are emitted only by the IORails engine.

Minimal shape:

```yaml
tracing:
  enabled: false

metrics:
  enabled: true
```

Operational rules:

- metrics need `opentelemetry-api` and a configured `MeterProvider`
- `Guardrails(config, use_iorails=True, require_iorails=True)` is the safest way to fail loudly when metrics are expected
- `LLMRails` does not emit metrics unless it is routed to IORails
- synchronous `generate()` does not emit metrics; use `generate_async()` or `stream_async()`
- if no `MeterProvider` is configured, the API returns a no-op meter and emissions are silently discarded

Exporter guidance:

- use `ConsoleMetricExporter` first for local checks
- use OTLP or Prometheus for production
- expect the backend to honor OpenTelemetry naming and bucket conventions only when it is configured to do so

## Anonymous usage telemetry

Telemetry is a separate product-usage signal.
It is emitted when you instantiate `LLMRails`, `IORails`, or `Guardrails`, then continues with periodic heartbeats from the same process.

Collected telemetry summarizes the deployment, not request content. It can include things like:

- package version, Python version, platform, and OS
- Colang version
- provider engine names and rails engine class
- rail counts and active rail categories
- built-in feature ids
- whether tracing, streaming, or a knowledge base is configured
- whether the deployment is a library, API server, or CLI server
- a per-process session UUID

It does **not** collect prompts, completions, model names, credentials, file paths, usernames, or IP addresses.

The local audit file is a JSONL record of the inner event payload. It rotates when it grows, and audit writes are best effort.

### Opt out

Set any one of these before the library starts:

```bash
export NEMO_GUARDRAILS_NO_USAGE_STATS=1
export DO_NOT_TRACK=1
mkdir -p ~/.config/nemoguardrails && touch ~/.config/nemoguardrails/do_not_track
```

Telemetry is also auto-disabled in CI and under pytest so test traffic does not look like real adoption.

### Important distinction

Disabling telemetry does not disable tracing, metrics, or any OpenTelemetry SDK you configure yourself. Those are separate switches.
