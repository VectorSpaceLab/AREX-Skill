# Production Deployment Reference

## Health checks

Use the CLI to check running services:

```bash
jina ping deployment grpc://localhost:12345
jina ping flow grpc://localhost:12345
jina ping gateway grpc://localhost:12345
jina ping executor localhost:12346
```

The repo also ships small health-check helpers in `jina/resources/health_check/`, but this skill uses the bundled helper script instead of the source checkout.

## Docker Compose

Generate a compose file from a Flow when all Executors are Docker-compatible:

```python
from jina import Flow
Flow(...).to_docker_compose_yaml("docker-compose.yml")
```

Run the generated compose file only when Docker is available and the image/dependency assumptions are correct.

## Kubernetes

Generate Kubernetes manifests when the Flow is ready for container orchestration:

```python
from jina import Flow
Flow(...).to_kubernetes_yaml("config")
```

This does not create or modify the cluster. Apply the YAML only with approved cluster access.

## Jina Cloud and Hub

- `jina cloud` / `jcloud` manage Jina AI Cloud deployments, secrets, jobs, and Flow lifecycle.
- `jina hub` creates and pushes/pulls Executors to Executor Hub.
- Both surfaces can require credentials, Docker, and network access. Use help-only checks unless the environment and approval explicitly allow remote operations.

## Custom Gateway surfaces

Use custom HTTP endpoints or OpenAPI schema export when you need to inspect the Gateway API surface or integrate with other services. Keep the runtime helper inside the generated skill tree rather than depending on the source repo. If the Gateway/FastAPI OpenAPI helper fails because of a Pydantic/FastAPI compatibility error, either align the app's dependency set or use `jina export schema --json-path <file>` for Jina's general API schema.
