# Observability and Logging Reference

## When to read

Read this when enabling traces/metrics/logs, debugging missing observability
records, selecting a backend, or reviewing changes to observability services.

## Three observability paths

| Path | Storage/backend | Typical use | Key flags |
| --- | --- | --- | --- |
| Internal observability | ContextForge database | self-contained traces and Admin UI views | `OBSERVABILITY_ENABLED`, trace retention/sample settings |
| OpenTelemetry | OTLP-compatible backend | distributed tracing and APM | `OTEL_ENABLE_OBSERVABILITY`, `OTEL_TRACES_EXPORTER`, `OTEL_EXPORTER_OTLP_ENDPOINT` |
| Prometheus | Prometheus scrape endpoint | time-series monitoring/alerts | `ENABLE_METRICS`, metrics token and handler filters |

These systems can run together. Internal observability is convenient for local
or small deployments; OpenTelemetry and Prometheus are common production
integrations.

## What is traced or measured

- HTTP requests and route timing.
- Tool invocations.
- Prompt rendering.
- Resource fetching.
- Gateway federation and upstream calls.
- Plugin execution and violations when enabled.
- A2A interactions and MCP protocol operations where instrumented.
- Errors, exceptions, correlation IDs, and performance metrics.

## Transaction behavior

Observability write operations use independent database sessions and commit
best-effort records immediately. This is intentional:

- Trace/span/event records can survive even when the main request fails.
- Observability is not atomic with the main request transaction.
- Query operations still use request-scoped sessions so RBAC/token scoping can
  filter read access.
- High traffic with tracing enabled increases database connection demand; size
  pools appropriately for production.

Audit logging follows a similar separate-session pattern when no explicit DB is
supplied. Existing service call sites should not pass their request-scoped DB
session into audit logging as a routine shortcut.

## Internal observability quick path

1. Enable internal observability.
2. Start the gateway with a production-appropriate database if retention or
   concurrency matters.
3. Use Admin UI observability pages or observability API routes to inspect
   traces, spans, events, stats, and query performance.
4. Configure retention and cleanup if traces are long-lived.

## OpenTelemetry quick path

1. Enable OTEL observability and set exporter type.
2. Point `OTEL_EXPORTER_OTLP_ENDPOINT` to the collector/backend.
3. Set service name/version attributes consistently across deployments.
4. Confirm the collector accepts gRPC or HTTP as configured.
5. Use trace IDs/correlation IDs to connect ContextForge logs to backend spans.

## Prometheus quick path

1. Enable metrics endpoint.
2. Generate a scrape token with suitable metrics permission.
3. Configure Prometheus with Authorization header.
4. Check excluded handler patterns if expected routes are absent.
5. Add custom labels for environment/region only when they have bounded
   cardinality.

## Logging and SIEM

ContextForge has structured logging, log storage/search, security events, audit
trail queries, performance metrics, and SIEM destination management. When
reviewing logging changes:

- Preserve correlation IDs.
- Redact tokens, passwords, OAuth secrets, API keys, and sensitive headers.
- Use security event severity/category fields for security findings.
- Keep SIEM destination URL handling controlled by allowlists and validation.
- Ensure support bundles sanitize environment and log material.

## Choosing a validation level

- Config-only change: parse settings and run targeted unit tests.
- Trace/span schema or DB change: add migration/unit tests and query tests.
- OTEL exporter change: run an OTEL smoke against a local collector when
  available; otherwise document the skipped external backend.
- Prometheus metric change: scrape endpoint or metric registry test.
- Plugin observability change: plugin unit tests plus parity E2E if public MCP
  path behavior changes.
