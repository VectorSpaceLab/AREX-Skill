# Inference workflows

## Local Docker compose inference profile

The inference profile runs a separate service set from the data-collection backend:

| Service | Purpose | Notes |
| --- | --- | --- |
| `inference-db` | Postgres for inference server state | Default exposed host port `5434`. |
| `inference-redis` | Redis for rate limiting and queue/state support | Default exposed host port `6389`. |
| `inference-server` | FastAPI inference API | Exposes `8000`; mounts shared and server source for dev image. |
| `inference-worker` | Worker process | Reads `MODEL_CONFIG_NAME` and connects to `ws://inference-server:8000`. |
| `inference-safety` | Optional safety server | Separate `inference-safety` profile; Blade2Blade model service surface. |

Typical compose commands:

```bash
docker compose --profile inference build
docker compose --profile inference up -d
docker compose logs -f inference-server inference-worker
```

Use `_lorem` for the lowest-resource service smoke:

```bash
MODEL_CONFIG_NAME=_lorem docker compose --profile inference up --build --attach-dependencies
```

Use `distilgpt2` only when downloading or using cached Hugging Face model artifacts is acceptable.

## Text client workflow

The debug text client expects an inference server with debug auth enabled:

```bash
cd inference/text-client
pip install -r requirements.txt
python __main__.py --backend-url http://127.0.0.1:8000 --model-config-name _lorem --username test1
```

Operating sequence:

1. Login via debug auth.
2. Create a chat.
3. Validate that the selected model config exists in `/configs/model_configs`.
4. POST a prompter message.
5. POST an assistant message with sampling parameters.
6. Stream message events and print `token` event text until final message.

## Worker configuration workflow

Useful environment variables:

| Variable | Default / role |
| --- | --- |
| `BACKEND_URL` | Websocket server URL, default local `ws://localhost:8000` in worker settings and compose `ws://inference-server:8000`. |
| `MODEL_CONFIG_NAME` | Default `distilgpt2`; set `_lorem` for no tokenizer/model download. |
| `API_KEY` | Worker API key; compose default `0000`. |
| `INFERENCE_SERVER_URL` | HTTP text-generation backend URL, default `http://localhost:8001`. |
| `MAX_PARALLEL_REQUESTS` | Number of concurrent work requests a worker accepts. |
| `ENABLE_SAFETY` / safety settings | Enables safety prompt rewriting when configured. |
| `OAHF_HOME` | HF cache location used by container worker startup scripts. |
| `LOGURU_LEVEL` | Runtime logging level. |

When running the worker directly, first ensure the shared package is importable, the selected config exists, and the model backend is reachable unless using `_lorem`.

## Full dev tmux workflow

The repository's full dev setup script starts several tmux panes with Postgres, Redis, optional text-generation inference server, inference server, text client, and two workers. Treat that as reference-only because it starts containers, opens ports, and may download models. A safer manual equivalent is:

1. Start Postgres and Redis.
2. Start inference server with debug keys, `ALLOW_DEBUG_AUTH=True`, and matching Redis/Postgres ports.
3. If using a real model, start the text-generation inference backend and wait for its connected/healthy log.
4. Start one `_lorem` worker first to prove websocket auth and protocol.
5. Start the text client and send a short prompt.
6. Add real model workers only after GPU/cache readiness checks.

## Safety server workflow

The safety server is a small FastAPI wrapper around Blade2Blade. It is optional. Enable it only when the worker has safety enabled and `SAFETY_SERVER_URL` points to a running service. If the safety server is down, disable safety for ordinary inference plumbing checks rather than treating chat/server routing as broken.

## Load testing workflow

A Locust load test simulates debug chat users, creates chats, sends repeated `hello` messages, and defaults to `_lorem` as the model config. Use it only after a local inference server is healthy. It is useful for queue/SSE/service testing, not model quality evaluation.

## Updating API docs

Once the inference server is running, the OpenAPI schema can be downloaded from `/openapi.json` and copied into documentation. This is a maintainer/doc update workflow; do not make it part of runtime skill operation unless the user explicitly asks to refresh docs.
