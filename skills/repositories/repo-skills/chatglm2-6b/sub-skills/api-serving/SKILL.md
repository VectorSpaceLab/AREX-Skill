---
name: api-serving
description: "Guides ChatGLM2-6B FastAPI and OpenAI-compatible serving, request
  validation, conversation-history mapping, streaming SSE, and safe local
  deployment."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# ChatGLM2-6B API Serving

Use this route for the repo's HTTP services, curl/OpenAI client integration,
SSE streaming, endpoint contracts, or service troubleshooting. Use
[`chat-and-demos`](../chat-and-demos/SKILL.md) for local UI/CLI generation and
[`ptuning`](../ptuning/SKILL.md) when the model is a prefix/full fine-tuned
checkpoint.

## Choose the endpoint

- **Simple API:** a FastAPI POST `/` accepting `prompt`, optional `history`,
  `max_length`, `top_p`, and `temperature`. It returns `response`, updated
  `history`, `status`, and a timestamp.
- **OpenAI-compatible API:** `GET /v1/models` plus
  `POST /v1/chat/completions`. Use this for clients that already speak the
  Chat Completions protocol. The repository supports normal JSON responses and
  Server-Sent Event streaming.

Read [`api-contracts.md`](references/api-contracts.md) before writing a client.
Read [`deployment.md`](references/deployment.md) before starting Uvicorn; the
service loads model weights once, keeps global `model`/`tokenizer` state, and
binds a listener. Run the bundled validators first:

```text
python sub-skills/api-serving/scripts/validate_api_payload.py --json '{"prompt":"你好","history":[]}'
python sub-skills/api-serving/scripts/validate_openai_messages.py --json '{"model":"chatglm2-6b","messages":[{"role":"user","content":"你好"}]}'
```

## Serve safely

1. Select a complete model directory or Hub id and a backend; the repo's
   launch path calls `.cuda()` and assumes model weights fit on one or more
   GPUs.
2. Install `fastapi`, `uvicorn`, and `sse-starlette` for the OpenAI streaming
   route in addition to the model runtime.
3. Bind to localhost while testing. Use one worker unless you deliberately
   duplicate model memory and have an external process policy.
4. Validate request roles/history before sending traffic. For streaming,
   parse JSON chunks until the final `finish_reason` chunk and `[DONE]`.
5. Treat CORS and `allow_origins=["*"]` as development defaults, not a
   production security policy. Add authentication, origin restrictions, rate
   limits, and timeouts outside this legacy sample.

The source route introspection is safe and confirms `/`, `/v1/models`, and
`/v1/chat/completions`; it does not prove that a model can load. Use
[`troubleshooting.md`](references/troubleshooting.md) for model, port, role,
SSE, and memory failures.
