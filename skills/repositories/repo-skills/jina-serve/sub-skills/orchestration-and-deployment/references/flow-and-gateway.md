# Flow and Gateway Reference

## Core model

A `Flow` orchestrates one or more `Deployment`s into a directed processing graph. Each Flow also includes a Gateway entrypoint that receives network traffic from the Client.

Key behaviors:

- `Flow().add(...)` adds a Deployment node to the pipeline.
- `Flow.config_gateway(...)` changes Gateway protocol and transport settings.
- `Flow(protocol=["grpc", "http", "websocket"], port=[...])` can expose multiple protocols.
- `Flow.load_config(...)` and `Deployment.load_config(...)` accept YAML or in-memory config structures.
- `Flow.is_flow_ready()` is a quick readiness check suitable for local debugging.
- `Flow.profiling()` reports service timing per node when the installed Jina/DocArray compatibility set still supports the profiling request model. If it fails with a DocArray `Document` import error, use readiness checks and align DocArray/Jina versions before relying on profiling.

## Topology choices

Use `Flow` when you need:

- multiple Executors in sequence,
- branching or merging services,
- protocol selection at the Gateway,
- replicas and shards across services,
- a single Client-facing entrypoint.

Use `Deployment` when you need:

- one Executor served as a network service,
- a simpler service boundary before composing a larger Flow.

## Gateway protocol guidance

- `grpc` is the default and usually the safest baseline.
- `http` is convenient for browser/API debugging and FastAPI-style access.
- `websocket` is useful when the caller expects bidirectional streaming behavior.
- Multiple protocols are allowed, but ports must be aligned with the protocol list.
- TLS is configured on the Gateway for client traffic; internal service traffic is separate.

## Readiness and health

- `jina ping flow grpc://localhost:12345` checks a Flow readiness endpoint.
- `jina ping deployment grpc://localhost:12345` checks a Deployment.
- `jina ping gateway grpc://localhost:12345` checks the Gateway service specifically.

## Export boundaries

Static exports are generated from the Python/YAML configuration. Exporting is not the same as running a Docker/Kubernetes/Cloud deployment. Generate the artifact first, then use the container/cluster/cloud tools only when the environment and credentials are approved.
