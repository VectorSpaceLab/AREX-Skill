# Test selection

Use this reference to choose the smallest useful check set while iterating, then broaden before final handoff.

## Repository check command matrix

Run commands from the Kiln checkout root unless a command explicitly changes directory.

| Scope | Use when | Command | Notes |
| --- | --- | --- | --- |
| Full repo | Broad code changes or final verification | `uv run ./checks.sh --agent-mode` | Runs Python lint/format/typecheck, optional misspell, OpenAPI schema check, web checks/build, and Python tests. Paid, slow, and Ollama tests remain gated by pytest markers. |
| Staged files | Pre-commit style check for staged changes | `uv run ./checks.sh --staged-only --agent-mode` | Skips web/Python test groups only when staged changes do not touch those areas. Python lint/type checks still run. |
| Python lint | Any Python change | `uv run ruff check` | Use `uv run ruff check --fix` only when you intentionally want autofixes. |
| Python format | Any Python change | `uv run ruff format --check .` | Use `uv run ruff format .` to format intentionally. |
| Python typecheck | Python code, especially SDK/server/datamodel changes | `uv run ty check` | Root config excludes tests, web UI, build artifacts, venvs, and generated API client. |
| Targeted Python test | One module, behavior, or regression | `uv run python3 -m pytest --benchmark-quiet -q path/to/test_file.py -k "expression"` | Use a direct node id for a single test when possible. Add `-o "addopts="` if serial execution is required. |
| Core library tests | Datamodel, adapters, eval/RAG/fine-tune internals | `uv run python3 -m pytest --benchmark-quiet -q libs/core` | Add a narrower file or `-k` first while iterating. |
| Server/desktop tests | REST, studio server, jobs, Git sync, provider APIs | `uv run python3 -m pytest --benchmark-quiet -q libs/server app/desktop/studio_server` | Pair with schema checks when API types or routes change. |
| OpenAPI schema freshness | Route, Pydantic API model, API path/query/field, or generated client changes | `app/web_ui/src/lib/check_schema.sh` | If the diff is intentional, regenerate with `app/web_ui/src/lib/generate_schema.sh` and review generated changes. |
| Web lint | Svelte/TypeScript/CSS changes | `cd app/web_ui && npm run lint` | Run after fixing syntax/type/import problems. |
| Web format | Svelte/TypeScript/CSS changes | `cd app/web_ui && npm run format_check` | Use `npm run format` only when intentionally formatting. |
| Web type/Svelte check | Svelte components, stores, API client use | `cd app/web_ui && npm run check` | Includes `svelte-kit sync` and `svelte-check`. |
| Web unit tests | Svelte component/store tests | `cd app/web_ui && npm run test_run` | For a focused Vitest run, pass a file/filter after `--` if supported by the local Vitest version. |
| Web build | UI routing, bundling, env, or release-sensitive frontend changes | `cd app/web_ui && npm run build` | Full check script runs this for web changes. |
| E2E web tests | Explicit browser workflow request | `cd app/web_ui && npm run tests:e2e` | Heavier than normal unit checks; run only when relevant. |

The bundled helper [../scripts/kiln_repo_checks.sh](../scripts/kiln_repo_checks.sh) prints or executes the common safe subsets:

```bash
bash ../scripts/kiln_repo_checks.sh --list
bash ../scripts/kiln_repo_checks.sh --scope python --run
bash ../scripts/kiln_repo_checks.sh --scope web --run
```

## Changed-file decision tree

Use this as a practical starting point:

1. **Only Python source under `libs/core/`, `libs/server/`, or `app/desktop/`:** run `ruff check`, `ruff format --check`, `ty check`, and the nearest focused pytest file. Finish with staged or full checks depending on breadth.
2. **Datamodel or SDK-visible behavior:** add focused tests for object serialization/loading or adapter behavior, then run relevant `libs/core` tests. Check docstrings and backward compatibility.
3. **FastAPI route or API Pydantic model:** run server/desktop targeted tests, `app/web_ui/src/lib/check_schema.sh`, and web type checks if generated client or UI call sites are affected.
4. **OpenAPI generated client drift:** if the schema diff is intended, run `app/web_ui/src/lib/generate_schema.sh`, review the generated TypeScript changes, then run web `npm run check` plus schema check again.
5. **Svelte component/store/routes:** run web `format_check`, `lint`, `check`, focused Vitest test, then `test_run` and `build` for broad UI changes.
6. **CSS/Tailwind/visual-only change:** still run web format/lint/check. Add component tests when behavior, accessibility state, or data rendering changes.
7. **Dependency, workspace, lock, or package metadata change:** run import probes, full Python/web checks, and at least one representative server/app import. Avoid manually loosening Starlette/FastAPI constraints.
8. **Docs/spec-only change:** run spelling/format checks when available. Code tests are usually unnecessary unless examples or commands were changed.
9. **Local maintenance skill change under `.agents/`:** read that skill's safety boundary. Paid, network, Slack, or source-modifying steps still require confirmation.

## Pytest markers and gates

Marker registration lives in the root pytest config and gate behavior is implemented by root test collection hooks.

| Marker | Default behavior | Opt-in flag | Use carefully because |
| --- | --- | --- | --- |
| `paid` | Skipped by default | `--runpaid` | Makes real paid provider/API calls and needs credentials. |
| `prerelease` | Not selected by default; with `--runprerelease`, non-prerelease tests are skipped | `--runprerelease` | Curated paid release smoke subset. It implies paid behavior for those tests and should run serially for live provider stability. |
| `slow` | Skipped by default | `--runslow` | Can be expensive in wall-clock time. |
| `ollama` | Skipped by default | `--ollama` | Requires a running local Ollama service and supported models. |

Useful examples:

```bash
uv run python3 -m pytest --benchmark-quiet -q libs/core/kiln_ai/adapters/test_file.py -k "case_name"
uv run python3 -m pytest --runprerelease -v --tb=short -o "addopts="
uv run python3 -m pytest --runpaid -v --tb=short -o "addopts=" path/to/test_file.py::test_name
uv run python3 -m pytest --ollama -q path/to/test_file.py
```

Do not use skip-bypass flags to hide missing paid/Ollama prerequisites. If credentials or services are absent, report a coverage gap instead of forcing an invalid run.

## Targeted API and web combinations

For changes that cross backend and frontend, pair checks so the contract is tested from both sides:

| Change | Backend checks | Frontend/schema checks |
| --- | --- | --- |
| Add or rename route | Focused route tests; route table/import test if present | `app/web_ui/src/lib/check_schema.sh`; regenerate if intentional; `npm run check` |
| Add request/response field | Pydantic/unit tests around defaults and validation | Schema check; generated client review; component/store tests that render/use the field |
| Change path/query parameter | Route tests for old/new behavior and error handling | Schema check; TypeScript call-site update; `npm run check` |
| Add SSE/job behavior | Focused server tests for stream/lifecycle/disconnect | Store/component tests for snapshot, reconnection, stale callbacks, and error states |
| Add provider/UI setting flow | Mocked provider/server tests first | Web store/component tests; do not hit live provider unless explicitly asked |

## Paid, prerelease, cloud, and service caveats

- Paid provider tests require explicit user direction and credentials. Missing keys should be reported as skipped coverage, not treated as code failures.
- Prerelease checks should be read-only: run standard checks, run the curated paid smoke set, diagnose failures, and write/report findings. Do not silently edit code or whitelists as part of a prerelease check.
- Ollama checks require a local Ollama service and installed supported models.
- Copilot, cloud provider, Docker Model Runner, and remote MCP flows require credentials or running services. Do not probe them during ordinary safe maintenance.
- Use `-k` filters carefully. For parametrized model/provider tests, prefer exact bracketed node-id filters when available rather than broad boolean expressions that can match unintended cases.

## Evidence notes

Commands and marker behavior came from `AGENTS.md`, `checks.sh`, root `pyproject.toml`, `conftest.py`, and `app/web_ui/package.json`.
