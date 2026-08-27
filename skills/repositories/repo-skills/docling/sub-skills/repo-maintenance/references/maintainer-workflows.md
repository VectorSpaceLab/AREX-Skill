# Maintainer Workflows

Use these workflows for repository-editing tasks. They are contributor-focused, not end-user conversion recipes.

## Standard Change Loop

1. Read the closest `AGENTS.md` instructions before editing.
2. Identify the smallest package, module, docs, or test surface that owns the behavior.
3. Make scoped changes consistent with the surrounding style.
4. Add or update focused tests only when they verify behavior, regressions, or integration boundaries.
5. Run the most specific affected tests first.
6. Run `make validate` before completion; rerun it if hooks mutate files.
7. Use `make check` for a read-only broad verification pass when practical.

Important project norms:

- Prefer structured Pydantic models or dataclasses over loose dictionaries when data crosses module boundaries or becomes a stable contract.
- Prefer `pathlib.Path` for new or edited path-handling code.
- Avoid broad attribute probing such as unnecessary `hasattr(...)` or loose `getattr(...)` checks.
- Do not add trivial tests that only restate implementation details.

## Makefile Commands

- `make setup`: install a CI-style development environment using `uv sync --frozen --group dev --all-extras --no-group docs --no-group examples`.
- `make test`: run the default pytest suite with verbose output.
- `make check`: run read-only checks including Ruff format/check, type checking, Tach checks, custom script checks, dprint, and locked dependency validation.
- `make validate`: run pre-commit hooks only on changed, staged, and untracked files; hooks may mutate files.
- `make validate-all`: run hooks on all files.
- `make fix`: run configured Ruff and dprint fixers.
- `make docs-render`: pre-render example notebooks/scripts and CLI reference.
- `make docs-build`: render docs artifacts and build the static docs site.
- `make docs-clean`: remove generated docs artifacts.

## CLI Flag or Command Changes

When changing CLI flags, option defaults, help text, or command structure:

1. Update the Typer/Click command implementation and keep public behavior typed.
2. Update CLI tests, usually under CLI-focused tests, to cover the changed option behavior and failure mode.
3. Regenerate CLI reference with `make docs-render` or the CLI reference rendering script.
4. If the change affects remote commands, service URL/API key handling, or optional `.env` loading, update service-client tests and troubleshooting docs.
5. Run targeted tests before broader validation.

Synthetic hard case: a contributor adds `--ocr-profile` to the local CLI. The safe plan is to update option parsing, route it into the relevant pipeline options, add CLI tests for valid/invalid values, regenerate generated CLI docs, and verify optional OCR dependencies remain extras-bound rather than base dependencies.

## Backend or Format Changes

When editing a format backend or conversion behavior:

1. Locate the backend-specific tests, such as tests for PDF, HTML, Markdown, Office, image, audio, XML, email, CSV/XLSX, EPUB, VTT, Docling JSON, or DocLang behavior.
2. Keep optional dependencies optional; backend imports may require model or format extras that are not installed in minimal environments.
3. Use targeted pytest paths first, for example backend-specific tests or API smoke tests.
4. If serialized conversion output changes intentionally, regenerate reference data with the project-supported environment variable and review the generated diff carefully.
5. Consider limits and safety parameters exposed by `DocumentConverter.convert`, including page ranges, max pages, max file size, headers, and `raises_on_error`.

Synthetic hard case: a contributor changes table handling in a PDF backend. The focused plan is to run PDF/table-specific tests, inspect whether reference outputs changed intentionally, regenerate data only for approved behavior changes, and avoid updating unrelated snapshots.

## Docs and Examples Generation

Docs generation uses scripts that create derived artifacts from source content:

- CLI reference generation introspects the `docling` and `docling-tools` command trees and emits a generated Markdown reference page.
- Notebook/example rendering converts Jupyter notebooks and Jupytext percent-format Python scripts under docs examples into generated Markdown while preserving relative structure.
- Plain Python scripts without Jupytext percent markers are skipped by example rendering.

Use `make docs-render` after changing CLI command surfaces or source examples referenced by the docs. Use `make docs-build` when navigation, generated pages, or site rendering may be affected.

## Tests and Optional Skips

Pytest markers identify tests that may download models, execute ML code, require ASR, require VLMs, use cross-platform smoke lanes, or require external services. Do not assume all optional tests are safe in every environment.

Prefer this order:

1. Run the narrowest changed tests.
2. Add marker selection or skips only when the dependency/backend requirement is real and documented.
3. Run broader suites when environment and time allow.
4. Record skipped optional coverage in handoff notes rather than pretending it passed.

Common targeted areas include CLI tests, service client SDK/unit/integration tests, backend tests by format, extraction tests, input document tests, conversion result JSON tests, and data-generation flag tests.

## Source-Script Inventory

Contributor scripts include:

- CLI reference rendering for generated command documentation.
- Notebook/example rendering for docs examples.
- Maximum line-count checking with warning/silent ignore patterns.
- Tach module coverage checking to ensure Python modules are covered by module-boundary configuration.

When changing or adding scripts:

- Keep them safe to run from the checkout root.
- Prefer deterministic output and clear nonzero exits for failures.
- Keep file path handling based on `Path` where possible.
- Add tests or validation hooks only when they prove useful repository behavior.

## CI Awareness

Workflow files cover main CI, docs CI/CD, heavy examples, publishing, fast pull-request checks, and release/reminder automation. For local work, align with Makefile targets first; inspect CI only when behavior differs between local checks and workflow lanes.
