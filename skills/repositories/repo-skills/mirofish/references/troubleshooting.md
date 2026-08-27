# Cross-cutting troubleshooting

## Backend will not start

Symptoms:

- `python run.py` exits with configuration errors.
- `npm run backend` starts uv but Flask does not bind.
- `/health` is unreachable.

Checks:

1. Confirm Python is 3.11 or 3.12.
2. Confirm backend dependencies are installed with `uv sync` or an equivalent editable backend install.
3. Create `.env` and set `LLM_API_KEY` plus `ZEP_API_KEY`.
4. Remove `ZEP_API_URL`; MiroFish validates and rejects it because only Zep Cloud is supported.
5. If debug mode is on, expect Flask reloader double-start behavior; logs may appear twice.

## Frontend is reachable but API calls fail

Symptoms:

- UI loads on port 3000 but graph/setup/report calls fail.
- Browser console shows network or CORS errors.

Checks:

1. Confirm backend is listening on port 5001 and `/health` returns ok.
2. Confirm the frontend API base URL matches the backend host/port used by the deployment.
3. Stop any other service occupying ports 3000 or 5001, or override the backend port with `FLASK_PORT` and update the frontend/deployment routing.
4. For Docker, confirm both ports are published and the container can read `.env`.

## Dependency install conflicts

Symptoms:

- `uv sync` fails.
- OASIS/CAMEL dependency resolution conflicts with existing global packages.
- Tests import a different `app` package.

Checks:

1. Use a fresh Python 3.11/3.12 environment for backend work.
2. Prefer the repository's uv lock or pyproject metadata instead of manually installing arbitrary latest OASIS/CAMEL packages.
3. Run backend commands from the backend package context so `app` resolves to MiroFish's backend package.
4. Use `pip check` after editable installs to catch inconsistent packages.

## LLM provider request errors

Symptoms:

- Ontology/profile/report calls fail with provider schema errors.
- Provider rejects temperature or token arguments.
- JSON-mode output fails intermittently.

Checks:

1. Verify `LLM_BASE_URL` is OpenAI SDK compatible and matches the key.
2. Verify `LLM_MODEL_NAME` is a deployed chat model.
3. MiroFish has compatibility handling for GPT-5-style `max_completion_tokens` and one retry without `response_format` when JSON mode is rejected; repeated failures usually mean provider configuration or quota limits.
4. For high-consumption scenarios, lower simulation rounds or use smaller test documents before long runs.

## Zep Cloud errors

Symptoms:

- Graph build/read/delete fails.
- Entity reads return authentication or permission errors.
- Report graph tools return Zep failures.

Checks:

1. Ensure `ZEP_API_KEY` is set for Zep Cloud.
2. Do not configure self-hosted `ZEP_API_URL`.
3. Treat auth and permission errors as hard configuration failures.
4. Treat network, 408, 429, and 5xx issues as retryable only where the owning sub-skill says the operation is read-only or idempotently reconciled.
5. Use graph lifecycle locks: active simulations, memory updaters, or reports can block reset/delete.

## Long simulation or report run is consuming too much

Symptoms:

- OASIS processes keep running.
- API status stays active for too long.
- Report agent performs many tool calls.

Checks:

1. Use fewer rounds first; the README recommends trying fewer than 40 rounds while validating keys and cost.
2. Use `simulation-run` stop/close-env guidance instead of killing arbitrary processes unless recovery requires it.
3. Lower Report Agent limits with `REPORT_AGENT_MAX_TOOL_CALLS` and `REPORT_AGENT_MAX_REFLECTION_ROUNDS`.
4. Do not start report generation until simulation and graph-memory updater have reached a terminal state.

## Generated artifacts are stale or inconsistent

Symptoms:

- Setup profiles do not match the current graph.
- Report refers to an old simulation.
- Graph visualization no longer matches profiles.

Checks:

1. Keep `project_id`, `graph_id`, `simulation_id`, and `report_id` pairs together.
2. Regenerate setup after resetting or rebuilding a graph.
3. Force-regenerate a report only after confirming the simulation and graph are stable.
4. Use the sub-skill artifact references before deleting files manually.

## Safe manual validation boundaries

- Safe routine checks: config check, `/health`, bundled script self-tests, backend import smoke, unit tests with mocked LLM/Zep surfaces.
- Manual/credentialed checks: live Zep Cloud validation, real graph ingestion, real OASIS runs, long report generation, destructive graph deletion.
- Unsafe as default smoke: root star-history maintenance scripts, long platform launcher scripts, or validation scripts that can create/delete cloud graphs.
