# LMDeploy Client Integration

This reference gives copy-adaptable client patterns for an already-running LMDeploy server.

## cURL Validation

List models:

```bash
curl http://127.0.0.1:23333/v1/models
```

OpenAI chat:

```bash
curl http://127.0.0.1:23333/v1/chat/completions \
  -H "content-type: application/json" \
  -d '{
    "model": "lmdeploy-model",
    "messages": [{"role": "user", "content": "Reply exactly: pong"}],
    "max_tokens": 32
  }'
```

OpenAI completion:

```bash
curl http://127.0.0.1:23333/v1/completions \
  -H "content-type: application/json" \
  -d '{
    "model": "lmdeploy-model",
    "prompt": "Reply exactly: pong",
    "max_tokens": 32
  }'
```

Responses endpoint:

```bash
curl http://127.0.0.1:23333/v1/responses \
  -H "content-type: application/json" \
  -d '{
    "model": "lmdeploy-model",
    "input": "Reply exactly: pong",
    "max_output_tokens": 32
  }'
```

Anthropic Messages endpoint:

```bash
curl http://127.0.0.1:23333/v1/messages \
  -H "content-type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "lmdeploy-model",
    "max_tokens": 32,
    "messages": [{"role": "user", "content": "Reply exactly: pong"}]
  }'
```

Authenticated requests add:

```bash
-H "Authorization: Bearer <api-key>"
```

## LMDeploy `APIClient`

`APIClient` takes the server root, not the `/v1` URL:

```python
from lmdeploy.serve.openai.api_client import APIClient

client = APIClient("http://127.0.0.1:23333", api_key="optional-key")
model = client.available_models[0]

for item in client.chat_completions_v1(
    model=model,
    messages=[{"role": "user", "content": "Say this is a test."}],
    max_tokens=32,
):
    print(item)

for item in client.completions_v1(model=model, prompt="One word greeting:", max_tokens=8):
    print(item)
```

Use `client.encode(input="text", do_preprocess=False, add_bos=True)` when checking tokenization behavior exposed by `/v1/encode`.

## OpenAI Python SDK

The OpenAI SDK base URL is the `/v1` root:

```python
from openai import OpenAI

client = OpenAI(
    api_key="optional-or-dummy-key",
    base_url="http://127.0.0.1:23333/v1",
)
model = client.models.list().data[0].id
response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Give three deployment checks."}],
    temperature=0.8,
    top_p=0.8,
    max_tokens=128,
)
print(response.choices[0].message.content)
```

Streaming with reasoning parser enabled:

```python
from openai import OpenAI

client = OpenAI(api_key="optional-or-dummy-key", base_url="http://127.0.0.1:23333/v1")
model = client.models.list().data[0].id
stream = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "9.11 and 9.8, which is greater?"}],
    stream=True,
)
for chunk in stream:
    delta = chunk.choices[0].delta
    print("reasoning:", getattr(delta, "reasoning_content", None))
    print("content:", delta.content)
```

Tool calling requires starting the server with a parser that matches the model family:

```bash
lmdeploy serve api_server <model> --tool-call-parser qwen --server-port 23333
```

Then call the OpenAI chat API with `tools=[...]` and inspect `response.choices[0].message.tool_calls`.

## Codex Responses Integration

Start LMDeploy with the model Codex should use:

```bash
lmdeploy serve api_server Qwen/Qwen3.5-35B-A3B \
  --backend pytorch \
  --server-port 23333 \
  --tool-call-parser qwen
```

Verify Responses before configuring Codex:

```bash
curl http://127.0.0.1:23333/v1/models
curl http://127.0.0.1:23333/v1/responses \
  -H "content-type: application/json" \
  -d '{"model":"Qwen/Qwen3.5-35B-A3B","input":"Say hello from LMDeploy","max_output_tokens":32}'
```

Codex provider config uses `/v1` as the base URL and `wire_api = "responses"`:

```toml
model = "Qwen/Qwen3.5-35B-A3B"
model_provider = "lmdeploy"

[model_providers.lmdeploy]
name = "LMDeploy"
base_url = "http://127.0.0.1:23333/v1"
env_key = "LMDEPLOY_API_KEY"
wire_api = "responses"
requires_openai_auth = false
stream_idle_timeout_ms = 300000
```

Set an API key environment variable before running Codex. If the server was not launched with `--api-keys`, any non-empty value is enough for clients that require a key variable:

```bash
export LMDEPLOY_API_KEY=dummy
codex exec "Say hello from LMDeploy"
```

## Claude Code Anthropic Integration

Start LMDeploy with the model Claude Code should use:

```bash
lmdeploy serve api_server Qwen/Qwen3.5-35B-A3B \
  --backend pytorch \
  --server-port 23333 \
  --tool-call-parser qwen
```

Verify Anthropic Messages before configuring Claude Code:

```bash
curl http://127.0.0.1:23333/v1/messages \
  -H "content-type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model":"Qwen/Qwen3.5-35B-A3B","max_tokens":128,"messages":[{"role":"user","content":"Say hello from LMDeploy"}]}'
```

Claude Code uses the server root for `ANTHROPIC_BASE_URL`, not `/v1`:

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:23333",
    "ANTHROPIC_AUTH_TOKEN": "dummy",
    "ANTHROPIC_MODEL": "Qwen/Qwen3.5-35B-A3B",
    "ANTHROPIC_CUSTOM_MODEL_OPTION": "Qwen/Qwen3.5-35B-A3B",
    "ANTHROPIC_CUSTOM_MODEL_OPTION_NAME": "LMDeploy local model",
    "ANTHROPIC_CUSTOM_MODEL_OPTION_DESCRIPTION": "Served by LMDeploy /v1/messages",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "Qwen/Qwen3.5-35B-A3B",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "Qwen/Qwen3.5-35B-A3B",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "Qwen/Qwen3.5-35B-A3B",
    "CLAUDE_CODE_SUBAGENT_MODEL": "Qwen/Qwen3.5-35B-A3B",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1"
  }
}
```

Run:

```bash
claude --model Qwen/Qwen3.5-35B-A3B
```

If model discovery fails, keep the explicit `ANTHROPIC_MODEL` and custom model variables aligned with `/v1/models` output.

## Parser Validation Curls

Authenticated streaming Responses with a tool definition:

```bash
curl -N http://127.0.0.1:23333/v1/responses \
  -H "content-type: application/json" \
  -H "Authorization: Bearer local-secret" \
  -d '{
    "model":"lmdeploy-model",
    "input":"Call the search tool with query lmdeploy.",
    "max_output_tokens":128,
    "stream":true,
    "tools":[{"type":"function","name":"search","description":"Search docs","parameters":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}]
  }'
```

Anthropic streaming with a tool definition:

```bash
curl -N http://127.0.0.1:23333/v1/messages \
  -H "content-type: application/json" \
  -H "anthropic-version: 2023-06-01" \
  -H "Authorization: Bearer local-secret" \
  -d '{
    "model":"lmdeploy-model",
    "max_tokens":128,
    "stream":true,
    "messages":[{"role":"user","content":"Find lmdeploy docs"}],
    "tools":[{"name":"search","description":"Search docs","input_schema":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"]}}],
    "tool_choice":{"type":"auto"}
  }'
```
