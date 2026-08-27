# Serving troubleshooting

Use the smallest check that distinguishes configuration, dependency, network,
registry, and model-operation failures. Keep credentials and Authorization
headers redacted.

## Static configuration and import

| Symptom | Likely boundary | Check and correction |
|---|---|---|
| TOML parse error | syntax | run `model_config_check.py`; fix table spelling, quoting, array-of-table syntax, or types |
| model entry ignored or wrong provider class | discriminator | use exact `provider` value; provider is selected by the registered parameter class |
| missing required model field | model role/config | every entry needs `name`; local paths/backend fields and provider credentials must be supplied as applicable |
| `${env:...}` remains unresolved | environment | export the exact variable before starting; use `:-default` only for safe non-secret defaults |
| key appears in logs | observability hygiene | stop, rotate the exposed credential, redact logs/reports; never echo resolved config |
| import error for vLLM/torch/llama.cpp/MLX/bitsandbytes | optional backend | install/prepare the backend in the target runtime or switch to a verified proxy/CPU path; do not claim the backend works |
| local path not found | artifact/root | use a path readable by the service process; remember relative paths are resolved against DB-GPT's runtime root, not an arbitrary shell directory |
| chat works but RAG fails | role pairing | configure/test a distinct embedding model and endpoint; a chat API is not automatically an embedding API |

## Provider and endpoint

### OpenAI-compatible endpoint missing embedding configuration

If an OpenAI-compatible LLM parses but knowledge/RAG reports no embedding model,
this is an incomplete configuration, not an embedding runtime success. Add a
separate `[[models.embeddings]]` entry with its model name, provider, embedding
URL/base URL as expected by that provider adapter, and the matching credential.
Then validate again and run an embedding request. If the endpoint supports chat
only, choose a real embedding provider instead.

### Authentication failures

For `401`, `403`, or provider authentication errors:

1. Confirm the provider value and model name.
2. Confirm the environment variable is set in the service's process environment,
   not only in an interactive shell.
3. Confirm `api_base`/`api_url` targets the correct API version and deployment.
4. Check provider account permissions, quota, and network proxy settings.
5. Retry a minimal request with the key redacted from output.

Do not fix an authentication error by putting a key in a generated skill or
committing it to TOML.

### Connection refused, timeout, or 404

Check the URL from the same network namespace as DB-GPT. `localhost` inside a
container or remote worker refers to that container/host. Confirm the provider
or Ollama process is listening, the path includes the required API prefix, and
firewall/proxy rules permit it. A successful TCP connection does not prove the
model name or request schema is valid.

## Controller, worker, and API server

| Symptom | Check order | Correct interpretation |
|---|---|---|
| controller unreachable / timeout / 502 | controller bind host/port, process log, network route, `controller_addr`, health endpoint | model CLI discovery/start is not successful; stop and fix reachability |
| worker process starts but absent from `model list` | worker `register`, `controller_addr`, register host, controller logs, unique port | no registry proof; worker may be serving only locally or failed registration |
| worker appears unhealthy | heartbeat interval/timeout, controller route, worker process/log, advertised host | registry health is false/stale; do not route traffic to it |
| registry shows healthy but generation fails | issue minimal generate/embedding call; inspect worker/model/provider logs | registry only proves heartbeat, not model capability |
| API server starts but `/v1/models` fails | API `controller_addr`, controller health, API log, API key/CORS | gateway cannot discover a worker; API process alone is not deployment |
| `/v1/models` works but chat/embedding fails | select the exact model name and role; inspect upstream provider/backend | routing is alive; selected model operation remains failed |
| port already in use | list local listeners and compare web/controller/worker/API ports | assign unique ports; do not kill an unrelated process blindly |
| daemon command returns but no service | inspect daemon log/PID and listen socket | fork success is not service success; rerun foreground for diagnosis |

The default model service ports are controller `8000`, worker `8001`, and model
API server `8100`; webserver commonly uses `5670`. Treat them as defaults, not
universal assignments. All split workers need a unique advertised port.

### Unreachable-controller synthetic case

For a command such as:

```bash
dbgpt model --address http://127.0.0.1:9 list
```

an expected result is an actionable connection error and an explicit
“deployment not verified/failed” outcome. It is incorrect to report a model as
started because a local config parsed or because a start request was attempted.
The same rule applies when dynamic `model start` option discovery returns a
remote 502.

## Local model and hardware failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| model file/tokenizer download stalls | missing cache/network/access | use an approved preloaded path or verify network; record download as incomplete |
| CUDA unavailable | torch/backend mismatch or no compatible runtime | run a backend-specific probe; use CPU/proxy if appropriate; keep CUDA unverified |
| CUDA OOM | model/context/batch too large | reduce model, context, concurrency, or GPU memory target; consider tested quantization; record exact settings |
| quantization rejects CPU | bitsandbytes 4/8-bit path requires CUDA in this version | remove quantization for CPU smoke or prepare a CUDA environment; do not call it CPU-compatible |
| vLLM startup error | vLLM/torch/model format/GPU/parallelism mismatch | verify versions, model path, dtype, tensor/pipeline sizes, VRAM; no claim from config parse |
| llama.cpp child server timeout | binary path, GGUF path, port, startup timeout, incompatible binary | run the binary health check in the target environment and inspect child log; avoid opaque installers |
| slow CPU generation | expected local-backend limitation | use a tiny model for smoke or a proxy; do not extrapolate production latency |

## Logs and redaction

Prefer foreground startup while diagnosing. For daemon mode, find the configured
log directory, identify the service-specific log, and inspect the first error
plus the final bind/ready line. Report:

- service role and configured host/port;
- controller/provider URL without credentials;
- model name and worker role;
- highest verification level reached;
- exact non-secret exception and next check.

Never report resolved `api_key`, bearer tokens, cookies, full authorization
headers, private model paths, or local inspection-environment paths.
