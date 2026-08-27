# Kiln Cross-Cutting Troubleshooting

Read this before debugging failures that span multiple Kiln packages or before assuming a sub-skill-specific workflow is broken.

## Install and import failures

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ImportError: cannot import name 'streamablehttp_client' from mcp.client.streamable_http` while importing `kiln_ai.tools` or MCP adapters | A resolver installed an incompatible major `mcp` release. Current repo evidence used `mcp[cli]==1.10.1`. | In a checkout, prefer `uv run` / the repo lock. In a package env, pin `mcp[cli]==1.10.1` until the code supports newer MCP APIs. Re-run `python -m pip check` and import `kiln_ai.tools`. |
| `ImportError: cannot import name 'collapse_excgroups' from starlette._utils` while importing `kiln_server.server` | A resolver selected a Starlette release whose private utility no longer matches the server code. | Prefer the repo lock/override. The verified inspection env worked with `starlette==0.52.1`. Re-run `python -m pip check` and `python -c "from kiln_server.server import make_app; print(len(make_app().routes))"`. |
| RAG/vector-store import fails with `No module named 'pandas'` | LanceDB/LlamaIndex vector-store import path needs pandas even when a minimal resolver missed it. | Install `pandas`, then run the RAG sub-skill helper. Do not treat this as requiring a provider key or cloud LanceDB account. |
| `ModuleNotFoundError: No module named 'app'` outside a checkout | Desktop/studio-server source modules are checkout-bound. The desktop distribution metadata does not make the whole monorepo source importable from arbitrary environments. | For installed package work, use `kiln-ai` and `kiln-server`. For desktop/studio-server maintenance, work inside a Kiln checkout and follow the server/desktop/web sub-skill. |
| Provider call fails with 401/403/404/429/5xx or timeout | Missing/invalid key, stale model slug, provider outage/rate limit/quota, or network issue. | Check provider config in `task-execution-providers-tools`; use mocked/local tests for code changes. Run paid/prerelease tests only after explicit approval and credentials. |

## Checkout checks fail

1. Use [scripts/kiln_repo_checks.sh](../scripts/kiln_repo_checks.sh) or the repo-development sub-skill helper to choose the narrowest useful command first.
2. Python code normally needs `ruff check`, `ruff format --check .`, `ty check`, and a targeted pytest command before the full `uv run ./checks.sh --agent-mode`.
3. Backend API changes that affect the web UI need the OpenAPI schema check; if stale, regenerate schema from the checkout before web type checks.
4. Web UI changes need `npm run format_check`, `npm run lint`, `npm run check`, and targeted Vitest/Playwright commands as appropriate.
5. Paid/prerelease/Ollama markers are not normal CI failures when credentials/services are absent; record them as optional coverage gaps unless the user asked for that coverage.

## Data/model validation errors

- Kiln names are filename-safe and reject forbidden filename characters, repeated whitespace/underscores, and too-long names. Fix the name rather than bypassing validation.
- `Task.output_json_schema` must be an object schema; `Task.input_json_schema` can be object or array. Use the project-datamodel schema reference before constructing JSON by hand.
- `Task.runs()` returns leaf runs by default. If diagnostics require every on-disk run in a multiturn chain, pass `include_intermediate_runs=True`.
- `.kiln` files include `model_type` and schema version. A mismatched type or too-new version is a hard load error and usually means the caller opened the wrong file or needs a newer Kiln version.

## External services and credentials

Do not silently run these workflows:

- paid/prerelease provider tests;
- Ollama or Docker Model Runner checks that require local services or downloads;
- Copilot/Kiln Pro calls;
- cloud LanceDB, hosted fine-tune provider, Vertex/Bedrock/AWS calls;
- desktop signing, installer release, or outward-facing release posts.

Ask for explicit approval, required credentials/services, cost expectations, and stopping conditions before running them.
