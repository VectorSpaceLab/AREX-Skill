# Observability Reference

## Logging

EverOS uses structlog and bridges stdlib logging through the same formatter. `configure_logging(level="INFO")` replaces the root handler with a stdout handler using a shared processor chain. Third-party HTTP client success logs are demoted to warnings to reduce noise.

The server CLI configures logging before handing off to Uvicorn and passes `log_config=None` so Uvicorn does not replace handlers.

## Request IDs

The API installs request-id middleware outermost. Success and error envelopes include `request_id`, and logs/traces can correlate on that value.

## Metrics

`GET /metrics` returns the Prometheus exposition format from the current registry. The metrics lifespan warms/logs the registry at startup; it does not start a separate metrics server.

## Tracing config

Install optional dependencies:

```bash
python -m pip install 'everos[otel]'
```

Enable in `everos.toml`:

```toml
[observability]
enabled = true
exporter = "otlp_http"
endpoint = "https://collector.example/v1/traces"
service_name = "everos"
sample_rate = 1.0
capture_content = false
```

When disabled, exporter is `none`, or the `otel` extra is missing, tracing returns no-op spans and should not break application behavior. The tracing lifespan initializes before other providers and shuts down/flushed on app shutdown.

## Privacy

`capture_content=false` means metadata-only spans. Set `capture_content=true` only when it is acceptable to emit query text, extracted memory, and Markdown paths to the configured backend. The setting is global for the process.

## Trace operations

Expected operations include:

| Operation | Trace signal |
|---|---|
| `/memory/add` and `/memory/flush` | request/root memory spans |
| boundary detection and extraction | generation spans with model/usage when available |
| persistence | markdown/storage spans |
| `/memory/search` | retriever and recall/rank spans |
| embedding calls | embedding spans |
| OME strategies/reflection | strategy spans linked to triggering context |
