# API service troubleshooting

For package-pinning and environment-level issues, also see `../../../references/troubleshooting.md`.
This page only covers the FastAPI service surface.

| Signal | Likely cause | Fix |
| --- | --- | --- |
| `ImportError: cannot import name 'graphql' from starlette` or `ModuleNotFoundError: starlette.graphql` | The installed FastAPI/Starlette pair is newer than the compatible stack that this snapshot expects, but `patch_fastapi` still imports `starlette.graphql`. | Use the verified compatible stack for this snapshot (`fastapi==0.63.0`, `starlette==0.13.6`, `pydantic<2`, `uvicorn<0.24`) or update the patch before relying on the patched docs routes. |
| `ValueError: The callable MUST have a parameter with the name \`input\`` | The wrapped function is not Opyrator-compatible. | Add an `input` parameter with a type annotation that points to a Pydantic model. |
| `ValueError: The return value MUST be a subclass of the Pydantic BaseModel or a list of Pydantic models.` | The return annotation is missing or not Pydantic-compatible. | Return a `BaseModel`, or a list of `BaseModel` items. Keep the failure if you are testing the negative path; service creation should stop here. |
| `/docs` or `/redoc` load but asset URLs are absolute, or the app is mounted under a subpath and docs break | `patch_fastapi(app)` was skipped or the app was built with a raw `FastAPI` object instead of `create_api(...)`. | Call `create_api(...)` or `patch_fastapi(app)` before serving, then verify the HTML contains `./openapi.json` and the root route redirects to `./docs`. |
| `opyrator launch-api ...` cannot import the target callable | The CLI only appends the current working directory to `sys.path` before resolving the callable string. | Run the command from the directory that contains the module, or make the target importable as `module:function` / `module.function`. |
| The service starts on the wrong port or host | The direct helper and CLI wrapper use different port defaults. | Pass `--port` and `--host` explicitly. Remember: the Python helper defaults to `8501`, while the CLI defaults to `8080`, and both default to `0.0.0.0`. |
| `launch_api` never returns | This is expected; it calls `uvicorn.run(...)` and blocks. | Use `create_api(...)` and `TestClient` when you only need to inspect routes or OpenAPI in-process. |
| A deliberately bad callable fails before the app exists | The output or input annotation is invalid. | Keep the failure. The correct outcome is a clear annotation error, not a half-built server. |
