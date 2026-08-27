# Troubleshooting Repo Development

Use this reference when ADK repository checks fail or when deciding whether a failure is caused by style, environment, optional dependencies, credentials, stale generated files, or unsafe workflow choices.

## Environment Problems

### `uv` is missing

Symptom: setup commands fail with `uv: command not found`.

Resolution:

- Install `uv` before syncing the repo.
- Do not switch to an unmanaged `pip` workflow for normal contributor setup.
- After installing `uv`, create a fresh virtual environment and run the selected `uv sync` command.

### Wrong Python version

Symptom: package metadata, dependency resolution, or tests fail on an unsupported interpreter.

Resolution:

- Use Python 3.10+.
- For local contributor setup, Python 3.11 is a safe default.
- If testing version-specific behavior, use `tox` rather than manually mutating the main environment.

### Missing optional dependency

Symptom: imports fail for SQL/database, MCP, extensions, cloud providers, model integrations, or service-specific packages.

Resolution:

- Treat missing optional imports as expected in a base install.
- Install the relevant extra only when the changed area requires it, for example `db`, `mcp`, `extensions`, `gcp`, `eval`, `tools`, `a2a`, `slack`, or `toolbox`.
- Prefer tests that assert graceful missing-extra behavior when maintaining base-install compatibility.
- Do not mark a base install as broken solely because an optional integration import is unavailable.

## Formatter, Import, and Lint Failures

### `pyink` rewrites many lines

Likely causes:

- Code was formatted with a different formatter.
- Line length or indentation does not match ADK style.
- Multi-line call formatting drifted from Google-style formatting.

Resolution:

```bash
pyink <changed-python-files>
pre-commit run --files <changed-files>
```

Keep the formatting diff focused; do not reformat unrelated files.

### `isort` changes import blocks repeatedly

Likely causes:

- Source code used package-level imports from `__init__.py` instead of direct module imports.
- Tests used relative imports instead of absolute `google.adk` imports.
- Third-party and local imports were mixed.

Resolution:

- In `src/google/adk/`, use relative imports within the framework and import from concrete module files.
- In `tests/`, use absolute imports from `google.adk`.
- For CLI files, keep imports within `cli` relative and imports from outside `cli` absolute.
- Ensure non-CLI framework code does not import from CLI internals.

### New source file rejected by pre-commit

Symptom: new file under `src/google/adk/` fails the private-module prefix check.

Resolution:

- Rename new implementation modules with a leading underscore.
- Export intended public symbols through the nearest package `__init__.py` and `__all__`.
- Keep internal symbols unexported.

### `mypy` failures after a small change

Likely causes:

- Missing annotations.
- New `Any` propagation.
- Optional value used without a guard.
- Pydantic migration changed inferred types.
- Runtime-only import used for type checking and introduced a cycle.

Resolution:

- Add explicit argument and return types.
- Use `from __future__ import annotations` in source files.
- Put type-only imports behind `if TYPE_CHECKING:`.
- Prefer `isinstance` checks and explicit `else` fallbacks for polymorphic values.
- Use `X | None` consistently in new code, or match the edited file style.

## Test Failures and Skips

### Focused unit tests fail, broad suite not needed yet

Resolution:

- Fix the focused failure first; do not hide it by running only broader commands.
- Confirm the failing test asserts public behavior rather than implementation internals.
- Add a regression test near the changed source hierarchy under `tests/unittests/`.

### Integration tests require model or cloud credentials

Symptoms include missing API keys, ADC failures, provider-specific auth errors, network failures, or unavailable cloud resources.

Resolution:

- Do not run credentialed tests by default.
- Prefer mocked unit tests or non-credentialed CLI help/import checks.
- If the user asks for credentialed verification, document required environment variables, service account setup, network assumptions, and possible cost.
- Record skipped remote/model/cloud checks explicitly in the handoff.

### Remote tests fail or are too expensive

Remote tests under cloud trigger or deployed-service areas can require live resources and credentials.

Resolution:

- Skip remote tests unless the user explicitly authorizes them and the environment is prepared.
- Validate local behavior with focused unit tests and integration tests that mock external services.
- Do not create, deploy, or delete cloud resources without explicit approval.

### Flaky async or workflow tests

Likely causes:

- Blocking synchronous I/O inside async code.
- Race conditions in event ordering, sessions, plugins, or callbacks.
- Resume/checkpoint behavior not deterministic.
- Tests asserting private timing or internal state.

Resolution:

- Use async APIs end-to-end.
- Wrap blocking file/network/database calls in `asyncio.to_thread` if an async replacement is unavailable.
- Assert durable public outputs: events, state deltas, final responses, stored sessions, or service calls.
- Normalize nondeterministic IDs or timestamps in tests.
- For HITL/resume, test first interrupt, partial resume, final resume, and no duplicate events.

## Docs, Samples, and Schema Drift

### Public API changed but no docs or samples changed

Resolution:

- Check whether a guide under `docs/guides/` explains the affected API or workflow.
- Update or add a guide when users need to know about the changed behavior.
- Update `contributing/samples/` when a minimal runnable pattern demonstrates the capability better than prose.
- Update sample README sections: Overview, Sample Inputs, Graph if relevant, How To, and Related Guides.

### New sample hardcodes a model

Resolution:

- Remove `model=` from sample agents unless the user explicitly requires a specific model.
- Let the environment or ADK defaults choose the model for general samples.

### Generated config schema stale

Symptoms:

- Tests or review show mismatches in `AgentConfig.json`.
- Agent config fields, aliases, validators, or docstrings changed.
- YAML config validation behavior changed.

Resolution:

```bash
python scripts/generate_agent_config_schema.py
git diff -- src/google/adk/agents/config_schemas/AgentConfig.json
```

Accept the schema diff only if it matches the intended config model change. Unexpected diffs usually indicate changed field descriptions, aliases, validators, or Pydantic schema behavior.

## Optional Extras and Base Install Compatibility

Base installs intentionally do not cover every integration. Common optional-extra failure families:

- `db`: SQLAlchemy and database-backed session services.
- `mcp`: MCP toolsets and protocol dependencies.
- `extensions`: Docker, LangGraph, LiteLLM, CrewAI, Firestore, Kubernetes, and other extended integrations.
- `gcp`: Google Cloud services and telemetry exporters.
- `eval`: evaluation dependencies such as pandas or evaluation SDKs.
- `a2a`, `slack`, `toolbox`, `tools`, `agent-identity`: specific integration families.

When changing optional integration code:

1. Keep base-import paths from importing optional dependencies at module import time unless guarded.
2. Add clear error messages that name the missing extra when practical.
3. Test both installed and missing-extra behavior if feasible.
4. Skip credentialed live-service tests unless explicitly authorized.

## Unsafe Git or Repository Operations

Do not perform these without explicit user approval:

- `git reset --hard`
- `git clean`
- force-push
- rebase of user work
- branch deletion
- deleting untracked files
- publishing packages
- creating, updating, or deleting cloud resources
- running migration scripts against real databases

If a user asks for review, stop after reporting findings unless they explicitly ask you to apply fixes.

## Quick Diagnosis Matrix

| Symptom | First check | Likely action |
| --- | --- | --- |
| Formatter diff is huge | `pyink`/line length/import layout | Reformat only changed files |
| New module rejected | File name under `src/google/adk/` | Prefix implementation file with `_` and export intentionally |
| `ModuleNotFoundError` for integration | Optional extra and test target | Install relevant extra or skip base-incompatible test |
| CLI/config schema mismatch | Agent config model or field docs | Regenerate `AgentConfig.json` and review diff |
| Workflow resume duplicate events | HITL/checkpoint/event tests | Add focused resume regression test |
| Cloud test fails locally | Credentials/network/resource setup | Skip unless authorized and environment prepared |
| Sample review flags `model=` | Sample agent defaults | Remove fixed model unless explicitly required |
| User asks for commit | Git policy | Use Conventional Commit only after validation |
