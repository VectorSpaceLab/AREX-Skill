---
name: observability-and-operations
description: "Configure BentoML logging, metrics, monitoring/data collection,
  tracing, resource settings, scaling/autoscaling, gateways, testing, and
  production operational troubleshooting. Use when work involves operational
  knobs rather than defining APIs, packaging Bentos, basic serving, or cloud
  deployment CRUD."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# BentoML Observability and Operations

Use this sub-skill when a BentoML Service needs production diagnostics, telemetry, resource/concurrency tuning, or operational validation.

## Route Here For

- Access logging controls, `bentoml` library logger setup, trace/log correlation fields, and log-level confusion.
- Prometheus `/metrics`, default/custom metric definitions, histogram bucket tuning, and missing metric debugging.
- `bentoml.monitor(...)` data collection, local monitor log files, OTLP monitoring targets, and plugin collector caveats.
- OpenTelemetry tracing with `zipkin`, `jaeger`, or `otlp`, including missing exporter dependencies and environment-variable precedence.
- `resources`, `workers`, `traffic`, `runner_probe`, health endpoints, GPU allocation, CUDA visibility, batching/concurrency symptoms, and BentoCloud autoscaling/gateway planning.
- Operational testing patterns for health, metrics, ASGI/HTTP behavior, and safe BentoCloud E2E test design.

## Boundaries

- For service class and API decorator shape, route to `../service-authoring/SKILL.md`.
- For `bentoml serve`, HTTP/gRPC clients, and server startup basics, route to `../serving-and-clients/SKILL.md`.
- For `bentoml deploy`, deployment CRUD, secrets, and cloud CLI management, route to `../cli-and-cloud/SKILL.md`.
- For Bento build/runtime image and package configuration, route to `../packaging-and-containerization/SKILL.md`.

## Core Workflow

1. Identify the operating target: local serve, container runtime, BentoCloud Deployment, Gateway, or test-only environment.
2. Place runtime config on the `@bentoml.service(...)` decorator unless the project intentionally uses a deployment config file for BentoCloud-only scaling policies.
3. Keep local controls separate from BentoCloud controls: `max_concurrency`, `workers`, metrics, logs, tracing, and monitoring affect local/runtime behavior; `resources`, `traffic.concurrency`, `traffic.external_queue`, scaling min/max, policies, and gateways are BentoCloud scheduling/routing concerns.
4. Verify safe endpoints first: `/livez`, `/readyz`, `/healthz`, then `/metrics`; only then debug external collectors or BentoCloud routing.
5. Use `references/troubleshooting.md` for symptom-to-cause triage before changing unrelated service code.

## References

- `references/observability.md`: logging, metrics, monitoring, tracing, and endpoint checks.
- `references/configuration.md`: runtime config fields, resources/workers/GPU, traffic, autoscaling, gateways, and testing plans.
- `references/troubleshooting.md`: operational symptoms and fixes.

## Bundled Scripts

- `scripts/check_observability_config.py`: validates a local JSON/YAML service or deployment-like config file for common observability/operations mistakes.
- `scripts/resource_plan_template.py`: emits a self-contained local/BentoCloud resource, GPU, autoscaling, gateway, and verification plan template.

Both scripts are local-only helpers. They do not contact BentoCloud, Prometheus, tracing backends, gateways, or external collectors.
