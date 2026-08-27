# Testing and Cassettes

Use this reference to choose the smallest useful validation command and to handle VCR cassettes safely.

## Command Selection

Start specific, then broaden only when the first check passes or the change touches broad behavior.

| Need | Command |
| --- | --- |
| Run one test | `uv run pytest path/to/test.py::test_name -q` |
| Run a focused set by expression | `uv run pytest path/to/test.py -k "keyword" -q` |
| Re-run last failures | `uv run pytest --lf -q` |
| Show concise failure locations | `uv run pytest path/to/test.py::test_name -vv --tb=line` |
| Typecheck one file or subtree | `PYRIGHT_PYTHON_IGNORE_WARNINGS=1 uv run pyright path/to/file.py` |
| Format one Python file | `uv run ruff format path/to/file.py` |
| Lint one Python file | `uv run ruff check path/to/file.py` |
| Format and fix all Python files | `make format` |
| Check formatting and lint all Python files | `make lint` |
| Run project pyright | `make typecheck` |
| Run local test suite without coverage | `make test` |
| Run coverage test suite | `make testcov` |
| Build docs | `make docs` |
| Serve docs | `make docs-serve` |
| Update docs examples | `make update-examples` |
| Rewrite VCR tests | `make update-vcr-tests` |
| Check cassette/test pairing | From this sub-skill directory: `python scripts/check_repo_context.py --check-cassettes` |

Prefer targeted commands while editing. Full `make`, full test suite, and full typecheck are slow and best reserved for broad changes or final gating.

## Test Defaults and Fixtures

Important defaults from the test harness:

- `pydantic_ai.models.ALLOW_MODEL_REQUESTS = False` is set in `tests/conftest.py`, so tests should not accidentally make live model requests.
- Use `allow_model_requests` only when a test intentionally exercises model-request plumbing or VCR playback/recording.
- Use `env` (`TestEnv`) to set or remove environment variables and automatically restore them after the test.
- The indirect `model` fixture maps provider names such as `openai`, `anthropic`, `google`, `groq`, `mistral`, `cohere`, `bedrock`, `huggingface`, and `test` to configured `Model` instances, using mock API keys by default where possible.
- `client_with_handler` provides an `httpx.MockTransport` client for deterministic HTTP behavior.
- `disable_ssrf_protection_for_vcr` is required for VCR tests that download URL content and need recorded hostnames to match replay.
- HTTP client tracking closes created clients at test teardown to catch lifecycle leaks.

Test style from `tests/AGENTS.md`:

- Prefer public API behavior: `Agent(...)`, `agent.run(...)`, toolsets, model wrappers, and message/output objects as users would exercise them.
- Prefer feature-centric parametrized test files over appending unrelated cases to large legacy provider files.
- Use `snapshot()` for complex structured outputs, message histories, event streams, and provider request/response shapes.
- Use helper matchers such as `IsStr`, `IsDatetime`, `IsBytes`, `IsSameStr`, and schema-stripping helpers for values that vary legitimately.
- Unit tests are appropriate when a VCR test cannot reach the branch, would not assert the relevant request body, or would be too brittle/expensive for a precise internal invariant.

## VCR Recording and Playback

Provider behavior should generally be tested against real provider responses recorded in cassettes, then verified in playback.

Safe workflow:

1. Confirm the test is narrow and targets the provider behavior that needs a real API or SDK.
2. Confirm provider credentials are available outside the public code and that recording has explicit user approval.
3. Run the target test with `--record-mode=rewrite`, usually through `source .env && uv run pytest path/to/test.py::test_name -vv --tb=line --record-mode=rewrite`.
4. Run the same target test without `--record-mode` to verify cassette playback.
5. Review code diffs separately from cassette diffs.
6. Inspect cassette request/response content for sensitive data and expected request shapes.
7. From this sub-skill directory, run `python scripts/check_repo_context.py --check-cassettes` if cassette files were added, removed, or renamed.

Do not run broad `--record-mode=rewrite tests` unless intentionally updating many cassettes. It can make many paid/network requests and create noisy cassette churn.

## Cassette Mechanics

The test harness configures `pytest-recording` and VCR with project-specific behavior:

- The custom YAML serializer in `tests/json_body_serializer.py` normalizes smart quotes and special characters, parses JSON bodies into `parsed_body`, removes or filters sensitive headers, redacts common token fields, handles compressed JSON responses, and updates content lengths where needed.
- VCR request matching includes method and path matchers; Bedrock host matching normalizes regions.
- Requests to Google OAuth token endpoints are skipped rather than recorded.
- Root cassettes usually live under `tests/cassettes/<test_module>/`.
- Model/provider cassettes usually live under `tests/models/cassettes/<test_module>/`.
- xAI uses protobuf-derived `.xai.yaml` cassette files through a custom fixture rather than normal HTTP VCR YAML.
- Playback normally fails when a cassette is partially used after a successful test; `--strict-vcr-cassette-usage` also fails when a loaded cassette has zero interactions played.

The bundled `check_repo_context.py --check-cassettes` mode parses tests and cassette directories to flag likely orphaned cassettes. It expects conventional cassette naming; custom cassette names may need manual review.

The source checkout includes cassette maintenance scripts as evidence of maintainer workflows. Treat the cassette checker as superseded by the bundled read-only mode for generated-skill use, and treat the source scrubber as a one-time mutating helper to use only with explicit intent and careful diff review.

## Snapshot Workflow

The repo wraps `inline_snapshot` to avoid expensive imports unless snapshot flags are passed.

- Normal test runs compare existing snapshots and warn on mismatch through lightweight stubs.
- Use `--inline-snapshot=create` when creating new snapshots.
- Use `--inline-snapshot=fix`, `--snap`, or `--snap-fix` when intentionally updating snapshots.
- Review generated snapshot changes for semantic correctness; do not blindly accept provider output churn.
- Prefer matchers for timestamps, IDs, bytes, generated names, and provider fields that are expected to vary.

Docs-example updates may also produce snapshot or example-output changes. Run the narrowest docs-example command first when possible, then `make update-examples` if the change intentionally updates docs examples.

## Docs Example Tests

`tests/test_examples.py` finds examples in `docs`, `pydantic_ai_slim`, `pydantic_graph`, and `pydantic_evals`, skipping `.agents` content. It copies helper modules to a temp directory, patches model inference, HTTP clients, MCP/FastMCP objects, randomness, SSL context behavior, and many provider environment variables.

When a docs example fails:

- Check example prefix settings such as `test`, `lint`, `requires`, `py`, `max_py`, `title`, and `dunder_name`.
- Check whether the example should be runnable with mocks rather than skipped.
- Check missing local example dependencies declared through `requires`.
- Check ruff/import ordering expectations in the docs harness before adding inline suppressions.
- Keep examples realistic and current; avoid historical notes and deprecated APIs in public docs.

## Provider and Model Bug Fix Case

For a provider/model bug fix with cassettes, choose validation like this:

1. If the defect is request-shape translation, write or update a targeted test that asserts the request body through `vcr` or `tests/cassette_utils.py` helpers, or through a patched client when cassette matching would not protect the field.
2. If the defect is response parsing, add a playback-backed assertion on normalized `ModelResponse`, message parts, provider details, usage, or final agent behavior.
3. Record only the affected provider/model/test with `--record-mode=rewrite` after approval and credentials are available.
4. Verify playback without recording.
5. Run targeted typecheck/lint for the changed adapter and targeted tests for both streaming and non-streaming paths when both paths share the behavior.
6. Route generated skill updates to `../models-and-providers/` when provider behavior, settings, native tools, profiles, or troubleshooting changes.

Example command sequence:

```bash
source .env && uv run pytest tests/models/test_openai.py::test_specific_behavior -vv --tb=line --record-mode=rewrite
source .env && uv run pytest tests/models/test_openai.py::test_specific_behavior -vv --tb=line
PYRIGHT_PYTHON_IGNORE_WARNINGS=1 uv run pyright pydantic_ai_slim/pydantic_ai/models/openai.py
uv run ruff check pydantic_ai_slim/pydantic_ai/models/openai.py tests/models/test_openai.py
```

Adjust provider paths and tests to the actual changed files. Do not include `.env` contents, credentials, or local paths in docs, skills, commits, or public logs.

## Public API Change Case

For a public API change, validate the contract before implementation and again before handoff:

1. Confirm issue/proposal alignment and backward compatibility.
2. Identify all affected surfaces: imports, constructor/function signatures, dataclasses, settings, docs, examples, tests, generated skills, deprecations, serialized messages/specs, and provider/tool/output behavior.
3. Add public-API tests for the new behavior and deprecation tests for old behavior if compatibility requires aliases or warnings.
4. Typecheck the changed source and tests.
5. Update docs where users naturally discover the feature, not only docstrings.
6. Update matching generated runtime skills and user-facing package skills if future agents need the new mechanics.
7. Run targeted docs-example tests if docs or docstrings include runnable examples.

Avoid using VCR as the only proof of public API behavior if the change can be tested deterministically with `TestModel`, `FunctionModel`, `Agent.override`, mocked HTTP clients, or direct schema/message assertions.

## Local Workflow Skills as Evidence

The repository includes local Claude skills that may help a maintainer understand workflows:

- `.claude/skills/testing-skill/` documents the VCR record/playback/parse workflow.
- `.claude/skills/pre-push-review/` documents a local review pass based on CI review prompts.
- `.claude/skills/address-feedback/` documents review-comment triage and response flow.

These are maintainer workflow evidence, not dependencies for generated runtime skills. Future generated skills should include self-contained instructions and safe bundled helpers instead of requiring those local skill files.
