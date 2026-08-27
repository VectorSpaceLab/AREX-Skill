# LMDeploy Serving API Reference

LMDeploy `api_server` includes OpenAI-compatible, OpenAI Responses-compatible, and Anthropic-compatible routers. The same engine model list is reused across these surfaces.

## Authentication and Base URLs

- Without `--api-keys`, no bearer token is required.
- With `--api-keys key-a key-b`, clients must send `Authorization: Bearer key-a` or another configured key.
- OpenAI SDK base URL is the `/v1` root, for example `http://127.0.0.1:23333/v1`.
- LMDeploy `APIClient` base URL is the server root, for example `http://127.0.0.1:23333`.
- Codex Responses config uses `/v1` as `base_url`; Codex appends `/responses`.
- Claude Code Anthropic config uses the server root; Claude Code appends `/v1/messages`.

## OpenAI-Compatible Endpoints

Supported core endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/v1/models` | Return model cards for base model and adapters. |
| `POST` | `/v1/chat/completions` | Chat completion in OpenAI-compatible shape. |
| `POST` | `/v1/completions` | Prompt completion in OpenAI-compatible shape. |
| `POST` | `/v1/encode` | Tokenize input through LMDeploy API client helper. |

Minimal chat request:

```json
{
  "model": "lmdeploy-model",
  "messages": [{"role": "user", "content": "Reply with pong"}],
  "max_tokens": 32
}
```

Important chat request fields include `temperature`, `top_p`, `top_k`, `max_completion_tokens`, deprecated-compatible `max_tokens`, `stop`, `stream`, `stream_options`, `tools`, `tool_choice`, `parallel_tool_calls`, `response_format`, `logprobs`, `top_logprobs`, `presence_penalty`, `frequency_penalty`, `repetition_penalty`, `session_id`, `seed`, `min_new_tokens`, `min_p`, `enable_thinking`, `return_token_ids`, `return_logprob`, `include_stop_str_in_output`, and `chat_template_kwargs`.

LMDeploy-specific chat notes:

- `messages` may be an OpenAI-style message list; multimodal payload details are owned by the `vision-language` sub-skill.
- `stop` strings must map to single token ids for reliable stop behavior.
- `response_format.type` accepts `text`, `json_object`, `json_schema`, and LMDeploy's `regex_schema` extension.
- Tool calls require a matching `--tool-call-parser` at server launch.
- Reasoning fields require a matching `--reasoning-parser` or model/parser behavior that extracts reasoning.
- `stream_options.include_usage` can request usage chunks for compatible clients.

Completion request shape:

```json
{
  "model": "lmdeploy-model",
  "prompt": "Two steps to build a house:",
  "max_tokens": 32,
  "temperature": 0.7
}
```

## OpenAI Responses-Compatible Endpoint

Supported endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/v1/responses` | Text-first subset of OpenAI Responses create API. |
| `GET` | `/v1/models` | Model list reused by Responses clients. |

Minimal request:

```json
{
  "model": "lmdeploy-model",
  "input": "Reply exactly: pong",
  "max_output_tokens": 32
}
```

Response body includes `object: "response"`, `status`, an `output` item list, and convenience `output_text`.

Responses compatibility notes:

- `input` may be a string or a list of Responses input items.
- `instructions`, `developer`, and `system` messages are merged into a leading system message for chat-template compatibility.
- Function tools are converted to LMDeploy OpenAI-compatible tools; launch with `--tool-call-parser` to parse tool calls.
- `parallel_tool_calls` defaults to `true`; when `false`, only the first parsed function call is returned for vLLM-style compatibility.
- Non-function hosted tools such as `web_search` are accepted but ignored.
- Responses-only logprob serialization and stream obfuscation options are accepted but ignored.
- `background` mode and `previous_response_id` are not supported.
- LMDeploy generation extensions include `presence_penalty`, `frequency_penalty`, `repetition_penalty`, `top_k`, `stop`, `seed`, `min_p`, `ignore_eos`, `skip_special_tokens`, and `include_stop_str_in_output`.

Streaming `/v1/responses` returns server-sent events such as `response.created`, `response.in_progress`, `response.output_item.added`, `response.content_part.added`, `response.output_text.delta`, `response.output_text.done`, `response.function_call_arguments.delta`, `response.function_call_arguments.done`, `response.output_item.done`, and `response.completed`.

## Anthropic-Compatible Endpoints

Supported endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/v1/messages` | Anthropic Messages-compatible generation. |
| `POST` | `/v1/messages/count_tokens` | Token count estimate using tokenizer/chat-template behavior. |
| `GET` | `/anthropic/v1/models` | Anthropic-oriented model list. |

Required headers for Anthropic POST endpoints:

```text
content-type: application/json
anthropic-version: 2023-06-01
```

Minimal message request:

```json
{
  "model": "lmdeploy-model",
  "max_tokens": 128,
  "messages": [{"role": "user", "content": "Hello from Anthropic client"}]
}
```

Important message request fields include `system`, `messages`, `max_tokens`, `stop_sequences`, `stream`, `temperature`, `top_p`, `top_k`, `tools`, `tool_choice`, `return_token_ids`, `return_logprob`, `include_stop_str_in_output`, and `return_routed_experts`.

Anthropic compatibility notes:

- Output content blocks may include `text`, `thinking`, and `tool_use`.
- Tool-use output requires a configured `--tool-call-parser`.
- Reasoning block extraction uses the same parser stack as OpenAI-compatible chat.
- `count_tokens` is intended for practical estimation, not a strict external tokenizer guarantee.
- Claude Code may need explicit model environment variables if model discovery does not use `/anthropic/v1/models`.

Streaming `/v1/messages` returns Anthropic-style server-sent events such as `message_start`, `content_block_start`, `content_block_delta`, `content_block_stop`, `message_delta`, and `message_stop`.

## Health, Docs, and Discovery

- The API server prints a browser URL for Swagger UI unless launched with `--disable-fastapi-docs`.
- `/v1/models` is the safest first live probe for OpenAI/Responses clients.
- `/anthropic/v1/models` is the documented model-list endpoint for Anthropic-style discovery.
- Proxy servers expose `/nodes/status`, `/nodes/add`, and `/nodes/remove` in addition to OpenAI-compatible `/v1/*` routes.
