# Observability Reference

## Monitoring and tracing

Jina supports both legacy Prometheus/Grafana metrics and OpenTelemetry-based tracing/metrics.

Key settings:

- `monitoring=True` and `port_monitoring=...` for local metrics endpoints.
- `tracing=True`, `traces_exporter_host`, and `traces_exporter_port` for traces.
- `metrics=True`, `metrics_exporter_host`, and `metrics_exporter_port` for metrics.
- Client tracing is supported; client metrics/tracing must be configured separately from service-side configuration.

## What to expect

- Monitoring endpoints expose counters/histograms about request throughput, bytes, and request processing timing.
- OpenTelemetry requires an external collector/backends such as Jaeger and Prometheus/Grafana if you want to visualize signals.
- Jina can export schema details for the Gateway OpenAPI surface, but observing data requires the exporter/collector/visualization stack to be running.

## Telemetry and privacy

- `JINA_OPTOUT_TELEMETRY=1` disables Jina telemetry.
- Do not embed auth tokens, cloud secrets, or private registry credentials in generated skill examples.
