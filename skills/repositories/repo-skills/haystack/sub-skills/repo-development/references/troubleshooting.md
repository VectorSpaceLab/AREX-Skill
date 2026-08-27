# Haystack Repository Development Troubleshooting

## Hatch and Install Failures

Symptoms:

- `hatch: command not found`
- Hatch creates or syncs an environment repeatedly.
- Imports fail only inside repository commands.

Actions:

1. Run `hatch --version` from the repository root before any repository Python command.
2. If Hatch is unavailable, pause and install or locate Hatch before continuing; do not switch to bare `python` or `pip`.
3. If the environment is stale or corrupted, use `hatch env prune`, then rerun the Hatch command.
4. For one-off scripts requiring test dependencies, run `hatch -e test run python SCRIPT.py`.
5. For temporary experiments only, install inside the active Hatch environment with `uv pip install PACKAGE` and avoid committing dependency changes unless the task is dependency-related.

## Import and Package Confusion

Symptoms:

- `ModuleNotFoundError: No module named 'haystack'`.
- Imported behavior does not match edited source.
- A globally installed `haystack-ai` package shadows the checkout.

Actions:

- Run tests through Hatch so the checkout package is installed in the managed environment.
- Avoid running bare `python -c 'import haystack'` from an arbitrary shell.
- Confirm changed code is under the package source tree and that the corresponding test imports the same public or internal symbol.
- If testing public package behavior rather than repository internals, route to the relevant sibling sub-skill for runtime usage instead of changing repository commands.

## Optional Dependency Failures

Symptoms:

- Tests fail importing `transformers`, `sentence_transformers`, `pypdf`, `openai-whisper`, `tika`, `azure`, or document conversion packages.
- A component test fails because a heavy backend is missing.

Actions:

1. Use the Hatch test environment: `hatch run test:unit ...` or `hatch run test:integration ...`.
2. Check whether the test is marked `integration` or `slow`; do not force slow/backend tests into a unit workflow.
3. If a dependency is intentionally optional for package users, assert clear import errors or skip behavior in tests instead of making it mandatory.
4. When a backend requires system services or model downloads, document the skip and run the closest deterministic unit test.

## Credential and Backend Failures

Symptoms:

- OpenAI, Hugging Face, Azure, AWS, search API, tracing, or external service tests fail because secrets or services are missing.
- Integration tests time out against Docker or network backends.

Actions:

- Do not invent or embed credentials.
- Prefer unit tests with mocked clients for code paths that can be validated without network calls.
- Run integration tests only when the required service, Docker container, or credential is available and the change directly affects that integration.
- If an integration test is unsafe or unavailable, record the exact command that would validate it and the reason it was skipped.

## API Misuse While Editing Tests

Symptoms:

- Pipeline tests fail with missing component input, unknown socket, type mismatch, or repeated component run errors.
- Component tests fail because outputs are missing or socket names changed.

Actions:

- For public pipeline/component API details, route to `../pipelines-and-components/SKILL.md`.
- In repository tests, assert the exact public error message when changing validation behavior.
- Keep custom test components small and deterministic; declare outputs with `@component.output_types(...)`.
- When changing serialization, test both `to_dict()` and `from_dict()` or equivalent round-trip behavior.

## Data and Config Failures

Symptoms:

- Tests fail because fixture files are missing, binary formats differ, or expected metadata changed.
- YAML, TOML, or JSON config changes break parser tests or CI checks.

Actions:

- Reuse existing fixture files under `test/test_files/` before adding new large fixtures.
- Keep fixture assertions stable: check counts, keys, metadata fields, and representative content, not full brittle blobs unless exact output is the feature.
- For config edits, run the smallest related test plus `hatch run fmt-check` or `hatch run fmt` when Python formatting/linting can be affected.
- For package metadata changes, inspect `pyproject.toml` and run the focused command that exercises that metadata when available.

## Pytest Selection Problems

Symptoms:

- `-k` selects no tests.
- A direct node id is not found.
- Unit command unexpectedly runs integration tests.

Actions:

1. Check the path and class/function names in the test file.
2. Prefer a file path first, then add a `-k` keyword once selection is confirmed.
3. Use `hatch run test:unit` for tests not marked `integration`; use `hatch run test:integration` for tests with the integration marker.
4. If a change touches shared fixtures or helpers, broaden from one test node to the containing file or directory.

## Type Check Failures

Symptoms:

- `hatch run test:types` fails in an unrelated area.
- Mypy reports missing stubs or incomplete definitions.

Actions:

- First determine whether the error is caused by the changed files; do not fix unrelated type debt.
- Prefer precise annotations over `Any`, `cast`, or `type: ignore`.
- If a `type: ignore` is unavoidable, make it as narrow as possible and explain the reason in the handoff.
- Remember that the configured type check covers `haystack` and selected test directories, not every test file.

## Format and Lint Failures

Symptoms:

- Ruff changes files unexpectedly.
- Lint errors appear after a focused test passes.
- Markdown/MDX Python examples are reformatted.

Actions:

- Run `hatch run fmt` to apply repository formatting fixes.
- Use `hatch run fmt-check` when you only need a non-mutating check.
- If doc code blocks are reformatted by `scripts/ruff_format_docs.py`, keep the example valid Python and let the hook normalize layout.
- Do not add broad lint disables for local style issues; follow the existing `pyproject.toml` configuration.

## Release Note Failures

Symptoms:

- CI says a release note is missing.
- Release note rendering or pre-commit fails on backticks.
- Reno cannot create a note.

Actions:

1. For user-facing code, dependency, or behavior changes, run `hatch run release-note short-description`.
2. Edit the generated YAML under `releasenotes/notes/` and keep only relevant sections.
3. Use reStructuredText inline code with double backticks, for example ``Pipeline``.
4. Check notes with `hatch -e test run python scripts/release_note_backticks.py --check releasenotes/notes/file.yaml`.
5. Do not create a release note for docs-only, tests-only, or CI-only changes unless maintainers request one.

## Docs Website Failures

Symptoms:

- Docusaurus reports broken links, duplicate routes, missing sidebars, or blank local pages.
- API reference edits disappear or conflict.

Actions:

- For narrative docs, edit `docs-website/docs/`; for stable-doc fixes, also update the highest `docs-website/versioned_docs/version-*` copy.
- Add new pages to `docs-website/sidebars.js` and include required frontmatter.
- Do not manually edit generated API reference pages; change Python docstrings instead.
- For cross-plugin links between docs and reference, use absolute `/docs/...` or `/reference/...` paths.
- If local Docusaurus pages are blank, clear cache with `npm run clear` from `docs-website/`, then rebuild or restart.

## Workflow-Specific Decision Failures

When uncertain which checks are enough, use this escalation order:

1. Run the closest unit test path or node id.
2. Run the containing test file or directory.
3. Run `hatch run fmt` or `hatch run fmt-check` if Python, docs code blocks, configs, or scripts changed.
4. Run `hatch run test:types` if public signatures, dataclasses, core pipeline/component types, or typed tests changed.
5. Run integration tests only for changed integration behavior and only when required backends are available.
6. Add or validate release notes for user-facing changes.

If validation remains incomplete, hand off exact commands not run and why: missing Hatch, missing credentials, unavailable Docker/service, slow/unstable backend, or unrelated existing failures.
