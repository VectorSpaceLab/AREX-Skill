# Native Verification

LangChain is a multi-package Python monorepo. There is no root `pyproject.toml`; validation is package-local under `libs/*`, each with its own `pyproject.toml` and `uv.lock`. Use `uv` for dependency and command execution.

## Verification Ladder

Start narrow, then broaden only when useful:

1. Changed test file only: `uv run --group test pytest tests/unit_tests/path/to/test_file.py`.
2. Owning unit-test directory: `uv run --group test pytest tests/unit_tests/...`.
3. Static checks: `uv run --group lint ruff check .` and `uv run --group typing mypy .`, or package Makefile equivalents.
4. Package import/version scripts: run only if the package provides them.
5. Integration checks: run only with user approval and required credentials/services/cassettes.

Use the bundled `scripts/select_safe_langchain_checks.py` helper linked from this sub-skill's `SKILL.md` to inspect a package and print a safe starting command set.

## Common Package-Local Commands

From `libs/<package>`:

```bash
uv sync --group test
uv run --group test pytest tests/unit_tests/path/to/test_file.py
uv run --group lint ruff check .
uv run --group typing mypy .
```

Package Makefiles may expose equivalent or stricter targets:

```bash
make test
make lint
make format
make type
make check_imports
make check_version
```

Prefer existing Makefile targets when they are present and clearly scoped to the package. Otherwise use `uv run` commands derived from dependency groups in `pyproject.toml`.

## Import And Version Scripts

Several packages include check scripts under their local `scripts/` directory.

- `check_imports.py` loads Python files to detect import-time failures. It is useful after moving modules, changing optional imports, or editing public package exports.
- `lint_imports.sh` uses grep rules to forbid disallowed cross-package imports. For example, core packages avoid importing higher-level `langchain` packages except specifically allowed APIs.
- `check_version.py` compares package metadata with package-specific version files or generated artifacts. In core it also checks snapshot metadata that embeds the `langchain-core` version.

Run these only from the package directory and only when the script exists:

```bash
uv run --group test python scripts/check_imports.py path/to/file.py
bash scripts/lint_imports.sh
uv run --group test python scripts/check_version.py
```

If a Makefile wraps the script, prefer the Makefile target.

## Pytest Selection Rules

Prefer tests under `tests/unit_tests/` for default local verification. Treat these as safe if they do not use provider credentials, network, service fixtures, or large optional dependencies.

Be cautious with:

- `tests/integration_tests/`: usually credentialed, service-backed, cassette-backed, or optional-dependency-heavy.
- `@pytest.mark.scheduled`: broader CI or scheduled-only intent.
- `@pytest.mark.vcr` or recording-related fixtures: cassette-sensitive; do not re-record by default.
- Tests requiring package downloads such as tokenizer/model corpora or NLP models.
- Local server/mock-server tests that open sockets, ports, subprocesses, or Docker services.

Use marker expressions to exclude risky categories when appropriate:

```bash
uv run --group test pytest tests/unit_tests -m "not scheduled"
uv run --group test pytest tests/unit_tests/path -k "not integration"
```

Do not add marker expressions that conflict with package `pyproject.toml` marker declarations under strict markers.

## No-Network Text Splitter Case

After changing a text splitter implementation, a safe first pass is:

```bash
cd libs/text-splitters
uv sync --group test
uv run --group test pytest tests/unit_tests/test_text_splitters.py
uv run --group test pytest tests/unit_tests/test_html_security.py
```

Skip integration tests involving `sentence_transformers`, spaCy model downloads, transformers, or remote resources unless the user requested them and the environment is prepared. Optional `requires` markers may skip missing parser packages such as `bs4` or `lxml`; report expected skips rather than treating them as failures.

## Provider Package Case

After changing a provider package, safe native checks usually include unit tests and static checks only:

```bash
cd libs/partners/<provider>
uv sync --group test
uv run --group test pytest tests/unit_tests/path/to/test_file.py
uv run --group lint ruff check .
uv run --group typing mypy .
```

Skip integration tests unless credentials, network approval, and required services are available. If a provider package has standard tests, run `langchain_tests.unit_tests` subclasses locally and classify `langchain_tests.integration_tests` subclasses as credentialed/service-backed unless they use a deterministic fake backend.

## Validation Handoff

Always report:

- Package directory used.
- Exact commands run or proposed.
- Whether `uv sync` was run and which groups were installed.
- Number of passed, failed, skipped, xfailed, or deselected tests when pytest ran.
- Explicit skip reason for integration, network, credential, GPU, service, or snapshot-update checks.
- Missing tool blocker such as `uv` unavailable, without implying validation succeeded.
