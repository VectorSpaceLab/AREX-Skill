# Observability in BentoML

## Access and Library Logging

BentoML server access logging is enabled by default. Each request log includes the client, request method/path/content details, response status/content details, latency, and OpenTelemetry fields such as trace ID, span ID, sampling flag, and service name.

Configure access logs on the service decorator:

```python
import bentoml

@bentoml.service(logging={
    "access": {
        "enabled": True,
        "request_content_length": True,
        "request_content_type": True,
        "response_content_length": True,
        "response_content_type": True,
        "skip_paths": ["/metrics", "/healthz", "/livez", "/readyz"],
        "format": {"trace_id": "032x", "span_id": "016x"},
    }
})
class MyService:
    ...
```

Operational notes:

- Access log defaults already skip `/metrics`, `/healthz`, `/livez`, and `/readyz` in BentoML's default runtime configuration.
- BentoML library logs use the `bentoml` logger namespace. When using BentoML as a library, Python's root logger behavior applies unless the application registers a handler and level for `logging.getLogger("bentoml")`.
- Avoid file-rotation handlers inside the service definition for `bentoml serve` child processes; configure central logging outside the service process or stream logs to stdout/stderr for container platforms.
- Trace/span IDs in logs are for correlation; tracing export still requires tracing configuration and optional exporter dependencies.

## Metrics

BentoML exposes a Prometheus-compatible `/metrics` endpoint by default. Default service metrics include:

- `bentoml_service_request_in_progress` gauge with endpoint, runner/service name/version dimensions.
- `bentoml_service_request_total` counter with endpoint, service, runner, version, and HTTP response code dimensions.
- `bentoml_service_request_duration_seconds_*` histogram series with endpoint, service, runner, version, and HTTP response code dimensions.
- `bentoml_service_adaptive_batch_size_*` histogram series when adaptive batching is enabled.

Configure service metrics with the `metrics` decorator field:

```python
@bentoml.service(metrics={
    "enabled": True,
    "namespace": "bentoml_service",
    "duration": {"buckets": [0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0]},
})
class MyService:
    ...
```

Rules and gotchas:

- `metrics.enabled` defaults to `True`; disabling it removes the primary Prometheus endpoint signal for server behavior.
- `metrics.duration.buckets` is mutually exclusive with exponential `duration.min`, `duration.max`, and `duration.factor`.
- `duration.factor` must be greater than `1.0`; `min` and `max` must be positive floats.
- Custom metrics can be created with `prometheus_client` or `bentoml.metrics` classes such as `Counter`, `Histogram`, `Summary`, and `Gauge`.
- Import-order matters for multiprocess Prometheus collection. BentoML's `bentoml.metrics` module defers importing `prometheus_client` until first metric attribute access so workers can set `PROMETHEUS_MULTIPROC_DIR` first. Prefer defining custom metrics at module import time with `bentoml.metrics` or follow the same deferred-import discipline.

Minimal custom metric pattern:

```python
import time
import bentoml
from bentoml.metrics import Counter, Histogram

request_counter = Counter(
    "summary_requests_total",
    "Total summarization requests",
    ["status"],
)
latency = Histogram(
    "summary_latency_seconds",
    "Summarization latency",
    ["status"],
    buckets=(0.1, 0.2, 0.5, 1.0, 2.0, 5.0, float("inf")),
)

@bentoml.service
class Summarization:
    @bentoml.api
    def summarize(self, text: str) -> str:
        start = time.time()
        status = "success"
        try:
            return text[:80]
        except Exception:
            status = "failure"
            raise
        finally:
            request_counter.labels(status=status).inc()
            latency.labels(status=status).observe(time.time() - start)
```

Verification checklist:

1. Start the service locally.
2. Call at least one API endpoint so request metrics are registered.
3. Request `GET /metrics` and search for default and custom metric names.
4. If custom metrics are absent in a multi-worker service, inspect metric import order and `PROMETHEUS_MULTIPROC_DIR` behavior before changing the metric names.

## Health and Monitoring Endpoints

BentoML services expose:

- `/livez`: liveness probe.
- `/readyz`: readiness probe.
- `/healthz`: alias of `/livez`.

A healthy endpoint returns HTTP 200 with an empty body. Custom endpoint paths can be configured with `endpoints={"livez": "/health", "readyz": "/ready"}` on the service decorator or service constructor.

Use health endpoints for Kubernetes probes, BentoCloud readiness checks, and quick local smoke checks before diagnosing collectors or clients.

## Monitoring and Data Collection

Use `bentoml.monitor(name)` inside API code to log structured inference data:

```python
import bentoml

@bentoml.service(monitoring={
    "enabled": True,
    "type": "default",
    "options": {"log_path": "monitoring"},
})
class Summarization:
    @bentoml.api
    def summarize(self, text: str) -> str:
        prediction = text[:80]
        with bentoml.monitor("text_summarization") as monitor:
            monitor.log(text, name="input_text", role="feature", data_type="text")
            monitor.log(prediction, name="summary", role="prediction", data_type="text")
        return prediction
```

Default monitor behavior:

- Writes schema logs under `monitoring/<monitor_name>/schema/` and data logs under `monitoring/<monitor_name>/data/`.
- Uses rotating JSON log handlers by default.
- Adds preserved columns such as `timestamp`, `request_id`, and `trace_id`.
- Accepts a custom Python logging YAML via `monitoring.options.log_config_file`.

OTLP monitoring mode:

```python
@bentoml.service(monitoring={
    "enabled": True,
    "type": "otlp",
    "options": {
        "endpoint": "http://localhost:5000",
        "insecure": True,
        "timeout": 10,
        "meta_sample_rate": 1.0,
    },
})
class MyService:
    ...
```

Operational guardrails:

- External collectors, Fluent Bit, Kafka, object stores, Datadog, Elasticsearch, InfluxDB, BigQuery, and Arize require deployment-specific infrastructure and credentials. Mark them explicitly as external requirements in plans.
- Keep secrets such as Arize API keys out of service source when possible; use runtime envs/secrets instead.
- For containers, mount or ship the configured `log_path` if local monitor files must persist across restarts.

## Tracing

BentoML uses OpenTelemetry tracing with `zipkin`, `jaeger`, or `otlp` exporters. Configure tracing on the service decorator:

```python
@bentoml.service(tracing={
    "exporter_type": "otlp",
    "sample_rate": 1.0,
    "timeout": 5,
    "max_tag_value_length": 256,
    "excluded_urls": ["readyz", "livez", "metrics"],
    "otlp": {
        "protocol": "http",
        "endpoint": "http://localhost:4318/v1/traces",
        "http": {"headers": {"Keep-Alive": "timeout=5, max=1000"}},
    },
})
class MyService:
    ...
```

Exporter notes:

- `zipkin` supports Zipkin V2 endpoints; direct Zipkin server URLs commonly include `/api/v2/spans`.
- `jaeger` supports Thrift and gRPC-related configuration. For Thrift, configure `collector_endpoint` or `thrift.agent_host_name` and `thrift.agent_port` as appropriate.
- `otlp` supports HTTP and gRPC-related configuration; docs emphasize HTTP protobuf for OTLP traces.
- Install the matching optional extra in the runtime image or environment: `bentoml[tracing-zipkin]`, `bentoml[tracing-jaeger]`, or `bentoml[tracing-otlp]`.
- OpenTelemetry environment variables can override decorator tracing settings. Always inspect environment variables before assuming the decorator is ignored.

Tracing validation checklist:

1. Confirm `tracing.exporter_type` is one of `zipkin`, `jaeger`, or `otlp`.
2. Confirm `sample_rate` is set above `0`; default/no sample rate can mean no traces are collected.
3. Confirm the matching exporter package is installed in the service runtime.
4. Confirm endpoint/protocol settings match the collector actually running.
5. Confirm `excluded_urls` does not accidentally match the endpoint being tested.
6. Correlate access log trace IDs with collector spans after generating a request.
