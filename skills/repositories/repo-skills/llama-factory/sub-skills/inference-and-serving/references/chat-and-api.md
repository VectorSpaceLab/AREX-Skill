# ChatModel and OpenAI-Compatible API

## Entry Points

LlamaFactory exposes inference through the `llamafactory-cli` console script and the shorter `lmf` alias. The v0 launcher is the default; setting `USE_V1=1` switches to the experimental v1 architecture, so most inference guidance here assumes v0.

Useful commands:

```bash
llamafactory-cli chat CONFIG.yaml
lmf chat CONFIG.yaml
llamafactory-cli webchat CONFIG.yaml
API_PORT=8000 llamafactory-cli api CONFIG.yaml
API_PORT=8000 lmf api CONFIG.yaml infer_backend=vllm vllm_enforce_eager=true
```

The `api` command constructs a `ChatModel`, wraps it in FastAPI, and starts uvicorn. The `chat` command uses the same `ChatModel` class in a terminal loop with `clear` and `exit` commands.

## ChatModel API

`llamafactory.chat.ChatModel` accepts an optional argument dictionary. When no dictionary is supplied, LlamaFactory parses CLI/YAML/JSON arguments using the normal inference argument parser.

Core methods:

- `chat(messages, system=None, tools=None, images=None, videos=None, audios=None, **kwargs)` returns a list of response objects.
- `stream_chat(...)` yields text deltas token by token.
- `get_scores(batch_input, **kwargs)` returns reward-model scores and is only valid for non-generating/reward-model loading.
- `achat`, `astream_chat`, and `aget_scores` are async equivalents.

Message dictionaries use LlamaFactory roles such as `user` and `assistant` for direct `ChatModel` calls. Generation kwargs are forwarded to the selected engine and commonly include `do_sample`, `temperature`, `top_p`, `max_new_tokens`, `num_return_sequences`, `repetition_penalty`, and `stop`.

Minimal direct usage:

```python
from llamafactory.chat import ChatModel

chat_model = ChatModel({
    "model_name_or_path": "MODEL_OR_LOCAL_PATH",
    "template": "llama3",
    "infer_backend": "huggingface",
    "max_new_tokens": 128,
})
responses = chat_model.chat([{"role": "user", "content": "Hi"}])
print(responses[0].response_text)
```

If a direct `ChatModel` call fails while loading model weights, tokenizers, adapters, devices, or quantization state, route the investigation to `model-loading-and-export`. If prompt rendering or multimodal placeholders are wrong, route to `data-and-templates`.

## API Environment Variables

The API server recognizes these environment variables:

| Variable | Effect |
| --- | --- |
| `API_HOST` | uvicorn bind host; defaults to `0.0.0.0`. |
| `API_PORT` | uvicorn bind port; defaults to `8000`. |
| `API_KEY` | Optional bearer token; when set, all routes require `Authorization: Bearer <API_KEY>`. |
| `API_MODEL_NAME` | Model id returned by `/v1/models`; defaults to `gpt-3.5-turbo`. |
| `FASTAPI_ROOT_PATH` | FastAPI `root_path` for reverse proxies/sub-path deployments. |
| `API_VERBOSE` | Request logging is enabled by default; set a disabling value if noisy logs are a problem. |

Example authenticated launch:

```bash
API_HOST=127.0.0.1 API_PORT=8000 API_KEY=secret API_MODEL_NAME=my-model \
  llamafactory-cli api CONFIG.yaml infer_backend=huggingface
```

## OpenAI-Compatible Routes

The server registers exactly these public OpenAI-style routes:

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/v1/models` | Returns a one-item model list using `API_MODEL_NAME` or `gpt-3.5-turbo`. |
| `POST` | `/v1/chat/completions` | Generates chat completions when the engine can generate. Supports non-streaming and streaming responses. |
| `POST` | `/v1/score/evaluation` | Returns reward-model scores when the loaded engine cannot generate. |

`/v1/chat/completions` returns HTTP 405 when the loaded model is a scorer/reward model rather than a generator. `/v1/score/evaluation` returns HTTP 405 when the loaded model can generate. Use the endpoint that matches the loaded model stage.

## Chat Completion Payload

The chat request model is close to OpenAI chat completions:

```json
{
  "model": "test",
  "messages": [{"role": "user", "content": "Hello"}],
  "temperature": 0.7,
  "top_p": 0.9,
  "n": 1,
  "max_tokens": 128,
  "stop": null,
  "stream": false
}
```

Supported roles are `system`, `user`, `assistant`, `function`, and `tool`. Request validation requires a valid alternating conversation after an optional first `system` message: user/tool turns at even positions and assistant/function turns at odd positions. Empty messages, invalid roles, and even-length post-system histories return HTTP 400.

Supported multimodal content item types are `text`, `image_url`, `video_url`, and `audio_url`. URL fields may contain supported base64 data URLs, local files that pass LFI checks, or remote URLs that pass SSRF checks. Multimodal model/template problems are usually data/template ownership unless they only happen after API request parsing.

Tool calling is supported in non-streaming mode through `tools`. When tools are supplied, generated tool-call text is converted into OpenAI-style `tool_calls` if the selected template can extract it. Streaming tool calls are rejected with HTTP 400: `Cannot stream function calls.` Streaming with `n > 1` is also rejected.

## Streaming Semantics

Set `stream: true` on `/v1/chat/completions` to receive server-sent events with media type `text/event-stream`. The stream sends:

1. An initial assistant delta with empty content.
2. One chunk per non-empty generated token delta.
3. A final chunk with `finish_reason: stop`.
4. A final `[DONE]` sentinel.

Clients should parse SSE events and not assume every event contains non-empty text. The bundled `scripts/openai_api_smoke.py` includes a minimal streaming check.

## Score Evaluation Payload

Use `/v1/score/evaluation` only with a loaded scorer/reward model configuration:

```json
{
  "model": "test",
  "messages": ["candidate response A", "candidate response B"],
  "max_length": 1024
}
```

The response object is `score.evaluation` and contains a `scores` list of floats. vLLM and SGLang engines do not implement `get_scores`; Hugging Face scorer/reward-model loading is the expected path.

## Native Verification Candidates

Safe candidates for later verification planning:

- Static route/protocol assertions: verify `/v1/models`, `/v1/chat/completions`, `/v1/score/evaluation`, auth behavior, streaming restrictions, and score-vs-chat 405 behavior from the API source.
- ChatModel e2e candidate: direct `ChatModel` chat and stream calls with a tiny model, when model download and dependencies are available.
- SGLang e2e candidate: chat and stream through `infer_backend: sglang`, only when CUDA and SGLang are installed and safe to launch.
- API examples candidate: function/tool-call and image chat payloads, only against a running server with a compatible model/template.
