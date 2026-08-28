# HTTP serving contract

Launch the stateless server with `fastvideo serve --config`. Main endpoints are:

- `POST /v1/videos/generations` for synchronous video generation.
- `GET /v1/videos` and `GET /v1/videos/{id}` for in-memory job listing/status.
- `GET /v1/videos/{id}/content` for ready MP4 content.
- `POST /v1/images/generations` for image generation.
- `GET /v1/models` for registered model metadata and `/health` for liveness.

A video request can carry `prompt`, `size` (`WIDTHxHEIGHT`), `seconds`, `fps`,
`num_frames`, `seed`, `num_inference_steps`, `guidance_scale`,
`negative_prompt`, and an input reference. Request extensions include guidance,
TeaCache, and output controls when supported by the selected model.

Merge precedence is client-explicit body fields, then operator-explicit fields
under `default_request`, then hardcoded fallback. This distinction matters:
Pydantic/dataclass schema defaults that the operator did not write must not mask
request intent.

Errors use an OpenAI-style `{ "error": {"type": ..., "message": ...} }`
envelope. Typical status codes are 400 for validation, 404 for unknown jobs,
409 for duplicate IDs, 500 for pipeline failure, and 503 when no generator is
ready or shutdown is in progress.

Continuation is an opaque JSON-serializable `state` envelope. Clients may
round-trip it and request a fresh state with an output flag when the selected
pipeline supports it; do not deserialize payload internals generically.
