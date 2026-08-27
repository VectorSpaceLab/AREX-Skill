# Observability and Debugging

## Metrics

Triton exposes Prometheus text metrics at `http://<host>:8002/metrics` by default. Use:

```bash
curl -s http://localhost:8002/metrics | head
```

Important flags include:

- `--allow-metrics=false` to disable all metrics.
- `--allow-gpu-metrics=false` and `--allow-cpu-metrics=false` to disable device-specific metrics.
- `--metrics-port`, `--metrics-address`, and `--metrics-interval-ms` to configure the endpoint and interval.
- `--metrics-config counter_latencies=false` or `--metrics-config histogram_latencies=true` for latency families where supported.

GPU metrics require a GPU-enabled runtime; CPU-only launches should not be expected to expose meaningful GPU utilization.

## Logs and readiness

- Increase log detail with verbose server flags when debugging model load or protocol behavior.
- A model that fails to load can keep readiness non-200 under strict readiness. Decide whether `--strict-readiness=false` is acceptable for the service objective.
- Search logs for `UNAVAILABLE`, `Invalid argument`, missing backend/model file, unsupported datatype/dims, and version mismatch messages.

## Performance first steps

- Use perf analyzer/model analyzer in an approved runtime to separate client, queue, compute input, compute infer, and compute output bottlenecks.
- Enable tracing only when needed; tracing can affect performance and creates extra artifacts.
- Interpret counters carefully: request count, inference count, and execution count differ when batching is enabled.
