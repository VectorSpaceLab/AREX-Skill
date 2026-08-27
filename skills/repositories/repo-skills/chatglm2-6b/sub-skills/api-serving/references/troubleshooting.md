# API Serving Troubleshooting

## Validation errors

- **`Invalid request` or HTTP 400:** the last OpenAI message is not a
  `user` message. Put the current query last and keep prior turns in strict
  `user`, `assistant` pairs.
- **History is empty or wrong:** earlier messages are odd-length, start with a
  non-system role, or use roles outside `user`/`assistant`. Run
  `validate_openai_messages.py --json ...` and inspect the normalized history.
- **Simple API returns an exception:** verify `prompt` is a string and
  `history` is a list of two-item pairs. Validate numeric generation fields
  before calling the service.

## Service startup

- **`ModuleNotFoundError: sse_starlette`:** install the package for the
  OpenAI-compatible streaming route; the basic JSON endpoint does not need it.
- **Port already in use:** identify the intended process or choose a different
  Uvicorn port. Do not start a second model worker blindly.
- **Server starts but requests hang:** model loading may still be in progress,
  the GPU may be out of memory, or a proxy may buffer SSE. Check the server
  logs, call `/docs` locally, and test non-streaming before streaming.

## Generation and resource failures

- **CUDA OOM:** lower `max_length`, reduce concurrent requests/history, use a
  supported quantized model, or dispatch across GPUs. Worker count multiplies
  model memory.
- **Model class/file error:** use a complete local model directory or an
  accessible Hub id, keep `trust_remote_code=True`, and align tokenizer/model
  revisions.
- **No incremental output:** confirm `stream: true`, use an SSE-capable client,
  consume the initial role delta and content deltas, and stop only after the
  final `finish_reason` event and `[DONE]`.

## Exposure and CORS

The sample enables wildcard CORS and has no authentication. Treat that as a
local-development default. Before non-local exposure, add authentication,
origin restrictions, request size/rate limits, timeouts, and an audit policy.
Do not send user secrets to a public endpoint merely because the sample accepts
OpenAI-shaped messages.
