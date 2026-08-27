---
name: client-and-protocols
description: "Use Jina Client calls, protocol selection, streaming, retries,
  callbacks, request parameters, and target-executor routing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Client and Protocols

Use this sub-skill when a task involves sending requests to a running Flow or Deployment, selecting gRPC/HTTP/WebSocket protocols, configuring retries or callbacks, streaming generators, or debugging protocol/TLS and request-routing problems.

## Read first

- [Client API](references/client-api.md) for `Client` construction and `post()` semantics.
- [Streaming and retries](references/streaming-and-retries.md) for async clients, callbacks, batching, target executors, and failure handling.
- [Troubleshooting](references/troubleshooting.md) for protocol mismatch, TLS, callback, retry, ordering, and streaming issues.
- Use [smoke_client_roundtrip.py](scripts/smoke_client_roundtrip.py) for a tiny local roundtrip check when a Flow or Deployment is already running.

## Quick example

```python
from jina import Client
from docarray import BaseDoc

client = Client(host="grpc://localhost:12345")
resp = client.post("/", BaseDoc(), return_responses=True)
```

## Boundaries

- This sub-skill owns the caller side. Use [orchestration-and-deployment](../orchestration-and-deployment/SKILL.md) to create or configure the Flow/Gateway being called.
- Use [executor-service-patterns](../executor-service-patterns/SKILL.md) for request endpoint definitions and service logic.
- Use [observability-and-production](../observability-and-production/SKILL.md) for endpoint health, service mesh, Docker/Kubernetes, and production connectivity.
