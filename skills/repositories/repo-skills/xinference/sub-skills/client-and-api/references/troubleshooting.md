# Troubleshooting

## Fast triage

1. Check the base URL first.
   - Xinference client: `http://HOST:PORT`
   - OpenAI-style SDK: `http://HOST:PORT/v1`
2. Confirm the model UID is launched and visible in `list_models()`.
3. Confirm the request family matches the model type.
4. If auth is enabled, confirm the `Authorization: Bearer ...` header or client token.
5. Re-test with a placeholder prompt/query before changing model parameters.

## Common failures

### 404 or missing route

- Usually means the wrong base URL shape.
- Use the service root for `Client` and the `/v1` URL for OpenAI-style calls.
- If you pointed the OpenAI SDK at the service root, it will miss the `/v1/...` routes.

### Authentication errors

- A `401` or `403` usually means a missing, expired, or wrong bearer token.
- Use `Client.login(...)` / `AsyncClient.login(...)` when the cluster advertises auth support, or pass a valid API key in the constructor.
- If the cluster is running without auth support, login is a no-op and the API key may be ignored.
- Bootstrap, OIDC, admin setup, and policy changes belong in `operations-and-security`.

### `get_model()` returns the wrong handle or raises

- The model UID may not exist.
- The model may still be loading.
- The model may have the wrong type/ability for the handle you expected.
- Inspect `describe_model(MODEL_UID)` before changing the client code.

### Strict chat ordering errors

- Some LLMs require the first `system` message to come before every other role.
- If a strict model sees a later `system` message, Xinference returns HTTP 400.
- Keep the first `system` message at index 0 and keep tool messages in a valid chat sequence.

### Launch payload validation errors

- `replica` must be an integer-like value `>= 1`.
- Booleans and floats are rejected.
- `replica_config` cannot be combined with `worker_ip`, `n_gpu`, or `gpu_idx`.

### Streaming confusion

- `stream=True` changes the return type.
- The sync client returns an iterator; the async client returns an async iterator.
- Do not call `.json()` on a streaming response.
- If you want a single JSON payload, turn streaming off.

### OCR looks like plain text but still fails to parse

- The OCR endpoint returns JSON content, even when the OCR result is a simple string.
- Use the client helper or parse JSON explicitly.

### Embedding length or truncation issues

- Embedding requests accept `truncate_prompt_tokens`.
- `None` means no truncation.
- Use a positive limit when you need deterministic length control.

### Async client construction seems slow

- The async client performs a synchronous auth probe during construction.
- Create one client per endpoint and reuse it instead of building a new client for every request.

## When to switch sub-skills

- Need a launch recipe, CLI flag set, or distributed placement plan: `serving-and-cli`.
- Need a model family or backend choice: `models-and-backends`.
- Need auth DB setup, OIDC, API-key policy, or admin bootstrap: `operations-and-security`.
