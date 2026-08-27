# Testing and Quality

Use this reference to select verification for repository changes. Start with the narrowest safe checks for the edited area, then run the required full stack when repository policy applies.

## Canonical Commands

Run commands from the repository root.

| Need | Command | Notes |
| --- | --- | --- |
| Install or refresh dev environment | `make sync` | Runs `uv sync --all-extras --all-packages --group dev`. |
| Apply formatting and safe Ruff fixes | `make format` | Runs `uv run ruff format` then `uv run ruff check --fix`. |
| Check formatting only | `make format-check` | Useful when avoiding mutation. |
| Lint only | `make lint` | Runs `uv run ruff check`. |
| Typecheck | `make typecheck` | Runs `make mypy` and `make pyright` in parallel. |
| Full test suite | `make tests` | Runs parallel shard-safe tests, then serial tests. |
| Parallel tests | `make tests-parallel` | Runs `uv run pytest -n auto --dist loadfile -m "not serial"`. |
| Serial tests | `make tests-serial` | Runs `uv run pytest -m serial`. |
| Focused pytest | `uv run pytest -s -k <pattern>` | Best first pass for changed code. Prefer a specific file/test when known. |
| Coverage | `make coverage` | Fails if coverage is below the configured threshold. |
| Fix inline snapshots | `make snapshots-fix` | Mutates existing snapshots, then rerun `make tests`. |
| Create inline snapshots | `make snapshots-create` | Creates new inline snapshots, then rerun `make tests`. |
| Build docs | `make build-docs` | Runs reference generation and `mkdocs build`. |
| Full docs with translations | `make build-full-docs` | Runs translation automation and `mkdocs build`; use only when appropriate. |
| Serve docs locally | `make serve-docs` | Preview only; not a validation substitute. |

## Mandatory Verification Policy

When `$code-change-verification` applies, the mandatory local order is:

```bash
make format
make lint
make typecheck
make tests
```

It applies to changes in:

- `src/agents/` or shared runtime utilities.
- `tests/`, including snapshot tests.
- `examples/`.
- Build/test/doc configuration such as `pyproject.toml`, `Makefile`, `mkdocs.yml`, `docs/scripts/`, or CI workflows.

It can usually be skipped for docs-only or repo-meta changes, unless docs have behavior impact or the user asks for full verification.

## Focused Test Selection

Use focused tests before the full stack to shorten iteration.

| Changed area | First focused commands |
| --- | --- |
| `src/agents/run_state.py` | `uv run pytest -s tests/test_run_state.py tests/test_tool_origin.py tests/test_run_impl_resume_paths.py -k "run_state or schema or from_json or to_json or resume"` |
| `src/agents/run.py` or `src/agents/run_internal/` | `uv run pytest -s tests/test_agent_runner.py tests/test_agent_runner_streamed.py tests/test_run_step_execution.py tests/test_run_impl_resume_paths.py` |
| Public constructor or dataclass field order | `uv run pytest -s tests/test_source_compat_constructors.py` |
| Tool/function-tool behavior | `uv run pytest -s tests/test_function_tool.py tests/test_handoff_tool.py tests/test_run_step_execution.py -k "tool"` |
| MCP behavior | `uv run pytest -s tests/mcp` |
| Model/provider behavior | `uv run pytest -s tests/models` |
| Realtime behavior | `uv run pytest -s tests/realtime` |
| Voice imports or voice pipeline | Check optional voice dependencies before running voice tests; base install does not include voice extras. |
| Sandbox behavior | `uv run pytest -s tests/sandbox` plus extension-specific sandbox tests when touched. |
| Sessions and memory | `uv run pytest -s tests/memory tests/extensions/memory` |
| Docs source | `make build-docs` after snippet/source checks. |
| `pyproject.toml` / `Makefile` / CI workflows | Run affected make target first, then full verification when code-change policy applies. |

The bundled helper [../scripts/select_test_targets.py](../scripts/select_test_targets.py) automates this mapping for changed path lists, but still only prints suggestions.

## Inline Snapshots

Some tests use inline snapshots. If changes intentionally alter snapshot output:

1. Run the failing focused test to confirm the snapshot diff is expected.
2. Use `make snapshots-fix` for changed snapshots or `make snapshots-create` for new snapshots.
3. Inspect the mutated test files carefully.
4. Rerun `make tests` to prove the updated snapshots pass.

Do not update snapshots just to hide unexpected behavior; first understand the behavioral change.

## Public API Positional Compatibility

When editing exported dataclasses, constructors, or public call surfaces:

- Treat positional parameter and dataclass field order as compatibility-sensitive.
- Append optional fields whenever possible.
- Preserve old positional meanings for released APIs.
- Add or update compatibility tests that instantiate the old positional call pattern.
- Include tests for any compatibility shim or old keyword alias.

Focused check:

```bash
uv run pytest -s tests/test_source_compat_constructors.py
```

If the changed public surface is not covered there, add a targeted regression test in the closest existing compatibility test file.

## RunState Serialization Quality Bar

For `RunState` shape changes, require more than ordinary unit coverage:

| Requirement | Why |
| --- | --- |
| Bump `CURRENT_SCHEMA_VERSION`. | New `to_json()` payloads must advertise the new durable shape. |
| Add `SCHEMA_VERSION_SUMMARIES` entry. | Import-time assertions require every supported version to have a non-empty summary. |
| Preserve old supported versions. | Released snapshots must remain readable. |
| Add round-trip tests. | New fields must survive `to_json()` and `from_json()`. |
| Add legacy-read tests. | Older payloads should receive safe defaults or documented errors. |
| Check nested state when relevant. | Agent-as-tool, sandbox resume state, pending approvals, and nested states can hide schema gaps. |

Useful focused commands:

```bash
uv run pytest -s tests/test_run_state.py -k "schema or version or roundtrip or from_json or to_json"
uv run pytest -s tests/test_tool_origin.py -k "legacy or run_state"
uv run pytest -s tests/sandbox/test_compatibility_guards.py -k "RunState or roundtrip or compatibility"
```

## Docs Build Quality Bar

For docs changes:

- Verify code snippets against current source signatures before documenting them.
- Do not edit generated translation folders for normal English-source updates.
- Run `make build-docs` for source docs, API reference, `mkdocs.yml`, or `docs/scripts/generate_ref_files.py` changes.
- Use full translation automation only when the task explicitly covers translated docs or release docs maintenance.

`make build-docs` first creates missing API reference stubs, then runs `mkdocs build`.

## Optional or Service-Backed Tests

Some tests may rely on optional extras, Docker, browser/audio libraries, provider credentials, hosted services, Redis/MongoDB/Dapr, or other local services. Do not silently mark failures as product bugs when the environment is missing optional services. Record skips or environment failures separately from code failures, and run base-install checks where possible.

## Final Handoff Checklist

Before reporting eligible changes complete:

- Summarize files changed and behavior changed.
- Report focused commands and full-stack commands run, with failures or skips.
- State whether snapshots were updated.
- State compatibility review outcome for public API or serialized-state changes.
- Include the required PR draft summary for eligible changes.
