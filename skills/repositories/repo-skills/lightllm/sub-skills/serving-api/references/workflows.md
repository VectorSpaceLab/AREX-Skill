# Serving workflows

This reference gives concrete request templates for the serving surface.
Use it together with the root API and CLI references.

## 1. Start a single-node server

```bash
python -m lightllm.server.api_server \
  --model_dir /path/to/model \
  --model_name my-model \
  --port 8000
```

Add only the flags required by the selected model family or endpoint family.
For example, `--enable_multimodal`, `--use_tgi_api`, `--use_reward_model`, or
`--enable_profiling` only when the workflow needs them.

## 2. Smoke `/generate`

```bash
curl -sS http://127.0.0.1:8000/generate \
  -H 'Content-Type: application/json' \
  -d '{"inputs":"Hello","parameters":{"max_new_tokens":16}}'
```

Expected shape: a JSON object with a `generated_text` field.

## 3. Smoke OpenAI completions

```bash
curl -sS http://127.0.0.1:8000/v1/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"my-model","prompt":"Hello","max_tokens":16,"stream":false}'
```

Use this when a client expects completion-style prompts rather than chat
messages.

## 4. Smoke OpenAI chat completions

```bash
curl -sS http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{"model":"my-model","messages":[{"role":"user","content":"Hello"}],"max_tokens":16}'
```

Use this when a client needs tool calls, reasoning options, or message lists.

## 5. Smoke Anthropic Messages

```bash
curl -sS http://127.0.0.1:8000/v1/messages \
  -H 'Content-Type: application/json' \
  -d '{"model":"my-model","messages":[{"role":"user","content":"Hello"}],"max_tokens":16}'
```

This route depends on the Anthropic compatibility layer and therefore on
`litellm` being installed.

## 6. Readiness and profiler control

```bash
curl -sS http://127.0.0.1:8000/readiness
curl -sS http://127.0.0.1:8000/profiler_start
curl -sS http://127.0.0.1:8000/profiler_stop
```

Prefer readiness over health when a script needs the service to be usable.

## 7. Multimodal requests

For multimodal message flows, the `content` field is not always a plain string.
It may be a list of structured blocks with image or audio URLs. Compare the
payload shape against `references/api-reference.md` before debugging the server.

## 8. Streaming requests

Streaming endpoints return incremental chunks. A client should:

1. keep the HTTP connection open,
2. consume each chunk as it arrives,
3. not assume a single JSON object at the end,
4. and treat the final chunk as the end of the generation.

## 9. Local smoke helper

`../../scripts/request_smoke.py` can be used to send one tiny request to a
running server before a larger benchmark or integration test.

## 10. When to stop and inspect instead of retrying

Stop and inspect the payload if you see:

- validation errors from the request model,
- empty streamed output,
- a response shape that does not match the selected endpoint family,
- or a `litellm` / `uvloop` / `ujson` import failure on the serving path.
