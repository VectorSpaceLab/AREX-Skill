---
name: jina-serve
description: "Use Jina-serve to build, serve, orchestrate, call, observe, and
  deploy AI microservices and pipelines with the jina Python package."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Jina-serve

Use this repo skill when a task involves the `jina` Python package, Jina-serve, `Executor`, `Deployment`, `Flow`, `Gateway`, `Client`, DocArray-based service IO, Jina CLI commands, or Jina cloud-native deployment surfaces.

This skill is self-contained for the versioned Jina-serve package baseline in [repo provenance](references/repo-provenance.md). It does not require the original repository checkout.

## Quick start

Install a public package release:

```bash
pip install "jina==3.34.1"
```

For the current latest compatible release, use:

```bash
pip install -U jina
```

Verify the install:

```bash
python -c "from jina import Executor, Flow, Deployment, Client, requests; import jina; print(jina.__version__)"
jina --version
```

For a richer read-only diagnostic, run the bundled helper:

```bash
python scripts/check_jina_install.py
```

Read [install and compatibility](references/install-and-compatibility.md) before changing dependency variants, Python versions, DocArray/Pydantic/Protobuf/GRPC pins, or optional service extras.

## Route by task

- Use [cli-and-configuration](sub-skills/cli-and-configuration/SKILL.md) for install variants, CLI command selection, `jina help`, `jina -vf`, YAML/JAML, environment variables, telemetry opt-out, schemas, autocomplete, and parser inspection.
- Use [executor-service-patterns](sub-skills/executor-service-patterns/SKILL.md) to write `Executor` classes, `@requests` endpoints, DocArray schemas, standalone `Deployment`s, dynamic batching, Executor templates, Hub packaging, and GPU-executor prerequisites.
- Use [orchestration-and-deployment](sub-skills/orchestration-and-deployment/SKILL.md) for multi-Executor `Flow`s, Gateway protocols, Flow/Deployment YAML, readiness/profiling, replicas/shards, topology decisions, and static exports to Docker Compose or Kubernetes YAML.
- Use [client-and-protocols](sub-skills/client-and-protocols/SKILL.md) for `Client` construction, request batching, async/streaming calls, retries, callbacks, parameters, target executors, protocol/TLS mismatches, and response handling.
- Use [observability-and-production](sub-skills/observability-and-production/SKILL.md) for health checks, monitoring, OpenTelemetry, Prometheus/Grafana, Docker Compose operations, Kubernetes/JCloud/Hub boundaries, custom Gateway/FastAPI surfaces, and production troubleshooting.

## Public API anchors

Common public imports verified for this baseline:

```python
from jina import Executor, Flow, Deployment, Client, requests
from jina import dynamic_batching, monitor
from docarray import BaseDoc, DocList
```

The core mental model:

1. Define document schemas with DocArray `BaseDoc` and `DocList`.
2. Implement service logic in an `Executor` subclass and expose methods with `@requests`.
3. Serve one Executor with `Deployment`, or compose several services with `Flow`.
4. Expose traffic through a `Gateway` using gRPC, HTTP, WebSocket, or multi-protocol settings.
5. Send data with `Client.post()` or streaming/async client APIs.
6. Add observability, health checks, container/cloud deployment, and credentials only when the target environment requires them.

Read [API overview](references/api-overview.md) for signatures and route ownership.

## Common decisions

- Prefer explicit `Client` usage for production callers; `Flow.post()` and `Deployment.post()` are convenient for local debugging while the object is in scope.
- Use YAML for production `Deployment`/`Flow` definitions when you need reproducible config independent of Python service logic.
- Keep user model dependencies in the Executor project requirements, not in the global Jina install. Jina orchestrates services but does not choose torch, TensorFlow, diffusers, or GPU wheels for you.
- Treat Docker, Kubernetes, JCloud, Hub, and full OpenTelemetry stacks as optional operational surfaces that may need credentials, Docker/K8s clusters, network access, or long-running services.

## Troubleshooting first stops

- Cross-cutting install/import/runtime issues: [root troubleshooting](references/troubleshooting.md).
- CLI/YAML/env issues: [CLI troubleshooting](sub-skills/cli-and-configuration/references/troubleshooting.md).
- Executor/Deployment errors: [Executor troubleshooting](sub-skills/executor-service-patterns/references/troubleshooting.md).
- Flow/Gateway topology or export errors: [Flow troubleshooting](sub-skills/orchestration-and-deployment/references/troubleshooting.md).
- Client/protocol/retry issues: [Client troubleshooting](sub-skills/client-and-protocols/references/troubleshooting.md).
- Production/observability/cloud issues: [Production troubleshooting](sub-skills/observability-and-production/references/troubleshooting.md).
