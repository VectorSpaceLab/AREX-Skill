# Testing and Native Verification

Use this reference to choose focused, safe checks for CrewAI repository changes. Prefer commands that validate the changed area without exercising credentials, network services, LLM calls, release mutation, or broad suites unless explicitly requested.

## Root Tooling Configuration

The root workspace uses:

- Python `>=3.10,<3.14`.
- `uv` workspace members for all local packages.
- `pytest==9.0.3`, `pytest-xdist`, `pytest-timeout`, `pytest-randomly`, `pytest-recording`, and `pytest-subprocess` in the dev dependency group.
- `ruff==0.15.1` with `fix = true` in configuration, broad lint selections, `target-version = "py310"`, and `E501` ignored globally.
- `mypy==1.19.1` in strict mode with `python_version = "3.12"` and the Pydantic plugin.
- `bandit==1.9.2` with template directories excluded.

Root pytest configuration:

```toml
[tool.pytest.ini_options]
testpaths = [
  "lib/crewai/tests",
  "lib/crewai-tools/tests",
  "lib/crewai-files/tests",
  "lib/cli/tests",
  "lib/crewai-core/tests",
]
asyncio_mode = "strict"
asyncio_default_fixture_loop_scope = "function"
addopts = "--tb=short -n auto --timeout=60 --dist=loadfile --max-worker-restart=2 --block-network --import-mode=importlib"
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
```

Implications:

- Network is blocked by default in the root pytest suite.
- Import mode is `importlib`, which can expose differences from default pytest import behavior.
- Broad root test runs may be slow because they cover multiple packages in parallel.
- The root testpaths do not include `lib/devtools/tests`; run devtools tests explicitly.

## Lint and Type Checks

Diagnostic-only examples:

```bash
uv run ruff check --no-fix lib/crewai/src/crewai lib/crewai/tests/test_imports.py
uv run ruff format --check lib/crewai/src/crewai
uv run mypy lib/crewai/src/crewai
```

Use `--no-fix` for ruff checks unless the user asks to apply fixes, because root ruff config enables fixes. Mypy excludes template directories and test directories by default; if checking tests, use pytest/ruff rather than assuming mypy covers them.

## Focused Pytest Selection

Start with one or a few test files based on changed paths:

| Changed area | Suggested focused checks |
| --- | --- |
| CLI package, command registration, command options | `uv run pytest lib/cli/tests/test_cli.py -q`; add command-specific tests such as `test_create_crew.py`, `test_run_crew.py`, `test_train_crew.py`, `test_crew_test.py`, `test_version.py`, `deploy/test_validate.py`, or `tools/test_main.py`. |
| Core exports/import surface | `uv run pytest lib/crewai/tests/test_imports.py -q`. |
| Crew/Task runtime semantics | Selected tests in `lib/crewai/tests/test_crew.py`, `test_task.py`, `test_task_guardrails.py`, and `test_checkpoint.py`. |
| Flow/event behavior | Selected tests in `lib/crewai/tests/test_flow.py`, `test_flow_visualization.py`, `test_flow_persistence.py`, `test_flow_ask.py`, and `lib/crewai/tests/events/test_event_ordering.py`. |
| Hooks/observability | Selected tests in `lib/crewai/tests/hooks/test_decorators.py`, `test_llm_hooks.py`, `test_tool_hooks.py`, telemetry tests, and tracing tests. |
| LLM provider handling | Selected tests under `lib/crewai/tests/llms/` plus `test_custom_llm.py` or `test_streaming.py` when changed. |
| MCP handling | `lib/crewai/tests/mcp/test_mcp_config.py` and `test_tool_resolver_native.py`. |
| Memory, knowledge, RAG | Focused tests under `lib/crewai/tests/memory/`, `knowledge/`, and `rag/`; add `lib/crewai-tools/tests/rag/` for loader changes. |
| Official tools package | Focused tests under `lib/crewai-tools/tests/`, avoiding live external-service calls unless mocked or approved. |
| Files/multimodal package | `lib/crewai-files/tests/test_resolver.py`, validation/processing tests, and selected CrewAI multimodal tests. |
| Devtools docs/versioning/release logic | `uv run pytest lib/devtools/tests/test_docs_versioning.py -q` and `uv run pytest lib/devtools/tests/test_toml_updates.py -q`. |
| Docs content only | `mintlify broken-links` from the docs directory when Mintlify CLI is installed. |

Use [../scripts/select_native_tests.py](../scripts/select_native_tests.py) to generate a suggested command list from changed file paths.

## Safe Command Examples

```bash
uv run pytest lib/cli/tests/test_cli.py -q
uv run pytest lib/devtools/tests/test_docs_versioning.py -q
uv run pytest lib/crewai/tests/test_imports.py -q
uv run pytest lib/crewai-files/tests/test_resolver.py -q
uv run ruff check --no-fix lib/cli/src/crewai_cli lib/cli/tests/test_cli.py
```

Help-only checks for installed CLI surface:

```bash
crewai --help
crewai create --help
crewai deploy --help
```

These are normally safer than `crewai run`, `crewai train`, `crewai test`, `crewai replay`, or `crewai chat`, which may execute local project code or LLM-backed workflows.

## Devtools-Specific Testing

`lib/devtools/pyproject.toml` has package-local pytest settings:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--noconftest"
```

When validating docs versioning or version-bump helper behavior from the workspace root, pass explicit files:

```bash
uv run pytest lib/devtools/tests/test_docs_versioning.py -q
uv run pytest lib/devtools/tests/test_toml_updates.py -q
```

Do not substitute release commands for these tests. The tests cover freeze copy behavior, OpenAPI ref rewriting, docs.json version insertion, redirect updating, idempotency, invalid version rejection, workspace package coverage, dependency pin rewriting, and template dependency updates.

## Safe Native Verification Principles

- Prefer tests marked or known to use mocks, fixtures, local files, or help output.
- Avoid tests that require real third-party API keys, cloud services, browser automation, hosted CrewAI platform credentials, or unbounded downloads unless the user explicitly approves.
- Treat cassettes as evidence of recorded behavior, not proof that new live network calls are safe.
- If validating a generated skill or documentation recipe, adapt original native tests into small focused cases rather than running the whole suite first.
- Record skipped checks explicitly when optional dependencies, credentials, or tooling are not available.

## Mixed CLI and Docs Changes

For a change that touches a CLI command plus Edge docs:

1. Check frozen/docs image hazards first.
2. Run or suggest `python skills/crewai/sub-skills/repo-development/scripts/select_native_tests.py --changed-file ...` for the changed paths.
3. Include a CLI help or command-registration test such as `lib/cli/tests/test_cli.py`.
4. Include command-specific CLI tests if the changed path maps to run/create/train/test/deploy/auth/tool behavior.
5. Include `mintlify broken-links` if docs changed and Mintlify is available.
6. Add devtools docs-versioning tests only if docs versioning, docs scripts, or `docs/docs.json` release behavior changed.

## Broad Suite Escalation

Escalate to broader checks only after focused checks pass or when the change truly crosses multiple packages:

```bash
uv run pytest -q
uv run ruff check --no-fix lib
uv run mypy lib/crewai/src/crewai lib/cli/src/crewai_cli
```

Broad checks may be slow. If they fail outside the changed area, do not fix unrelated failures; report them as unrelated and keep the focused signal separate.
