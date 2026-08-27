# Haystack Repository Development Commands

## Environment Rules

Haystack uses Hatch for environment and dependency management.

- Check the tool first: `hatch --version`.
- Do not use bare `python` or `pip` for repository work.
- Run ad hoc Python scripts with test dependencies as `hatch -e test run python SCRIPT.py`.
- Open a test-dependency shell with `hatch -e test shell` only when an interactive session is needed.
- Install temporary experiment dependencies inside the active Hatch environment with `uv pip install PACKAGE`, then remove them or document that they were temporary.
- Reset Hatch environments with `hatch env prune` when dependency state is corrupt.

## Focused Test Selection

Prefer the smallest safe check before broader validation. Hatch passes extra arguments through to pytest.

| Changed area | First focused command | Broaden when |
|---|---|---|
| `haystack/components/<group>/...` | `hatch run test:unit test/components/<group>/test_*.py -k "keyword"` | Shared component contracts, serialization, or multiple groups changed |
| `haystack/core/pipeline/...` | `hatch run test:unit test/core/pipeline -k "keyword"` | Pipeline execution, async, breakpoints, serialization, or graph behavior changes |
| `haystack/core/component/...` | `hatch run test:unit test/core/component -k "keyword"` | Component decorator or socket behavior changes |
| `haystack/core/super_component/...` | `hatch run test:unit test/core/super_component -k "keyword"` | Super-component wrapping, input/output mapping, or serialization changes |
| `haystack/dataclasses/...` | `hatch run test:unit test/dataclasses -k "keyword"` | Public data model serialization or backward compatibility changes |
| `haystack/document_stores/...` | `hatch run test:unit test/document_stores -k "keyword"` | Filter policy, duplicate handling, or document store API changes |
| `haystack/tools/...` | `hatch run test:unit test/tools -k "keyword"` | Tool schema, invocation, serialization, or ComponentTool behavior changes |
| `haystack/testing/...` | `hatch run test:unit test/testing -k "keyword"` | Fixture/factory behavior changes across test suites |
| `haystack/tracing/...` | `hatch run test:unit test/tracing -k "keyword"` | OpenTelemetry, Datadog, logging tracer, or global tracer changes |
| `haystack/evaluation/...` | `hatch run test:unit test/evaluation -k "keyword"` | Evaluation result serialization or metric behavior changes |
| `test/...` only | Run the edited test path directly | Test helpers or fixtures affect multiple files |
| `scripts/...` | `hatch -e test run python path/to/script.py --help` or a safe dry run | Script is wired into pre-commit or release workflow |
| `releasenotes/notes/...` | `hatch -e test run python scripts/release_note_backticks.py --check releasenotes/notes/file.yaml` | Many release notes changed |

Examples:

```bash
hatch run test:unit test/core/pipeline/test_pipeline.py::TestPipeline::test_run
hatch run test:unit test/components/routers/test_file_router.py -k file_type
hatch run test:integration test/components/retrievers -k in_memory
```

Integration tests use the `integration` pytest marker and may need Docker, credentials, local services, or optional backends. Prefer `hatch run test:integration-only-fast ...` when slow tests are not relevant. Use `hatch run test:integration-only-slow ...` only when a change directly affects a slow/unstable integration path.

## Test Layout and Fixtures

- Unit tests live mostly under `test/` and are selected by `hatch run test:unit`, which runs pytest with coverage and excludes tests marked `integration`.
- Integration tests are marked with `@pytest.mark.integration`; slow/unstable ones also use `@pytest.mark.slow`.
- Shared fixtures start at `test/conftest.py`; more specific fixtures live near their suites, such as generator and pipeline breakpoint feature tests.
- Test data lives under `test/test_files/` for text, markdown, PDFs, images, CSV/XLSX, JSON/YAML, audio, office documents, and HTML.
- Keep unit tests deterministic: mock external services, avoid model inference, and assert data counts, output keys, metadata, serialization, and error messages rather than only success.

## Quality Checks

Run these from the repository root:

```bash
hatch run fmt
hatch run test:types
```

`hatch run fmt` runs Ruff checks with automatic fixes and Ruff formatting. `hatch run test:types` runs mypy over `haystack` and selected test areas. Avoid `type: ignore`, casts, or assertions unless they are the smallest correct fix; if unavoidable, explain why in the PR or handoff.

For a quicker formatting gate without mutation, use:

```bash
hatch run fmt-check
```

## Release Notes

Every user-facing PR that is not docs-only, tests-only, or CI-only needs a release note unless maintainers explicitly label it to ignore release notes.

Create one with:

```bash
hatch run release-note short-description
```

Then edit the generated file under `releasenotes/notes/`:

- Keep only the relevant section such as `features`, `enhancements`, `fixes`, `deprecations`, or `upgrade` if present in the template.
- Use reStructuredText, not Markdown.
- Use double backticks for inline code: ``ComponentName``.
- For code blocks, use RST directives such as `.. code:: python`.
- Run the backtick checker on edited release notes when uncertain:

```bash
hatch -e test run python scripts/release_note_backticks.py --check releasenotes/notes/your-note.yaml
```

## Docs Changes

For narrative docs, edit `docs-website/docs/` for the next release. For a fix that also affects current stable docs, edit the matching page under the highest `docs-website/versioned_docs/version-*` directory too.

When adding or moving documentation pages:

- Include required page frontmatter: `title`, `id`, `description`, and optional `slug`.
- Update `docs-website/sidebars.js` for narrative docs.
- Update `docs-website/reference-sidebars.js` only when API reference navigation actually needs manual changes.
- Do not manually edit generated API reference content; update Python docstrings instead.
- For links within `docs/`, use relative links. Between docs and reference, use absolute `/docs/...` or `/reference/...` paths.
- For substantial docs edits, run Docusaurus checks from `docs-website/` with `npm run build` if Node dependencies are installed.

Python code blocks in Markdown/MDX are formatted by `scripts/ruff_format_docs.py` in pre-commit contexts. If examples fail formatting, fix the example code rather than disabling the hook.

## Contribution Checklist

Before handing off a repository change, report:

1. Hatch availability check, if commands were run.
2. Focused tests run, including exact pytest paths or `-k` selectors.
3. Whether broader checks were run or intentionally skipped: `hatch run fmt`, `hatch run test:types`, integration tests, docs build.
4. Whether tests, docs, and release notes were added or judged unnecessary.
5. Any unavailable credentials, backend services, optional dependencies, or slow tests that blocked validation.

Use conventional-commit style PR titles, follow the PR template, and include an AI-generated disclaimer if the PR was fully generated by an AI assistant.
