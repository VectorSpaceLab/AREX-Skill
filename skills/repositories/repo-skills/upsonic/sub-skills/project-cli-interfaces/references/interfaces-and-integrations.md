# Interfaces and Integrations

## Server behavior

- `upsonic run` first loads `upsonic_configs.json`.
- If the entrypoint returns an `InterfaceManager`, Upsonic starts that interface server.
- Otherwise, Upsonic builds a FastAPI `/call` app from the declared input and output schemas.

## Helpful internal helpers

- `load_config(...)` reads and caches `upsonic_configs.json`.
- `modify_openapi_schema(...)` adjusts OpenAPI output for generated endpoints.
- `get_fastapi_imports()` keeps the CLI from importing heavy dependencies until it really needs them.

## What to remember

- This route is about project serving and packaging, not the model itself.
- Keep the config JSON tiny and valid before blaming the server runtime.
