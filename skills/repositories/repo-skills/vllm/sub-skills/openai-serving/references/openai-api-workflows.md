# OpenAI-Compatible API Workflows

vLLM's server implements OpenAI-compatible HTTP APIs so existing OpenAI clients can target a local or private vLLM server. The client must use the server's `/v1` base URL and the served model ID returned by `/v1/models`.

## Endpoint overview

| Endpoint | Typical client call | Use |
| --- | --- | --- |
| `GET /health` | `curl -f http://host:port/health` | Process readiness and load balancer health. |
| `GET /v1/models` | `client.models.list()` | Discover exact served model IDs. |
| `POST /v1/chat/completions` | `client.chat.completions.create(...)` | Message-list chat and instruction models. |
| `POST /v1/chat/completions/batch` | Raw HTTP JSON body | Multiple independent conversations in one non-streaming request. |
| `POST /v1/completions` | `client.completions.create(...)` | Prompt-completion compatibility. |
| `POST /v1/responses` | `client.responses.create(...)` | OpenAI Responses API style with input, tools, and optional stateful retrieval/cancel. |
| `GET /v1/responses/{response_id}` | Raw/OpenAI client if supported | Retrieve background/stateful response. |
| `POST /v1/responses/{response_id}/cancel` | Raw/OpenAI client if supported | Cancel background response. |
| `/v1/embeddings`, `/score`, `/rerank` | OpenAI/Cohere/raw clients | Pooling and scoring tasks; route details to `../modalities-adapters-pooling/SKILL.md`. |

The server may also register tokenizer, generate, pooling, speech, LoRA, render, or development routes depending on flags and model task support. Keep this sub-skill focused on general OpenAI serving and route specialized payload behavior to sibling skills.

## Python client setup

Install/use an OpenAI-compatible client in the user's environment and target `/v1`:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="EMPTY",
)
models = client.models.list()
model = models.data[0].id
```

Important invariants:

- `base_url` should be `http://HOST:PORT/v1`, not just `http://HOST:PORT`.
- `api_key` may be any placeholder only when the server was started without `--api-key`.
- If the server was started with `--api-key`, the client key must match one accepted token.
- Use `client.models.list()` to discover `model`; a 404 often means the request model does not match the served ID.

## Chat completion

```python
response = client.chat.completions.create(
    model=model,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Who won the World Series in 2020?"},
    ],
    max_tokens=64,
)
print(response.choices[0].message.content)
```

Streaming chat:

```python
stream = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "Count to three."}],
    stream=True,
)
for chunk in stream:
    delta = chunk.choices[0].delta
    if delta.content:
        print(delta.content, end="", flush=True)
```

Validation rules surfaced by vLLM include:

- `messages` is required and must be a non-empty list of chat messages.
- `tools=[]` is rejected; omit tools or provide a non-empty tools list.
- If `tool_choice` is set, compatible `tools` must be provided except for `none`.
- Structured outputs and tools are mutually constrained; deep schema/tool behavior belongs in `../structured-tool-reasoning/SKILL.md`.
- `response_format` with `json_schema` requires a schema payload.

## Completion

```python
response = client.completions.create(
    model=model,
    prompt="A robot may not injure a human being",
    max_tokens=64,
    temperature=0.2,
)
print(response.choices[0].text)
```

Use `/v1/completions` for prompt-style compatibility, logprobs/echo tests, or legacy clients. Use chat completions for chat-template-aware instruction models.

## Responses API

The Responses API accepts `input`, optional `instructions`, tools, streaming, and structured-output-related fields:

```python
response = client.responses.create(
    model=model,
    input="Write a one sentence status update.",
)
print(response.output_text)
```

Raw curl fallback:

```bash
curl http://localhost:8000/v1/responses \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer EMPTY' \
  -d '{"model":"Qwen/Qwen2.5-1.5B-Instruct","input":"Say hello","max_output_tokens":32}'
```

For structured output with Responses, prefer OpenAI `text.format` or vLLM `structured_outputs`, not both. If the task is primarily about JSON schemas, regex constraints, structural tags, tool calling, or Harmony/reasoning behavior, route to `../structured-tool-reasoning/SKILL.md` after confirming the serving basics here.

## Batch chat completions endpoint

`/v1/chat/completions/batch` accepts a single JSON request where `messages` is a list of conversations:

```bash
curl http://localhost:8000/v1/chat/completions/batch \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "Qwen/Qwen2.5-1.5B-Instruct",
    "messages": [
      [{"role":"user","content":"What is the capital of France?"}],
      [{"role":"user","content":"What is the capital of Japan?"}]
    ],
    "max_tokens": 32
  }'
```

Expected response has `choices` indexed `0..N-1`, one result per conversation. Current chat-batch limitations include no streaming, no tools, no beam search, and `n` must be `1`.

## Batch JSONL with `run-batch`

Create `requests.jsonl`:

```jsonl
{"custom_id":"chat-1","method":"POST","url":"/v1/chat/completions","body":{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[{"role":"user","content":"Say hello"}],"max_tokens":32}}
{"custom_id":"chat-2","method":"POST","url":"/v1/chat/completions","body":{"model":"Qwen/Qwen2.5-1.5B-Instruct","messages":[{"role":"user","content":"Say goodbye"}],"max_tokens":32}}
```

Run:

```bash
vllm run-batch -i requests.jsonl -o responses.jsonl --model Qwen/Qwen2.5-1.5B-Instruct
```

Each output line includes the input `custom_id`, response body, and error information if validation or execution fails. If users expect OpenAI hosted Batch job lifecycle objects, clarify that `vllm run-batch` is a local CLI workflow over JSONL, not a remote job management API.

## Curl smoke tests

No-auth server:

```bash
curl -f http://localhost:8000/health
curl http://localhost:8000/v1/models
curl http://localhost:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"MODEL_FROM_LIST","messages":[{"role":"user","content":"ping"}],"max_tokens":8}'
```

Auth-protected server:

```bash
curl http://localhost:8000/v1/models \
  -H 'Authorization: Bearer sk-local-dev-token'
```

## Model-name handoff rule

When helping users debug clients, ask for or retrieve:

1. The exact `vllm serve ...` command.
2. The `/v1/models` JSON.
3. The client `base_url`, `api_key` source, and `model` string.
4. The HTTP status and response body.

Most client issues are resolved by changing `base_url` to include `/v1`, changing `model` to a `data[].id` from `/v1/models`, or aligning the auth token.
