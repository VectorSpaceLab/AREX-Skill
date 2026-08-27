# Development and Testing

This reference distills ADK Python contributor setup, style, source layout, docs, samples, generated schema, and focused validation guidance for repository changes.

## Environment and Dependencies

- **Python**: use Python 3.10 or newer; contributor tooling commonly targets Python 3.11 for local development.
- **Package manager**: use `uv` for repository setup and dependency synchronization; avoid ad hoc `pip install` workflows for repo development unless diagnosing a packaging issue.
- **Base package facts**: the distribution is `google-adk` 2.3.0 and imports from `google.adk`.
- **Base install limits**: optional extras can be absent in a base environment. Missing modules for DB, MCP, extensions, cloud providers, or third-party integrations usually mean the relevant extra is not installed.

Typical contributor setup from the repository root:

```bash
uv venv --python "python3.11" ".venv"
source .venv/bin/activate
uv sync --all-extras
uv tool install pre-commit
uv tool install tox --with tox-uv
pre-commit install
```

Install narrower extras when broad `--all-extras` is inappropriate:

```bash
uv sync --extra dev --extra test
uv sync --extra docs
uv sync --extra db
uv sync --extra mcp
uv sync --extra extensions
uv sync --extra gcp
```

Use `uv build` when validating packaging and `tox` when testing across configured Python environments. Do not assume cloud, remote service, or model credentials are available.

## Formatting, Imports, and Typing

Core style defaults:

- Python files use 2-space indentation and an 80-character line limit.
- `pyink` is the formatter and `isort` uses the Google profile.
- Source code under `src/google/adk/` uses relative imports inside the framework; tests use absolute imports such as `from google.adk...`.
- Import from concrete module files rather than package `__init__.py` inside framework code.
- The `cli` package may import the rest of ADK, but non-CLI framework code must not import CLI internals.
- Use `from __future__ import annotations` after the license header in source files.
- Prefer strong typing and avoid `Any` unless there is a documented boundary reason.
- Prefer `X | None` in new code, especially workflow code; match local style in existing files when editing.
- Use `collections.abc` abstract types for input parameters when possible.
- Use keyword-only arguments for constructors or functions with multiple same-type parameters.
- Never use mutable default arguments.

Useful commands:

```bash
pre-commit run --files <changed-file> [<changed-file> ...]
pre-commit run --all-files
pyink <paths>
isort <paths>
ruff check <paths>
mypy src/google/adk
```

Pre-commit hooks include formatters and repository checks such as enforcing private-by-default new source modules. New Python implementation files under `src/google/adk/` should normally be underscore-prefixed; expose public symbols through the nearest package `__init__.py` and `__all__` only when they are intended public API.

## Pydantic and Public API Changes

ADK uses Pydantic v2 patterns:

- Use `Field()` for validation, defaults, and descriptions.
- Use `PrivateAttr()` for internal state that should not serialize.
- Use `model_post_init()` instead of overriding `__init__` for Pydantic setup.
- Use `model_dump()` rather than deprecated Pydantic v1 `dict()` style.
- For on-wire models, inherit from `SerializedBaseModel` so camelCase serialization stays consistent.
- Add `ConfigDict(use_attribute_docstrings=True)` for models whose field docstrings should become schema descriptions; this is already handled by `SerializedBaseModel`.
- Use `@field_validator(..., mode="after")` for single-field business validation and `@model_validator(mode="after")` for cross-field consistency.
- For migration validators with `mode="before"`, guard with `isinstance(data, dict)`.

When changing public APIs, constructor arguments, config models, CLI options, serialized payloads, or behavior visible to users:

1. Preserve backwards compatibility or add an explicit migration/deprecation path.
2. Add or update unit tests through public interfaces.
3. Update relevant guides under `docs/guides/` when a user-facing concept, workflow, or option changes.
4. Update samples under `contributing/samples/` when the change affects common patterns or introduces a key capability.
5. Regenerate and review config schemas if `AgentConfig`, agent config models, or schema descriptions change.

## Generated Agent Config Schema

The repository contains a source helper that generates `AgentConfig.json` from `AgentConfig` using Pydantic JSON schema generation with a fallback for invalid schema fragments. Treat schema generation as a maintainer check when changing agent config models, docstrings used as field descriptions, serialized aliases, or config validation behavior.

Safe schema validation workflow:

```bash
python scripts/generate_agent_config_schema.py
git diff -- src/google/adk/agents/config_schemas/AgentConfig.json
```

If the schema diff is expected, commit it with the source change. If the diff is surprising, inspect the changed model fields, validators, aliases, and docstrings before accepting it.

## Test Selection by Source Area

Start with the smallest behavior-focused tests, then widen.

| Changed area | Focused pytest targets |
| --- | --- |
| `src/google/adk/agents/` | `pytest tests/unittests/agents -q` plus selected flow/runner integration if execution behavior changed |
| `src/google/adk/workflow/` | `pytest tests/unittests/workflow -q` and `pytest tests/unittests/events -q` when event output changes |
| `src/google/adk/runners.py` or runner internals | `pytest tests/unittests/runners -q` plus selected integration tests such as single-agent, multi-agent, or multi-turn |
| `src/google/adk/sessions/` | `pytest tests/unittests/sessions -q` and migration tests when persistence changes |
| `src/google/adk/memory/` | `pytest tests/unittests/memory -q` |
| `src/google/adk/artifacts/` | `pytest tests/unittests/artifacts -q` |
| `src/google/adk/plugins/` | `pytest tests/unittests/plugins -q` |
| `src/google/adk/telemetry/` | `pytest tests/unittests/telemetry -q` |
| `src/google/adk/code_executors/` | `pytest tests/unittests/code_executors -q` |
| `src/google/adk/tools/` | `pytest tests/unittests/tools -q`; add auth/integration-specific tests for toolsets |
| `src/google/adk/auth/` | `pytest tests/unittests/auth -q` |
| `src/google/adk/integrations/` | focused `tests/unittests/integrations/<provider>`; avoid remote credentialed tests by default |
| `src/google/adk/a2a/` | `pytest tests/unittests/a2a -q` |
| `src/google/adk/cli/` | `pytest tests/unittests/cli -q` and selected CLI integration tests |
| `src/google/adk/evaluation/` | `pytest tests/unittests/evaluation -q` and selected eval integration tests |
| `src/google/adk/apps/` | `pytest tests/unittests/apps -q` plus CLI/API app discovery tests if loading changes |
| `src/google/adk/models/` | `pytest tests/unittests/models -q`; integration model tests may require credentials or external providers |
| `src/google/adk/planners/` | `pytest tests/unittests/planners -q` |
| `src/google/adk/flows/` | `pytest tests/unittests/flows -q` and agent integration tests when LLM flow behavior changes |
| `docs/` | docs build or markdown formatting if configured; also run code tests for referenced APIs when examples changed |
| `contributing/samples/` | run sample-specific import/test commands when available; otherwise run targeted CLI/help or pytest checks around the demonstrated feature |

Use the bundled selector for an initial map:

```bash
python skills/adk-python/sub-skills/repo-development/scripts/select_adk_tests.py src/google/adk/workflow/_base_node.py docs/guides/workflow/example.md
python skills/adk-python/sub-skills/repo-development/scripts/select_adk_tests.py workflow hitl resume
```

The selector prints likely checks only; it does not run tests.

## Test Writing Rules

ADK tests should be stable, behavior-focused, and refactor-proof:

- Test through public interfaces and assert user-visible behavior.
- Name tests for observed behavior, not implementation mechanics.
- Give each test a one-line docstring describing expected behavior; complex tests may include Setup/Act/Assert details.
- Keep one behavior per test.
- Avoid asserting private state; prefer public outputs, events, responses, or persisted results.
- Use real ADK components when practical; mock only external boundaries such as LLM APIs, cloud services, or service stores.
- Keep fixtures minimal and arrange logic close to the test unless shared by three or more tests.
- Make assertions read like a specification.
- Structure tests as arrange, act, assert with clear separation.

For workflow, resume, HITL, events, and runner tests, include deterministic IDs and normalize nondeterministic event fields before assertion when needed.

## Docs and Guides Policy

Update documentation when a change affects user-facing behavior, public API, configuration, serialized wire shape, CLI options, or a recommended workflow.

Guide expectations:

- Prefer updating an existing `docs/guides/` page incrementally when one already covers the concept.
- If creating a new guide for a code unit, place it in the relevant `docs/guides/` area and update the guide index when the title, summary, or new page needs discovery.
- Include a short summary, get-started example, how-it-works explanation, configuration options introduced by the code unit, advanced usage if relevant, limitations, and related samples.
- Avoid exhaustive API dumps in guides; focus on how to use the unit correctly.
- Do not set a fixed model in sample agents unless the user explicitly requested one.

## Sample Policy

Use samples when a change introduces or changes a capability that users need to see in context. Samples under `contributing/samples/` are minimal contributor examples, not full end-to-end customer applications.

Sample conventions:

- Use a snake_case folder name.
- Include `agent.py` and `README.md`.
- Keep `agent.py` focused on one feature or pattern.
- Use absolute imports in samples for testing convenience.
- For standalone agents, define `root_agent = Agent(...)`.
- For workflow samples, prefer `@node` for function nodes and use `Workflow` with explicit graph edges.
- Do not set `model=` in sample `Agent` instances by default.
- README files should include Overview, Sample Inputs, Graph when relevant, How To, and Related Guides.

## Native Test Tiers and Credentials

- **Unit tests** under `tests/unittests/` are the default focused validation target.
- **Integration tests** under `tests/integration/` may exercise CLI behavior, agent execution, model adapters, or evaluation fixtures; inspect whether the target needs model credentials before running.
- **Remote tests** under `tests/remote/` target cloud triggers and usually require credentials, deployed resources, or network access. Do not run them by default.
- **Model/cloud/provider tests** may need environment variables, credentials, network, or optional extras. Prefer mocked unit tests unless the user asks for credentialed verification.

## Source Script Inventory Decisions

- `scripts/check_new_py_files.sh`: maintainer/pre-commit check that enforces underscore-prefixed new Python files under `src/google/adk/`; reference it for policy, but normally let pre-commit run it.
- `scripts/generate_agent_config_schema.py`: maintainer helper to regenerate `AgentConfig.json` after config model changes; run only when config schema changes are plausible.
- Database migration scripts and service-specific helpers can have side effects; do not run migration or remote service scripts without explicit approval and a known safe target.
