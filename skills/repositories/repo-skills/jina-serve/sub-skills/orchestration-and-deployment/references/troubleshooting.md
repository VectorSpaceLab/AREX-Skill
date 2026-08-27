# Orchestration and Deployment Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Flow does not become ready inside `with f:` | One Executor or Gateway in the graph failed to start. | Inspect constructor errors first, then ports, runtime configuration, and dependencies. |
| `Flow.post()` works locally but a deployed service is unavailable | The Python object is gone after the context manager exits. | Use a `Client` against the running endpoint after startup, not `Flow.post()` outside debugging. |
| `jina ping` fails for a local Flow/Deployment | The service never bound the expected port or network/protocol was mismatched. | Confirm the protocol, port, and endpoint URL; check Gateway/Deployment logs and readiness. |
| Multi-protocol Gateway errors or missing endpoints | Port/protocol arrays do not match or the Gateway config was incomplete. | Align the protocol list and port list; ensure each protocol has an available port. |
| Flow YAML with top-level `py_modules` or `uses` is not resolved | The referenced file/module is not reachable from the configuration. | Use `py_modules` and `extra_search_paths` deliberately and keep classes at module top level. |
| Multiprocessing errors when starting a Flow or Deployment | Top-level code is not guarded, or classes are defined too deeply for spawn/fork. | Use `if __name__ == '__main__':` and importable module-level Executor classes. |
| Exported Docker/Kubernetes YAML is rejected by the downstream platform | The artifact was generated but not aligned with runtime/container assumptions. | Regenerate from a minimal Flow and review protocol/image/dependency assumptions before applying. |
| `Flow.profiling()` fails with `Cannot import name 'Document' from 'docarray'` | The profiling helper path expects legacy DocArray v1 `Document` APIs while the environment installed DocArray v2. | Treat profiling as not verified in that environment; use readiness checks and align Jina/DocArray versions if profiling is required. |
| Monitoring or tracing flags appear but no data shows up | Collector/Prometheus/Jaeger backends were not actually running. | Treat export settings as wiring only; bring up the required observability stack separately. |
