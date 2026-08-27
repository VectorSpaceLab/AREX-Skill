# Metrics and observability

Use this reference for Prometheus metrics, log handling, audit visibility, and
optional OpenTelemetry export.

## Metrics endpoints

- Supervisor metrics live at `<endpoint>/metrics`.
- Worker metrics use the separate exporter host and port configured for the
  worker or local process.
- `XINFERENCE_DISABLE_METRICS=1` disables the supervisor `/metrics` endpoint
  and prevents the worker exporter from starting.

Representative metric families:
- Supervisor API counters: requests, responses, status codes, exceptions.
- Worker inference metrics: generated tokens, input/output token counters,
  and time-to-first-token.
- Cluster metrics: worker counts, model status, GPU and memory gauges.
- Security counters: active API keys, expired API keys, banned IPs, and banned
  key pairs.

## Log handling

| Variable | Default | Meaning |
| --- | --- | --- |
| `XINFERENCE_LOG_CONSOLE` | `true` | Emit logs to the console as well as files. |
| `XINFERENCE_LOG_FORMAT` | `text` | Log formatting mode. |
| `XINFERENCE_LOG_DOWNLOAD_PROGRESS` | `sampled` | How download progress is recorded when console logging is off. |
| `XINFERENCE_LOG_ROTATION` | `daily+size` | Log rotation strategy. |
| `XINFERENCE_LOG_RETENTION_DAYS` | `30` | Log retention window. |
| `XINFERENCE_LOG_MAX_BYTES` | `104857600` | Maximum log-file size. |
| `XINFERENCE_LOG_BACKUP_COUNT` | `300` | Number of rotated log files kept. |
| `XINFERENCE_LOG_DIR` | `<XINFERENCE_HOME>/logs` | Log directory shared by application and audit logs. |

Operational notes:
- Local deployments combine supervisor and worker logs into one cluster log tree.
- Distributed deployments create separate supervisor and worker log trees.
- Audit logs live at `<XINFERENCE_LOG_DIR>/audit.log`.

## Audit visibility

The audit trail records authenticated API activity and security events.
It is not a full HTTP access log.

| Variable | Default | Meaning |
| --- | --- | --- |
| `XINFERENCE_AUDIT_LOG_RETENTION_DAYS` | `90` | Retention window for audit logs. |
| `XINFERENCE_ES_URL` | unset | Switch Audit Center search to Elasticsearch. |
| `XINFERENCE_AUDIT_ES_INDEX` | `xinference-audit-*` | Elasticsearch index pattern for audit data. |

Use Elasticsearch only when the audit pipeline is actually sending data there.
If `XINFERENCE_ES_URL` is unset, the audit search falls back to local files.

## Optional OpenTelemetry

OpenTelemetry is disabled unless enabled explicitly.

| Variable | Default | Meaning |
| --- | --- | --- |
| `XINFERENCE_ENABLE_OTEL` | `false` | Enable OTEL export and instrumentation. |
| `XINFERENCE_OTLP_BASE_ENDPOINT` | `http://localhost:4318` | Base OTLP endpoint. |
| `XINFERENCE_OTLP_TRACE_ENDPOINT` | `<base>/v1/traces` | Trace export endpoint. |
| `XINFERENCE_OTLP_METRIC_ENDPOINT` | `<base>/v1/metrics` | Metric export endpoint. |
| `XINFERENCE_OTLP_API_KEY` | unset | Authorization bearer token for OTLP requests. |
| `XINFERENCE_OTEL_EXPORTER_OTLP_PROTOCOL` | `http/protobuf` | OTLP transport protocol. |
| `XINFERENCE_OTEL_EXPORTER_TYPE` | `otlp` | Exporter family. |
| `XINFERENCE_OTEL_SAMPLING_RATE` | `0.1` | Trace sampling rate. |

If OTEL is unavailable at runtime, Xinference continues without it rather than
failing the process.

## Quick checks

- `curl <endpoint>/status` for basic liveness.
- `curl <endpoint>/metrics` for supervisor metrics.
- Confirm the worker exporter host and port when worker metrics are expected.
- If `/metrics` returns 404, check `XINFERENCE_DISABLE_METRICS` first.
