# Serving workflows

These workflows are intentionally explicit about what is being verified. They
use a config file with redacted environment placeholders and do not assume
credentials, model downloads, CUDA, or external services.

## 1. Proxy-backed unified webserver

Use this for the smallest CPU-first integration. Put a chat model and a
separate embedding model in the TOML, for example:

```toml
[models]
[[models.llms]]
name = "chat-model"
provider = "proxy/openai"
api_base = "${env:OPENAI_API_BASE:-https://api.openai.com/v1}"
api_key = "${env:OPENAI_API_KEY}"

[[models.embeddings]]
name = "embedding-model"
provider = "proxy/openai"
api_url = "${env:EMBEDDING_API_URL:-https://api.openai.com/v1/embeddings}"
api_key = "${env:OPENAI_API_KEY}"
```

Then:

```bash
python scripts/model_config_check.py config.toml
export OPENAI_API_KEY='...'
dbgpt start webserver --config config.toml
```

The exact webserver options vary with setup/profile integration; use
`dbgpt start webserver --help` in the installed package. A config parser pass
is not a provider call. Confirm the web process bind port, provider request,
and (if using knowledge/RAG) an embedding request separately. General profile
and workspace lifecycle belongs to `setup-and-cli`.

For a unified, non-light webserver, DB-GPT initializes its model manager in the
same application process and uses the model entries from `[models]`. In a
light/remote arrangement, the webserver does not start embedded model workers;
it uses the configured controller address and remote model services instead.
Do not mix the two modes accidentally.

## 2. Manual split cluster

Use this topology when workers need independent ports or machines:

```text
webserver :5670  -> controller :8000 -> llm worker :8001
                                      -> text2vec worker :8002
                                      -> reranker worker :8003 (optional)
optional model API :8100 -> controller :8000
```

### Start controller

Create a controller config with `[service.model.controller]` and run:

```bash
dbgpt start controller --config controller.toml
```

The controller is a registry/router. It does not load a model. Verify its
health endpoint and that the bind port is listening before starting a worker.

### Start worker

A worker config contains `[service.model.worker]` and a model collection
appropriate to the worker. Use a unique port for each worker:

```toml
[service.model.worker]
host = "0.0.0.0"
port = 8001
worker_type = "llm"
controller_addr = "http://127.0.0.1:8000"
register = true
send_heartbeat = true

[models]
[[models.llms]]
name = "chat-model"
provider = "proxy/openai"
api_base = "${env:OPENAI_API_BASE:-https://api.openai.com/v1}"
api_key = "${env:OPENAI_API_KEY}"
```

Start it with:

```bash
dbgpt start worker --config worker.toml
```

For `text2vec`, set `worker_type = "text2vec"` and provide a real embedding
entry. For a reranker use `worker_type = "reranker"` and a reranker entry. A
worker with `register = true` must be able to reach the controller from its own
network namespace; `127.0.0.1` means the worker host itself, not necessarily
the controller host.

### Verify worker registration

```bash
dbgpt model --address http://127.0.0.1:8000 list
```

Interpret the output as registry evidence. Require the intended model role,
host/port, `healthy = True`, and a recent heartbeat. Then issue a minimal
completion/embedding/rerank operation against the intended worker or API
server. If the command cannot reach the controller, report the deployment as
unverified/failed; do not infer success from the worker process log alone.

## 3. Optional model API server

The API server translates OpenAI-style requests to registered workers. Configure
it with `[service.model.api]`:

```toml
[service.model.api]
host = "0.0.0.0"
port = 8100
controller_addr = "http://127.0.0.1:8000"
api_keys = "${env:DBGPT_MODEL_API_KEYS:-}"
cors_allowed_origins = "http://localhost:5670"
```

Start it after the controller and workers:

```bash
dbgpt start apiserver --config api-server.toml
```

Verify in order:

```bash
curl -fsS http://127.0.0.1:8100/v1/models
# then use a minimal chat or embedding request with the intended model name
```

If `api_keys` is non-empty, authenticate according to the API's supported
Authorization format. Do not put upstream provider credentials in this field.
Use explicit CORS origins for a non-local deployment.

## 4. Controller lifecycle and model CLI

The model-management group is a remote client. Its address comes from
`--address` or `CONTROLLER_ADDRESS` (default detection falls back to the local
controller address):

```bash
export CONTROLLER_ADDRESS=http://127.0.0.1:8000
dbgpt model list
dbgpt model stop --model_name chat-model --model_type llm --host HOST --port 8001
dbgpt model restart --model_name chat-model --model_type llm
dbgpt model chat --model_name chat-model
```

`model start` is dynamic: it asks the controller for supported model metadata
and then sends a startup request with the selected parameters. This is useful
only after the controller and worker manager are reachable. Its help/discovery
can itself issue a remote request, so avoid using it as an offline parser test.
For a disconnected controller, preserve the connection error and stop; do not
say that the model was started.

The stop/restart commands address model instances through the remote worker
manager. `dbgpt stop controller|worker|apiserver [--port PORT]` controls service
processes, not a provider-side model deployment. Keep these two meanings
separate.

## 5. Standalone/local model decision

For local `hf`, `vllm`, `llama.cpp`, `llama.cpp.server`, or `mlx`:

1. Confirm the artifact path and backend package before starting.
2. Select `device`, dtype, quantization, context, and GPU/memory limits from the
   backend reference, not from a proxy example.
3. Validate TOML first; then run an isolated backend import probe.
4. Start only after a real model file and enough memory are available.
5. Read the model worker log for download, tokenizer, kernel, port, and VRAM
   errors. A host GPU listing does not prove that the Python backend is usable.

For a local CPU smoke, prefer a tiny model and no quantization. Do not claim
production latency or GPU capability from a CPU-only smoke.

## 6. Safe verification ladder

Use this ladder to avoid false positives:

| Level | Evidence | What it proves |
|---|---|---|
| 0 | TOML parse/checker | syntax and static shape only |
| 1 | package import/version/help | installed CLI/API surface only |
| 2 | controller health | controller process reachable |
| 3 | `model list` with recent heartbeat | worker registered and heartbeat visible |
| 4 | `/v1/models` or registry query through intended gateway | routing layer sees models |
| 5 | minimal chat/embedding/rerank request | selected model role actually works |
| 6 | representative application workflow | end-to-end serving path |

Always state the highest level reached and the missing level. Level 3 is not
level 5.

## 7. Logs, ports, and process boundaries

Use the configured log directory and service-specific log names emitted by the
installed launcher. Avoid assuming a checkout-relative log location. For a
foreground process, preserve stderr/stdout. For daemon mode, inspect the
launcher-created log and confirm the PID is alive and the port responds. Check
for port collisions among webserver, controller, worker, and API server before
starting. A successful daemon fork without a listening socket is not success.
