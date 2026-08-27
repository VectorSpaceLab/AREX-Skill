---
name: api-services
description: "Help future agents create, launch, inspect, and troubleshoot the
  FastAPI service Opyrator exposes for wrapped functions."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# api-services

Use this sub-skill when the user needs the HTTP API service that Opyrator exposes for a wrapped callable.

## What it covers
- `create_api(Opyrator) -> FastAPI`
- `launch_api(opyrator_path, port=8501, host="0.0.0.0")`
- `patch_fastapi(app)`
- `POST /call`, `GET /info`, `GET /` redirecting to `./docs`
- `/docs`, `/redoc`, and `/openapi.json` behavior after patching
- permissive CORS defaults
- OpenAPI generation from `Opyrator.input_type` and `Opyrator.output_type`
- service host and port selection for local startup
- array responses for wrapped callables that return `list[BaseModel]` or a root model around a list

## Route elsewhere
- CLI call/export/deploy and function wrapping: `../wrapping-and-cli/SKILL.md`
- Streamlit UI, file rendering, and component schema behavior: `../ui-and-components/SKILL.md`

## Start here
- Root router: `../../SKILL.md`
- Shared compatibility pins and install guidance: `../../references/troubleshooting.md`
- In-process smoke helper: `scripts/api_smoke.py`

## Evidence basis
The bundled references were distilled from the runtime API helpers, the public README API section, example wrappers and OpenAPI specs, and the package pin set that governs the compatible FastAPI and Starlette stack.

## Success signals
- `create_api` returns a `FastAPI` app without launching a server.
- `/call` uses the wrapped callable's input model for request validation and its output type for `response_model`.
- `/info` is present and returns an empty metadata object.
- `/` redirects to `./docs`.
- `/docs` and `/redoc` remain usable through relative URLs after patching.
- A callable with invalid input or output annotations fails before service creation.
