# OpenChat OpenAI-compatible API reference

OpenChat exposes a FastAPI server that mimics the OpenAI Chat Completions API and uses vLLM for generation. The serving module is `python -m ochat.serving.openai_api_server`.

See [deployment.md](deployment.md) before launching and [troubleshooting.md](troubleshooting.md) when an endpoint returns an unexpected status.

## Endpoints

| Endpoint | Method | Purpose | Auth behavior |
|---|---:|---|---|
| `/v1/models` | `GET` | Lists the request-side model names accepted by this server instance. | Requires `Authorization: Bearer ...` only when the server was launched with `--api-keys`. |
| `/v1/chat/completions` | `POST` | Creates a chat completion response, optionally streamed as server-sent events. | Same API-key behavior as `/v1/models`. |

## Model names and aliases

There are three different model identifiers in serving tasks:

| Name location | Meaning | Example |
|---|---|---|
| Launch `--model` | Hugging Face model id or model directory containing the weights/tokenizer and usually `openchat.json`. This is not what clients must send in JSON. | `openchat/openchat-3.6-8b-20240522` |
| Launch `--model-type` | OpenChat configuration key. If omitted, the server tries to read `openchat.json` from `--model`. | `openchat_3.6`, `openchat_v3.2_mistral` |
| Request JSON `model` | One of the names returned by `/v1/models`: the `--model-type` plus any configured serving aliases. | `openchat_3.6`, `openchat_3.5` |

Known installed model types and request aliases:

| `--model-type` key | Request aliases in addition to the key | Context length |
|---|---|---:|
| `openchat_3.6` | none | 8192 |
| `openchat_v3.2` | none | 4096 |
| `openchat_v3.2_mistral` | `openchat_3.5` | 8192 |
| `openchat_v3.2_gemma_new` | `openchat_3.5_gemma_new` | 8192 |
| `chatml_8192` | none | 8192 |
| `zephyr_mistral` | none | 8192 |
| `gemma_it` | none | 8192 |
| `llama3_instruct` | none | 8192 |

If a client sends a `model` value that is not in `/v1/models`, the server returns a 404 invalid-request error.

## `/v1/models`

Example without API-key enforcement:

```bash
curl -s http://localhost:18888/v1/models | python -m json.tool
```

Example with API-key enforcement:

```bash
curl -s http://localhost:18888/v1/models \
  -H "Authorization: Bearer ${OPENCHAT_API_KEY}" | python -m json.tool
```

The response is a list of `ModelCard` objects with `id` and `root` set to each accepted request-side model name.

## `/v1/chat/completions` request fields

The request schema is `ChatCompletionRequest`.

| Field | Required | Default | Serving behavior |
|---|---:|---|---|
| `model` | yes | none | Must match one name returned by `/v1/models`. This is the request alias/model type, not the launch `--model` path. |
| `messages` | yes | none | Use a list of `{ "role": ..., "content": ... }` dicts. `system` messages are ignored unless the server was launched with `--enable-sys-prompt`. |
| `condition` | no | `""` | Passed into OpenChat prompt construction. Empty string uses the model template's inference default when one exists. Route template-level questions to [../../prompting/SKILL.md](../../prompting/SKILL.md). |
| `temperature` | no | `0.7` | Forwarded to vLLM `SamplingParams`. |
| `top_p` | no | `1.0` | Forwarded to vLLM `SamplingParams`. |
| `n` | no | `1` | Number of candidate completions. Streaming sends chunks for each index. |
| `max_tokens` | no | remaining context | If omitted, the server fills the remaining model context. If explicit and `prompt_tokens + max_tokens` exceeds the model context, expect a 400 context-length error. |
| `seed` | no | `null` | Forwarded to vLLM `SamplingParams` for reproducible sampling when supported by the runtime. |
| `stop` | no | `null` | Present in the schema but not applied by the server's `SamplingParams`; generation stops on OpenChat end-of-turn tokens or length. |
| `presence_penalty` | no | `0.0` | Forwarded to vLLM `SamplingParams`. |
| `frequency_penalty` | no | `0.0` | Forwarded to vLLM `SamplingParams`. |
| `logit_bias` | no | `null` | Non-empty values are rejected with a 400 error; this server does not support logit bias. |
| `stream` | no | `false` | If true, returns `text/event-stream` chunks and a final `data: [DONE]`. |
| `user` | no | `null` | Accepted by the schema but not otherwise used by the server logic. |

The server appends an empty assistant turn before tokenization when the last non-system message is not already `assistant`.

## Non-streaming example

```bash
curl -s http://localhost:18888/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openchat_3.6",
    "messages": [
      {"role": "user", "content": "Write one sentence about OpenChat."}
    ],
    "temperature": 0.7,
    "top_p": 1.0,
    "max_tokens": 128
  }' | python -m json.tool
```

With API-key enforcement:

```bash
curl -s http://localhost:18888/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${OPENCHAT_API_KEY}" \
  -d '{
    "model": "openchat_3.6",
    "messages": [{"role": "user", "content": "Say hello."}],
    "max_tokens": 32
  }'
```

## Condition example

The request `condition` changes the condition prefix used during prompt construction. The README shows a math mode style request:

```bash
curl -s http://localhost:18888/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openchat_3.6",
    "condition": "Math Correct",
    "messages": [
      {"role": "user", "content": "10.3 - 7988.8133 = "}
    ],
    "max_tokens": 64
  }'
```

For the exact token prefixes produced by `condition`, route to [../../prompting/SKILL.md](../../prompting/SKILL.md).

## Streaming behavior

Launch-time `--stream-period` controls how many generated tokens are batched between stream events; the server default is 6.

```bash
curl -N http://localhost:18888/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openchat_3.6",
    "messages": [{"role": "user", "content": "Count to five."}],
    "stream": true,
    "n": 1,
    "max_tokens": 64
  }'
```

Streaming response shape:

1. First chunk for each `n` index includes `delta.role = "assistant"`.
2. Subsequent chunks include `delta.content` text deltas every `--stream-period` events or at finish.
3. A finish chunk has `finish_reason` of `"stop"` or `"length"`.
4. The stream ends with `data: [DONE]`.

For `n > 1`, inspect `choices[].index` and concatenate deltas separately per index.

## Response shape

Non-streaming responses include:

- `id`, `object = "chat.completion"`, `created`, `model`.
- `choices[]` with `index`, assistant `message`, and `finish_reason`.
- `usage` with `prompt_tokens`, `completion_tokens`, and `total_tokens` from vLLM output.

Streaming responses use `object = "chat.completion.chunk"` and send `delta` fragments instead of full messages.

## Unsupported or surprising OpenAI API differences

- `function_call` and tool-call features are not implemented by this server.
- Non-empty `logit_bias` is rejected.
- Custom `stop` strings are accepted by the schema but are not passed to vLLM sampling in this implementation.
- `messages` is best treated as a list of role/content dictionaries even though the pydantic annotation also permits a string.
- System prompts require server launch flag `--enable-sys-prompt`; otherwise system messages are silently skipped before tokenization.
