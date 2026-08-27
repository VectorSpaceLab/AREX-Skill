# Operational Troubleshooting

## Metrics Missing

Symptoms:

- `GET /metrics` is 404 or empty.
- Default metrics exist but custom metrics do not.
- Custom metrics appear locally with one worker but disappear with multiple workers.

Checks:

1. Confirm service started successfully and `/livez` plus `/readyz` return 200.
2. Confirm `metrics.enabled` is not set to `False` on the service decorator.
3. Generate at least one request to the API path before expecting request counters or custom metrics.
4. Check that metric names are valid Prometheus names and labels are always supplied with values.
5. For multi-worker custom metrics, avoid importing `prometheus_client` too early. Prefer `from bentoml.metrics import Counter, Histogram, Summary, Gauge`, which is designed to defer the underlying Prometheus import until worker setup.
6. If using custom histogram buckets, do not set both `duration.buckets` and `duration.min/max/factor`.

Likely fixes:

- Re-enable `metrics.enabled` or remove the override.
- Call the code path that registers/updates the metric.
- Move metric definition to module scope and use `bentoml.metrics` to avoid multiprocess import-order issues.
- Adjust invalid duration bucket config.

## Traces Missing

Symptoms:

- Access logs show trace IDs but collector UI/backend has no spans.
- Collector receives spans from other apps, not BentoML.
- Decorator tracing config appears ignored.

Checks:

1. Confirm `tracing.exporter_type` is `zipkin`, `jaeger`, or `otlp`.
2. Confirm `tracing.sample_rate` is set above `0`. A zero or unset effective sample rate can mean no traces are collected.
3. Confirm the runtime image/environment includes the matching optional package: `bentoml[tracing-zipkin]`, `bentoml[tracing-jaeger]`, or `bentoml[tracing-otlp]`.
4. Confirm collector endpoint, protocol, and URL path match the exporter. Zipkin commonly needs `/api/v2/spans`; OTLP HTTP commonly uses `/v1/traces`.
5. Inspect OpenTelemetry environment variables. BentoML honors OpenTelemetry APIs, and environment variables can take precedence over decorator settings.
6. Confirm `excluded_urls` does not exclude the tested route.

Likely fixes:

- Install the matching tracing extra in the runtime image.
- Set `sample_rate` during debugging, for example `1.0`, then reduce it for production.
- Correct endpoint/protocol settings or collector port mapping.
- Remove conflicting OpenTelemetry env vars from the service environment.

## Monitoring Data Not Written

Symptoms:

- No `monitoring/<name>/data/` or `schema/` logs appear.
- Schema exists but data is empty.
- A custom monitor log config raises YAML or logging errors.

Checks:

1. Confirm `monitoring.enabled` is `True`.
2. Confirm code enters `with bentoml.monitor("name") as monitor:` and calls `monitor.log(...)` before leaving the context.
3. Confirm `monitoring.options.log_path` is writable relative to the service runtime working directory.
4. If `log_config_file` is set, validate it as Python logging `dictConfig` YAML.
5. In containers, confirm the log directory is mounted or not being discarded with the container filesystem.

Likely fixes:

- Add explicit monitor logging to the API path under test.
- Use a simple default monitor config first, then introduce custom logging YAML.
- Write logs to stdout with a custom logging handler if file access is unsuitable for the environment.

## Invalid Config File or Decorator Config

Symptoms:

- Service import/startup fails before accepting requests.
- Errors mention invalid tracing type, IP address, bucket factor, timeout, or config schema.
- BentoCloud deployment config is accepted by the CLI but service behavior does not match local assumptions.

Checks:

1. Validate value types: timeouts and positive counts must be positive numbers; `workers` must be a positive integer or `"cpu_count"`.
2. Validate `resources.gpu` is positive and `resources.gpu_type` is a string.
3. Validate `tracing.sample_rate` is between `0` and `1`.
4. Validate `tracing.otlp.protocol` is supported and compression is `gzip`, `none`, or `deflate` when set.
5. Validate `http.host`/`grpc.host` are valid IP address strings when explicitly configured.
6. Separate service decorator runtime config from BentoCloud deployment config; scaling policies live in deployment config, not inside the local server runtime fields.

Use `scripts/check_observability_config.py` for local static checks against JSON/YAML config fragments.

## Log Level Confusion

Symptoms:

- Server access logs appear but `bentoml` debug/info library logs do not.
- Debug logs appear locally but not under `bentoml serve` or in containers.
- Health and metrics requests flood access logs.

Checks and fixes:

- Server access logging is configured through `logging.access` on `@bentoml.service`; library logging is Python logging under the `bentoml` namespace.
- Register a handler and level on `logging.getLogger("bentoml")` when using BentoML as a library.
- Use `logging.access.skip_paths` to suppress `/metrics`, `/healthz`, `/livez`, and `/readyz` access logs.
- Avoid rotating file handlers inside service definition when served in child processes; prefer stdout/stderr or platform logging.

## CUDA or GPU Resource Mismatch

Symptoms:

- BentoCloud allocates CPU when a GPU was expected.
- Local service starts but framework reports no CUDA device.
- Multi-worker service crashes with CUDA out-of-memory.
- Worker-to-GPU mapping uses the wrong device.

Checks:

1. Confirm `resources={"gpu": N}` and, for BentoCloud, `gpu_type` or an instance type compatible with GPU capacity.
2. Confirm local container runtime exposes devices, for example with Docker GPU flags. BentoML config alone cannot expose host GPUs.
3. Confirm runtime image includes CUDA-compatible framework packages.
4. Confirm `CUDA_VISIBLE_DEVICES` does not hide needed devices.
5. Confirm code moves models/tensors to `cuda`, `cuda:0`, etc.
6. For multi-worker mapping, remember BentoML's documented `worker_index` pattern is 1-indexed, so CUDA device ID is often `worker_index - 1`.
7. Confirm memory supports one model copy per worker.

Likely fixes:

- Add GPU resources to service/deployment planning and install the correct framework runtime in the image.
- Reduce worker count or switch to one model per GPU.
- Set `CUDA_VISIBLE_DEVICES` explicitly in local tests.

## Batching, Concurrency, and Latency Symptoms

Symptoms:

- High latency under load despite healthy endpoints.
- Request rejections or `ServiceUnavailable`-like behavior.
- BentoCloud does not scale when GPU utilization is high.
- External queue adds unexpected latency.

Checks:

1. Distinguish `max_concurrency` from BentoCloud `concurrency`.
2. For BentoCloud, set `traffic.concurrency`; otherwise autoscaling may rely on CPU utilization.
3. Align `traffic.concurrency` with adaptive/continuous batch size for batching services.
4. If `external_queue` is enabled, ensure `concurrency` is set and the additional latency is acceptable.
5. For CPU-bound work, increase `workers` only if memory can hold multiple model copies.
6. For long-running inference, increase `traffic.timeout` only after confirming throughput and queue behavior.

Likely fixes:

- Stress test locally or on BentoCloud to find sustainable concurrency.
- Set `traffic.concurrency` slightly below observed per-replica capacity.
- Add autoscaling min/max boundaries and stabilization windows in deployment config.
- Reduce batching latency or batch size if queueing dominates response time.

## Autoscaling or Gateway Misconfiguration

Symptoms:

- Deployment scales too slowly, too aggressively, or not at all.
- Scale-to-zero requests appear stuck.
- Direct deployment endpoint works but gateway endpoint fails.
- Gateway routes to the wrong upstream deployment.

Checks:

1. Confirm deployment scaling min/max and policy windows match the intended behavior.
2. Confirm service `traffic.concurrency` is configured for autoscaling.
3. For scale-to-zero, expect cold-start delay and external queue behavior; use `/readyz` to trigger scale-up when needed.
4. For gateways, confirm protocol, model/request routing fields, load balancing strategy, and upstream deployment readiness.
5. Compare direct deployment endpoint health and response with gateway response.
6. Confirm cloud credentials and permissions before attempting BentoCloud changes.

Likely fixes:

- Add or tune `traffic.concurrency` and deployment replica bounds.
- Adjust stabilization windows to reduce flapping or speed up reaction.
- Fix gateway protocol/model routing metadata rather than changing service code when direct endpoint behavior is correct.
