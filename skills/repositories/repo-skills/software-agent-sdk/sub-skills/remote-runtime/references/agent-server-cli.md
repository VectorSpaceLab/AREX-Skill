# Agent-Server CLI

## Entry point

```bash
python -m openhands.agent_server --host 127.0.0.1 --port 8000
```

## Important flags

- `--host`: defaults to loopback unless auth is enabled.
- `--port`: bind port for the FastAPI app.
- `--reload`: development auto-reload.
- `--check-browser`: smoke-check browser rendering and exit.
- `--import-modules`: comma-separated modules to preload before any conversation starts.
- `--extra-python-path`: extra module search paths for custom tools.

## Runtime facts

- The server rewrites wildcard binds to loopback for internal secret lookup.
- `OH_EXTRA_PYTHON_PATH` is also honored.
- `OPENHANDS_AGENT_SERVER_CONFIG_PATH` can point at a custom config file.
- `SESSION_API_KEY` / `OH_SESSION_API_KEYS_0` control request authentication.
- `OH_DEFERRED_INIT=true` starts the server dormant until `/api/init` is posted.
