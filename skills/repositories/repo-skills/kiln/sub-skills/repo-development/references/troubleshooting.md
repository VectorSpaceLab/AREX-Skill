# Troubleshooting repo development

Use this reference when ordinary Kiln maintenance checks, imports, schema checks, web tooling, optional provider flows, or local maintenance workflows fail.

## Check script fails before running checks

Symptoms:

- `uv run ./checks.sh --agent-mode` cannot find `checks.sh`.
- The bundled helper says it cannot locate a Kiln checkout.
- Commands run from a subdirectory and paths resolve incorrectly.

Fixes:

```bash
pwd
ls checks.sh pyproject.toml
bash skills/disco/kiln/sub-skills/repo-development/scripts/kiln_repo_checks.sh --list
```

Run repo-level commands from the checkout root. The helper can locate the root when executed from the normal generated skill path, but direct commands in this sub-skill assume the checkout root.

## Workspace imports fail

Symptoms:

- `ModuleNotFoundError: kiln_ai`, `kiln_server`, or desktop modules.
- `uv run` cannot resolve workspace members.
- Import probes behave differently from installed package probes.

Fixes:

```bash
uv run python - <<'PY'
import kiln_ai, kiln_server
print("kiln workspace imports OK")
PY
uv run python - <<'PY'
from kiln_server import make_app
app = make_app()
print(len(app.routes))
PY
```

Use the workspace environment for checkout maintenance. Verified distribution evidence covered `kiln-ai`, `kiln-server`, and `kiln-studio-desktop` 1.0.4, but source maintenance should still use the current checkout's workspace resolution.

## Starlette/FastAPI incompatibility

Symptoms:

- FastAPI TestClient, middleware, static files, CORS, or route inspection failures after dependency changes.
- Server app import succeeds but request handling fails in Starlette internals.

Known version evidence:

- Starlette 1.6 is incompatible with the current server code.
- Starlette 0.52.1 worked in the verified environment.
- The root workspace uses dependency override constraints to force a safe Starlette minimum. Do not loosen transitive dependencies casually.

Checks:

```bash
uv run python - <<'PY'
import fastapi, starlette
print("fastapi", fastapi.__version__)
print("starlette", starlette.__version__)
PY
```

Fix dependency drift through the workspace lock/config rather than ad hoc package upgrades.

## MCP imports or tools fail

Symptoms:

- `kiln_mcp --help` or MCP tool import fails.
- Server tools import errors mention the `mcp` package.
- MCP route/tool listing works in one environment but not another.

Fixes:

```bash
uv run python - <<'PY'
import mcp
print("mcp import OK", getattr(mcp, "__version__", "unknown"))
PY
kiln_mcp --help
```

The current tools imports need a lock-compatible `mcp` package at the 1.10.1 level. If the installed version is outside the lock-compatible range, resolve dependencies through the workspace rather than pinning manually in isolation.

## RAG or LanceDB optional imports fail

Symptoms:

- Document/RAG imports fail while unrelated repo checks pass.
- Errors mention LanceDB, vector-store dependencies, or `pandas`.

Fixes:

```bash
uv run python - <<'PY'
import pandas
print("pandas import OK")
PY
```

LanceDB-backed RAG imports needed `pandas` in the verified environment. Route detailed RAG/indexing behavior to `rag-documents-data`; for repo maintenance, treat missing optional RAG dependencies as a scoped environment issue unless the task requires RAG coverage.

## OpenAPI schema check fails

Symptoms:

- `app/web_ui/src/lib/check_schema.sh` reports a diff.
- TypeScript says an endpoint path, query parameter, or schema field is missing.
- Web UI compiles only after hand-written type changes.

Fixes:

```bash
app/web_ui/src/lib/check_schema.sh
app/web_ui/src/lib/generate_schema.sh
app/web_ui/src/lib/check_schema.sh
cd app/web_ui && npm run check
```

Regenerate only when the API change is intentional. Review generated TypeScript changes for unexpected route removals, renamed schemas, or broad diffs that indicate a server import problem.

## Web tooling fails

Symptoms:

- `npm run check`, `lint`, `format_check`, `test_run`, or `build` fails.
- Svelte or TypeScript errors appear after an API/schema change.
- Vitest cannot find browser-like globals.

Fixes:

```bash
cd app/web_ui && npm run format_check
cd app/web_ui && npm run lint
cd app/web_ui && npm run check
cd app/web_ui && npm run test_run
cd app/web_ui && npm run build
```

Common causes:

- Generated OpenAPI types are stale after backend changes.
- A component bypassed existing stores/helpers and duplicated API types.
- A raw dropdown was placed in a table/dialog/scroll area instead of using floating menu controls.
- Svelte 5 patterns were introduced into the Svelte 4 codebase.
- Formatting was not run after editing `.svelte` files.

## Pytest unexpectedly skips tests

Symptoms:

- Tests are collected but marked skipped with reasons mentioning `--runpaid`, `--runslow`, or `--ollama`.
- `--runprerelease` skips non-prerelease tests.

Interpretation:

- `paid`, `slow`, and `ollama` tests are skipped by default.
- `--runprerelease` selects only `prerelease` tests and implies paid behavior for that curated subset.
- Skips due to missing credentials or services are coverage gaps, not proof that code works.

Fixes:

```bash
uv run python3 -m pytest --benchmark-quiet -q path/to/test_file.py
uv run python3 -m pytest --runslow -q path/to/test_file.py
uv run python3 -m pytest --ollama -q path/to/test_file.py
uv run python3 -m pytest --runpaid -v --tb=short -o "addopts=" path/to/test_file.py::test_name
```

Run paid or service-backed flags only when the user asks and prerequisites are present.

## Paid, provider, Ollama, cloud, and Copilot flows fail

Symptoms:

- Provider tests fail with 401/403/429/5xx, missing key, quota, or model-not-found errors.
- Ollama routes say the service is unavailable or no supported model is installed.
- Copilot or cloud flows fail while local checks pass.

Fixes:

- Treat paid/provider/Ollama/cloud/Copilot flows as optional unless the task explicitly requires them.
- Confirm credentials/services before running live checks.
- For missing credentials, report skipped coverage instead of code failure.
- For rate limits, 5xx, and timeouts, retry once only when the workflow specifically calls for it.
- For provider model-not-found errors, route model-list semantics to `task-execution-providers-tools` or local deprecation maintenance as appropriate.
- For Ollama, ensure the local service is running and has at least one supported model installed before using `--ollama`.

## Prerelease check confusion

Symptoms:

- A prerelease task starts modifying code.
- A green prerelease run omits model-pin staleness information.
- Missing provider keys are reported as failures.

Fixes:

- Keep prerelease checks read-only: standard checks, curated paid smoke tests, diagnosis, staleness sweep, and report.
- Missing keys are skipped coverage.
- A model-pin staleness sweep is required even when tests pass.
- Do not edit prerelease whitelists or source during the prerelease report unless the user starts a separate fix task.

## Legal, license, or signing boundary appears

Symptoms:

- A PR template asks for CLA attestation.
- A dependency license is GPL/copyleft or unclear.
- A task asks to add a license file or set an OSS/MIT/proprietary tag.

Fixes:

- Stop and ask for a human decision.
- Do not fill out CLA attestations.
- Do not add or change license files or license metadata tags.
- Treat GPL/copyleft dependency additions as a critical issue that cannot be waived by the agent.

## Evidence notes

Troubleshooting evidence came from `AGENTS.md`, `checks.sh`, `pyproject.toml`, `conftest.py`, `app/web_ui/package.json`, server/package import verification, and verified environment gotchas: `mcp` compatibility at 1.10.1, Starlette 1.6 incompatibility with Starlette 0.52.1 working, LanceDB/RAG imports needing `pandas`, and optional paid/provider/Ollama/cloud/Copilot paths requiring credentials or running services.
