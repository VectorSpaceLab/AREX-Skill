# Observability Troubleshooting

## `observability_enabled_but_otel_not_installed`

Install the optional extra:

```bash
python -m pip install 'everos[otel]'
```

Then restart the server.

## No spans in backend

Check:
- `[observability].enabled = true`.
- `exporter` is not `none`.
- OTLP `endpoint` is correct, or Langfuse host/keys are set.
- Network egress from the server host to the backend is allowed.
- `sample_rate` is not 0.
- The server was restarted after config changes.

## Langfuse accepts traces but no scores

Recall scores need `emit_recall_scores=true` plus `langfuse_public_key`, `langfuse_secret_key`, and `langfuse_host`. They are sent out-of-band through a bounded background queue; under backpressure scores can be dropped while requests still succeed.

## Wrong Langfuse region

A 401/403 from Langfuse often means the keys belong to the other region. Try the matching US/EU host for the project.

## Sensitive content appears in traces

Set `capture_content=false` and restart. Content capture is opt-in but global for the process; review downstream retention policies before enabling it.

## Logs are too noisy

EverOS demotes common HTTP client success logs, but debug-level application logs can still be verbose. Start the server with a suitable log level and avoid enabling verbose CLI flags in production unless diagnosing an issue.
