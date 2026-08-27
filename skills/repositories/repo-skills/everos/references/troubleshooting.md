# Cross-Cutting Troubleshooting

## Install or import fails

Symptoms:
- `No module named everos`
- `everos: command not found`
- package resolver rejects Python version

Likely causes and fixes:
1. Use Python 3.12 or newer.
2. Install the public distribution: `python -m pip install everos`.
3. If the CLI is not on `PATH`, run `python -m pip show everos` to confirm installation and use the environment's console-script directory or reinstall in the active environment.
4. For multimodal parsing install `everos[multimodal]`; for tracing install `everos[otel]`.
5. Run the setup helper: `python sub-skills/setup-and-config/scripts/check_everos_install.py --json`.

## Server does not start

Symptoms:
- `everos.toml not found`
- provider configuration errors during startup
- port already in use

Recovery:
1. Generate config with `everos init --root <root>`.
2. Start with the same root: `everos server start --root <root>`.
3. Fill `[llm] api_key` and `base_url`; the normal server lifespan eagerly builds the LLM client.
4. Change `--port` or `EVEROS_API__PORT` if the default port is occupied.
5. Keep bind host as `127.0.0.1` unless an authenticated gateway is in front.

## Provider gate errors

Common error code: `PROVIDER_NOT_CONFIGURED` with a message naming `llm`, `embedding`, `rerank`, or `multimodal_llm`.

- Memory extraction requires LLM settings.
- Vector/hybrid/agentic retrieval and many evolution paths require embedding and/or rerank.
- Knowledge writes and knowledge search require both embedding and rerank.
- Multimodal parsing requires the parser extra plus multimodal LLM settings.

Do not present missing provider behavior as a package bug. It is usually an intentionally surfaced configuration gate.

## Search misses immediately after write

`/add` and `/flush` write Markdown synchronously when extraction occurs, but LanceDB projection is asynchronous. If search is empty right after a write:

1. Retry with backoff for several seconds.
2. Check `/health` and inspect the `cascade` block if present.
3. For local deterministic operation, run `everos cascade status` or `everos cascade sync` on the same memory root.

## Wrong memory root

Symptoms:
- Config looks correct but server sees no memory.
- CLI status shows empty queue for a root that should have data.

Check root resolution order: explicit `--root`, then `EVEROS_ROOT`, then the default. Use `everos config show --root <root>` and keep server, cascade CLI, and client expectations aligned.

## Security boundary

EverOS ships no built-in authentication. Do not bind the server to public interfaces without a gateway or reverse proxy that handles authentication, authorization, TLS, and body-size limits.
