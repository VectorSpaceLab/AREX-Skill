# Service workflows

## Purpose

Use this reference to start or validate Agent Lightning services without reopening source examples.

## Store service

Start a local in-memory store service:

```bash
agl store --host 127.0.0.1 --port 4747 --log-level INFO
```

Connect from Python:

```python
import agentlightning as agl
store = agl.LightningStoreClient("http://127.0.0.1:4747")
```

Use Mongo only when the optional dependency and service are provisioned:

```bash
agl store --backend mongo --mongo-uri 'mongodb://localhost:27017/?replicaSet=rs0'
```

Do not run Docker or Mongo setup scripts unless the user explicitly agrees to local service mutation.

## Prometheus metrics service

`agl prometheus` exposes the multiprocess Prometheus registry through a FastAPI server. It requires `PROMETHEUS_MULTIPROC_DIR` at runtime.

```bash
export PROMETHEUS_MULTIPROC_DIR="$(mktemp -d)"
agl prometheus --host 127.0.0.1 --port 4748 --metrics-path /v1/prometheus
```

For a short local smoke that does not require a running store, use:

```bash
python scripts/check_prometheus_metrics.py --duration 1 --host 127.0.0.1
```

## LLM Proxy

`LLMProxy` wraps LiteLLM and routes OpenAI-compatible requests while adding Agent Lightning trace attribution.

Verified constructor summary:

```python
LLMProxy(
    port=None,
    model_list=None,
    store=None,
    host=None,
    litellm_config=None,
    num_retries=0,
    num_workers=1,
    launch_mode='mp',
    launcher_args=None,
    middlewares=None,
    callbacks=None,
)
LLMProxy.update_model_list(model_list) -> None
```

Minimal pattern:

```python
import agentlightning as agl

store = agl.InMemoryLightningStore()
store_server = agl.LightningStoreServer(store, "127.0.0.1", 8081)
await store_server.start()

proxy = agl.LLMProxy(
    host="127.0.0.1",
    port=8082,
    store=store_server,
    model_list=[
        {
            "model_name": "my-model",
            "litellm_params": {
                "model": "hosted_vllm/my-model",
                "api_base": "http://127.0.0.1:8080/v1",
            },
        }
    ],
)
await proxy.start()
```

For attributed requests, call through a rollout/attempt path:

```text
http://127.0.0.1:8082/rollout/<rollout_id>/attempt/<attempt_id>/v1/chat/completions
```

`ProxyLLM.get_base_url(rollout_id, attempt_id)` builds this path for agents.

## Safe OpenAI-compatible endpoint check

Use the bundled checker when a user supplies an endpoint and model:

```bash
python scripts/check_litellm_proxy.py \
  --base-url http://127.0.0.1:8082/v1 \
  --model my-model \
  --api-key dummy \
  --chat
```

The checker:

- never prints the API key,
- can list models if requested,
- can run chat and/or responses endpoints,
- uses a short timeout,
- exits non-zero when the endpoint/model is unusable.

## vLLM integration

Use `agl vllm` only when vLLM is installed. It instruments vLLM's CLI path. For token-ID-sensitive training, confirm the serving backend can return token IDs and that proxy spans actually contain them.

## CI/maintainer scripts classified as reference-only

The source repository includes scripts for LiteLLM CI launch, MongoDB Docker setup, OpenAPI export, W&B result validation, Ray restart, and VM image setup. They are not bundled as runnable helpers here because they depend on secrets, mutate local services, start long-running infrastructure, or are maintainer-specific. This skill preserves the reusable patterns through safe checkers and references instead.
