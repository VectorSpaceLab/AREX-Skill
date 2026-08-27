# Production and Observability Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `jina ping` fails but the service looked ready in logs | Wrong protocol/host/port or stale port mapping. | Verify the exact endpoint emitted by the service and ping that URL. |
| Metrics/traces settings produce no dashboard data | Collector/Prometheus/Jaeger stack is not running or not pointed at the exporter. | Bring up the external observability stack and match the exporter host/port. |
| Docker Compose export works but containers fail later | The Flow uses non-Docker-compatible Executors or mismatched image versions. | Keep the Flow export static until the service images and dependency versions are aligned. |
| Kubernetes manifest deploy fails | Missing cluster access, Linkerd/service-mesh dependencies, or incompatible YAML. | Generate from a tiny Flow first, then verify the cluster prerequisites before applying. |
| `jina cloud` or `jina hub` asks for auth or remote access | Credentialed, network-bound operations. | Use help-only checks unless the user explicitly approves login/push/pull/deploy actions. |
| Health endpoint script cannot connect | The target service is down or the protocol is wrong. | Check service logs and the exact port/protocol before retrying. |
| Jina metrics show counts but not the expected route names | The service nodes have not processed traffic yet, or the wrong protocol path was used. | Send a real request first and re-check the metrics endpoint. |
| FastAPI/custom Gateway surface does not expose the expected route | The Gateway customization hook is wrong or the runtime is not using the intended app. | Inspect the Gateway configuration and keep custom routes separate from Flow topology. |
| Gateway OpenAPI schema export fails with a Pydantic/FastAPI model error | The installed Jina, DocArray, FastAPI, and Pydantic versions are not mutually compatible for Gateway internals. | Align those dependency versions for the target app, or use `jina export schema --json-path <file>` when you only need Jina's general API schema. |
