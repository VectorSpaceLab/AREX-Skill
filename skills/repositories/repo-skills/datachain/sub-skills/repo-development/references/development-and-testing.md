# Development and Testing

Use this reference when working inside a DataChain source checkout.

## Package and Environment

DataChain is a Python package with a `src/` layout and distribution name
`datachain`. The package metadata declares Python `>=3.10` and a console script:

```text
datachain = datachain.cli:main
```

Base dependencies include storage clients, pandas/pyarrow, SQLAlchemy, Pydantic,
LiteLLM, and Studio/client packages. Optional dependency groups are intentionally
separate:

| Extra | Purpose |
| --- | --- |
| `docs` | MkDocs documentation build. |
| `torch` | PyTorch dataset helpers and image/text conversion utilities. |
| `audio` | Audio file support dependencies. |
| `remote` | Remote/compression request extras. |
| `vector` | Vector/search dependencies such as `usearch`. |
| `hf` | Hugging Face datasets and audio/vision support. |
| `video` | Video decoding/processing dependencies. |
| `postgres` | PostgreSQL driver. |
| `zarr` | Zarr store support. |
| `tests` | Test dependencies and optional workflow extras. |
| `dev` | Docs/tests plus type/lint tooling. |
| `examples` | Example workflow dependencies, model/API packages. |

Install only the extra needed for the task. Do not treat a missing optional extra
as a base package failure unless base imports break.

## Nox Sessions

The repository uses `nox` with `uv|virtualenv` backends and reusable virtualenvs.
Key sessions:

| Session | Purpose | Typical command |
| --- | --- | --- |
| `tests` | Main pytest suite with coverage and xdist. | `nox -s tests -- tests/unit/test_cli_parsing.py -q` |
| `e2e` | End-to-end marked tests. | `nox -s e2e -- tests/test_cli_e2e.py -q` |
| `examples` | Example tests with `datachain[examples]`. | `nox -s examples -- tests/examples -q` |
| `lint` | pre-commit with dev/vector extras. | `nox -s lint` |
| `docs` | MkDocs build. | `nox -s docs` |
| `bench` | Benchmark suite. | `nox -s bench -- tests/benchmarks` |
| `build` | Build and twine check. | `nox -s build` |

For quick iteration, run direct pytest in an already-prepared development
environment before broad nox sessions.

## Test Layout

| Area | What it covers |
| --- | --- |
| `tests/unit/` | Unit tests for CLI parsing, config, query internals, schema conversion, clients, skills, package exports, optional imports. |
| `tests/unit/lib/` | DataChain library behavior: schema, files, UDFs, DataChain methods, conversion, model support, optional data types. |
| `tests/unit/sql/` | SQL expression and dialect behavior. |
| `tests/func/` | Functional behavior over local/cloud fixtures, storage, datasets, UDFs, exports, delta/retry, query workflows. |
| `tests/examples/` | Example workflows, often requiring optional extras. |
| `tests/benchmarks/` | Performance benchmarks; not a correctness default. |
| top-level `tests/test_*e2e.py` | CLI, Studio, query, job-management integration surfaces. |

Pytest markers include `e2e`, `examples`, `computer_vision`, `get_started`,
`llm_and_nlp`, `multimodal`, and `incremental_processing`. Default pytest opts
skip examples and benchmark execution.

## Focused Test Selection

Start with the file closest to the changed code:

| Changed area | First focused tests |
| --- | --- |
| `src/datachain/cli`, `src/datachain/studio.py`, `src/datachain/remote/studio.py` | `tests/unit/test_cli_parsing.py`, `tests/unit/test_cli_skill.py`, `tests/unit/test_cli_datasets.py`, selected top-level CLI/Studio e2e tests with mocks. |
| `src/datachain/lib/dc/datachain.py` | `tests/unit/lib/test_datachain.py`, `tests/func/test_datachain.py`, operation-specific tests such as merge/union/export. |
| `src/datachain/func`, `src/datachain/sql` | `tests/unit/test_func.py`, `tests/unit/sql/`, `tests/func/functions/`. |
| `src/datachain/lib/signal_schema.py`, `src/datachain/lib/convert` | `tests/unit/lib/test_signal_schema.py`, `tests/unit/lib/test_python_to_sql.py`, `tests/unit/lib/test_sql_to_python.py`, `tests/func/test_signal_schema.py`, export/read-back tests. |
| `src/datachain/lib/file.py`, `src/datachain/client`, `src/datachain/fs` | `tests/unit/lib/test_file.py`, `tests/unit/test_client*.py`, `tests/func/test_file.py`, storage functional tests when credentials/fixtures are available. |
| `src/datachain/llm` | `tests/unit/lib/test_llm.py`, `tests/func/test_llm.py` with fake providers; avoid real provider calls by default. |
| `src/datachain/skill` | `tests/unit/test_cli_skill.py`, `tests/unit/test_skill_knowledge_collect.py`, `tests/unit/test_skill_knowledge_snapshot.py`, `tests/unit/test_skill_jobs_scripts.py`. |
| Packaging/import metadata | `tests/unit/test_module_exports.py`, `tests/test_import_time.py`, `python -m pip check`. |

Use the bundled `scripts/select_tests.py` to print suggestions from changed path
names.

## Documentation and Comments

- Update docs when public API behavior, CLI flags, environment variables, or
  examples change.
- Public APIs should have docstrings; internal helpers usually should not unless
  they encode a non-obvious invariant.
- Comments should state durable facts about current behavior, not the story of a
  change. Avoid words like "previously", "now that", or "this PR".

## Definition of Done for Maintainer Changes

1. Focused tests reproduce the failure or cover the new behavior.
2. The fix is verified by focused tests plus the smallest broader nox session
   that exercises the affected integration surface.
3. Backend-sensitive claims have backend evidence or an explicit limitation.
4. Documentation and examples are updated when user-facing behavior changes.
5. No optional or credentialed workflow is silently treated as verified.
