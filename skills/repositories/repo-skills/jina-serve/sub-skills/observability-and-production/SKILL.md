---
name: observability-and-production
description: "Use Jina health checks, monitoring, OpenTelemetry, Docker Compose,
  Kubernetes, JCloud, Hub, and production troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Observability and Production

Use this sub-skill when the task involves health checks, Prometheus/Grafana or OpenTelemetry instrumentation, Docker Compose or Kubernetes export/deploy, Jina Cloud, Executor Hub, custom Gateway surfaces, or troubleshooting production connectivity and runtime issues.

## Read first

- [Production deployment reference](references/production-deployment.md) for Docker Compose, Kubernetes, JCloud, Hub, and service-boundary guidance.
- [Observability reference](references/observability.md) for monitoring, tracing, metrics, and health-check behavior.
- [Troubleshooting](references/troubleshooting.md) for container, cloud, credential, service-mesh, and observability failures.
- Use [check_jina_endpoint.py](scripts/check_jina_endpoint.py) for a safe health-check helper against a running endpoint.
- Use [export_gateway_openapi.py](scripts/export_gateway_openapi.py) to generate an OpenAPI schema snapshot from Gateway config without editing source files.

## Scope

- This sub-skill covers production surfaces that are often optional or environment-specific.
- It intentionally does not replace the core service, topology, or client sub-skills.
- Treat remote cloud/login/push/pull commands as credentialed or network-bound until explicitly approved.
