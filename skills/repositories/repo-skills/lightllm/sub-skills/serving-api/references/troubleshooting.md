# Serving troubleshooting

## 4xx from `/generate` or `/v1/*`

### Symptoms
- Validation errors from FastAPI / Pydantic.
- A request that works on `/v1/completions` fails on `/v1/chat/completions`.
- A multimodal client returns an empty or malformed payload.

### Causes
- The request envelope does not match the endpoint family.
- Chat messages were sent to a completion endpoint or vice versa.
- Structured message blocks were flattened into a string.
- `response_format`, `tools`, or reasoning fields do not match the client.

### Recovery
- Re-read `references/api-reference.md`.
- Compare against the exact request model and field types.
- Start with the smallest request that uses only `model`, input text, and
  `max_tokens` / `max_new_tokens`.

## Streaming never completes

### Symptoms
- The server starts streaming but the client never sees an end marker.
- The client receives only the first chunk.

### Causes
- Client code closes the connection early.
- The parser assumes a single JSON document instead of SSE chunks.
- The server is waiting on model output and the client timed out too early.

### Recovery
- Consume the stream incrementally.
- Add a longer client timeout for the smoke test.
- Use `scripts/request_smoke.py` to verify the local round trip.

## `/v1/messages` fails

### Symptoms
- The Anthropic route returns an import or capability error.

### Causes
- `litellm` is missing.
- The request payload does not follow Anthropic message conventions.

### Recovery
- Install the missing optional dependency.
- Compare the request with the examples in `references/workflows.md`.

## Profiler endpoints do nothing

### Symptoms
- `/profiler_start` and `/profiler_stop` return a disabled or inactive message.

### Causes
- The server was started without `--enable_profiling`.

### Recovery
- Restart the server with the profiler flag appropriate to the chosen backend.
- Use `--enable_profiling torch_profiler` or `--enable_profiling nvtx` only
  when the workflow needs it.

## Readiness vs health confusion

### Symptoms
- Health is green, but a benchmark or client still fails immediately after
  startup.

### Causes
- The model is still loading.
- A process is bound but not yet ready to serve requests.

### Recovery
- Use `/readiness` for launch validation.
- Wait for the model load stage to finish before retrying the smoke request.

## Proxy leakage

### Symptoms
- Local `curl` or `requests` calls fail only in the current shell.

### Causes
- `http_proxy` / `https_proxy` are still set.
- `no_proxy` does not include local addresses.

### Recovery
- Clear the proxy variables for the smoke call.
- Add `localhost` and `127.0.0.1` to `no_proxy`.
