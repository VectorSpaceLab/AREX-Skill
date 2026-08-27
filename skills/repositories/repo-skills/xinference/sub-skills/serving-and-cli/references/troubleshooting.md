# Troubleshooting

Use this page for CLI, deployment, and placement failures. If the issue is about Python client payloads, model-family/backend selection, or auth/metrics policy, route to the sibling sub-skill instead.

## Launch validation

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `--model-engine is required for LLM models.` | An LLM launch omitted the engine flag. | Add `-en/--model-engine` or query valid engines first with `engine`. |
| `Xinference does not support this inference engine ...` | The selected backend is not valid for that model/format/quantization combination. | Route to `models-and-backends` and choose a supported backend or model family. |
| The launch never becomes ready or takes a long time. | The model is downloading, a per-model virtual environment is being created, or the backend needs extra packages. | Expect the first launch to be slower and verify backend/hardware coverage before retrying. |
| A launch fails after adding extra flags. | Extra kwargs were not passed as `--key value` pairs. | Keep all backend-specific extras after the known flags and prefix each name with `--`. |

## Placement and cluster shape

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Worker ip address ... is not in the cluster` | The worker address does not match a registered worker. | Use the exact registered `IP:port` and verify the worker joined the cluster. |
| `n_worker cannot be larger than the number of available workers` | The request asked for more workers than are running. | Lower `--n-worker` or add workers first. |
| `duplicate indexes` or a GPU placement error | `--gpu-idx` contains invalid or repeated indexes, or the request conflicts with the current allocation. | Use unique integer indexes and keep `--n-gpu` consistent with the placement. |
| `list` shows stale or missing models after a worker failure | A worker temporarily failed and the supervisor is using cached state. | Retry after the worker recovers; the list may refresh once the cluster is healthy again. |

## Registration and cache commands

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `register` fails immediately | Wrong config file path or bad model type. | Recheck `--file`, `--model-type`, and the target worker address. |
| `unregister` or `terminate` does nothing | Wrong model name or UID. | Confirm the exact `--model-name` or `--model-uid` from `list`/`registrations`. |
| `cached` or `remove-cache` does not find the target | Wrong model name/version or worker scope. | Use the exact parser flag form and the full worker address; remember that `remove-cache` is destructive. |
| `stop-cluster` or `remove-cache` prompts before acting | The command is intentionally protected by confirmation. | Review the target carefully; use `--check` only when you intentionally want to skip the interactive prompt flow. |

## Memory and compatibility helpers

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `cal-model-mem` exits early | `--kv-cache-dtype` is invalid. | Use `8`, `16`, or `32`. |
| `vllm-models` does not list the desired family | The family is not vLLM-compatible. | Treat that as a backend-selection issue and route to `models-and-backends`. |
| `engine` returns no useful combination | The requested name, format, size, or quantization does not match a supported tuple. | Query again with fewer filters, then narrow down from the supported combinations. |

## Container and remote access

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| The service works locally but not from another machine | The bind address is loopback-only or the port is not published. | Use `0.0.0.0` for exposed services and map the container or host port. |
| Docker GPU launches fail or hang on startup | GPU access or shared-memory settings are missing. | Ensure the container has GPU access and adequate shared memory for the selected backend. |

## Escalation boundaries

- Python client request shapes, streaming bodies, and OpenAI-compatible payloads -> `client-and-api`
- Engine choice, model family choice, and optional backend packaging -> `models-and-backends`
- Auth system policy, metrics policy, and environment policy -> `operations-and-security`
