# Setup and Config Troubleshooting

## `everos` command not found

- Confirm the package is installed in the environment that owns your shell PATH.
- Try `python -m pip show everos` and reinstall with `python -m pip install everos`.
- Run `python scripts/check_everos_install.py --json` from this sub-skill directory to inspect import, metadata, CLI discovery, and no-lifespan app construction.

## `everos server start` says config is missing

The server requires `<root>/everos.toml`. Use the same root everywhere:

```bash
everos init --root /data/everos
everos config show --root /data/everos
everos server start --root /data/everos
```

If `EVEROS_ROOT` is set, it may point somewhere unexpected. Explicit `--root` wins.

## Server startup fails on LLM config

Normal startup eagerly builds the LLM client. Fill `[llm] api_key` and `base_url`, or export `EVEROS_LLM__API_KEY` and `EVEROS_LLM__BASE_URL`. If you only need schema inspection, use the no-lifespan OpenAPI helper instead of starting the server.

## Health says optional features are disabled

This is expected when providers are not configured:

| Missing capability | Disabled features commonly reported |
|---|---|
| embedding | `vector_search`, `hybrid_search`, `reflection`, `skill_extraction`, `knowledge` |
| rerank | `agentic_search`, `knowledge` |
| multimodal LLM or parser | `multimodal_upload` |

Configure the corresponding TOML/env section and restart the server.

## Demo fails in a non-interactive shell

Use `everos demo --plain`. Interactive TUI mode needs a terminal. Live mode needs a running server and provider-backed memory extraction.

## Binding beyond loopback

EverOS does not include auth. If `--host 0.0.0.0` is required, put the service behind a gateway that handles auth, TLS, and request-size limits.
