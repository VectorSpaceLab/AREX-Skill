# Proxy Server Workflows

Read this when you need concrete OptiLLM server/client workflows.

## 1. External OpenAI-compatible proxy

Use this when another service provides chat completions and OptiLLM should optimize requests before forwarding them.

```bash
export OPENAI_API_KEY="sk-no-key-or-real-key"
optillm --approach auto --model gpt-4o-mini --base-url http://localhost:8080/v1
```

Client:

```python
from openai import OpenAI
client = OpenAI(api_key="sk-no-key-or-real-key", base_url="http://localhost:8000/v1")
response = client.chat.completions.create(
    model="re2-gpt-4o-mini",
    messages=[{"role": "user", "content": "How many r's are in strawberry?"}],
)
```

Use `--base-url` for llama.cpp, Ollama-compatible OpenAI endpoints, local OpenAI-compatible proxies, or other provider gateways.

## 2. Provider-key routing

Provider precedence is shared in the root configuration reference. Common starts:

```bash
export OPENAI_API_KEY="sk-..."
optillm --approach auto --model gpt-4o-mini
```

```bash
export CEREBRAS_API_KEY="..."
optillm --approach cepo --model llama-3.3-70b
```

```bash
export AZURE_OPENAI_API_KEY="..."
export AZURE_API_VERSION="2024-02-15-preview"
export AZURE_API_BASE="https://resource.openai.azure.com"
optillm --model deployment-name
```

If none of those variables is set and `OPTILLM_API_KEY` is also unset, OptiLLM uses the LiteLLM wrapper fallback.

## 3. Server auth versus provider auth

`--optillm-api-key` protects the OptiLLM server from clients. It is separate from provider credentials.

```bash
optillm --optillm-api-key "server-secret" --approach auto
```

Client:

```python
client = OpenAI(base_url="http://localhost:8000/v1", api_key="server-secret")
```

Do not confuse this with `OPENAI_API_KEY`/`CEREBRAS_API_KEY`/`AZURE_*` upstream credentials. A request bearer token beginning with `sk-` can override the upstream OpenAI key for that request.

## 4. Approach selection in requests

Model prefix:

```python
client.chat.completions.create(model="moa-gpt-4o-mini", messages=[...])
```

Request body / OpenAI SDK extra body:

```python
client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[...],
    extra_body={"optillm_approach": "bon|moa|mcts"},
)
```

Prompt tag:

```text
<optillm_approach>re2</optillm_approach> Solve the query.
```

Use tags sparingly because they modify prompt content before the model sees it.

## 5. Docker variants

OptiLLM publishes or builds three image families:

- Full image: includes local inference and plugins.
- Proxy-only image: smaller; intended for external provider routing.
- Offline image: includes pre-downloaded models/assets for offline scenarios.

A typical compose service exposes `OPTILLM_PORT`, provider environment variables, and a healthcheck against `/health`.

## 6. Health and model checks

- `GET /health` is the fastest liveness probe and returns `{"status": "ok"}`.
- `GET /v1/models` delegates to the configured provider when `base_url` is set, or returns a local synthetic model entry for local inference.

## 7. When to avoid running a full server smoke

Avoid full server tests when the task lacks:

- Provider credentials.
- A reachable external OpenAI-compatible endpoint.
- A cached local HuggingFace model.
- Permission to bind ports or run a long-lived process.

In those cases, use dry-run request construction with `scripts/proxy_smoke_client.py` and parser inspection through the optimization sub-skill.
