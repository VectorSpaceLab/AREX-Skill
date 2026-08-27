# Maintenance Workflows

## Before Editing

1. Confirm the request is appropriate for `langchain-classic`: legacy bug fix, compatibility repair, deprecation cleanup, import preservation, or migration support.
2. Locate the nearest package area and tests. Typical source roots are `langchain_classic/chains`, `agents`, `retrievers`, `document_loaders`, `document_transformers`, `memory`, `indexes`, `evaluation`, and `callbacks` inside the classic package.
3. Check public exposure through package `__init__.py`, `__all__`, dynamic `create_importer` mappings, or tests named `test_imports.py` / `test_public_api.py`.
4. Inspect the current unit test pattern before adding coverage. Mirror the package test layout, such as `tests/unit_tests/chains`, `tests/unit_tests/agents`, `tests/unit_tests/retrievers`, `tests/unit_tests/document_loaders`, `tests/unit_tests/memory`, `tests/unit_tests/schema`, and `tests/unit_tests/evaluation`.

## Compatibility-Safe Patch Loop

Use this loop for classic bug fixes:

1. Reproduce the issue with the smallest deterministic unit test. Prefer fake LLMs, fake retrievers, in-memory stores, and local `Document` objects over real providers or services.
2. Patch the root cause while preserving public signatures, default values, positional argument behavior, and return shape.
3. Keep deprecation decorators and dynamic import lookups intact unless the task is specifically about correcting them.
4. Validate sync and async paths when both exist. Classic chains and retrievers often implement `_call`/`_acall`, `_get_docs`/`_aget_docs`, or sync/async memory methods in parallel.
5. Check callback propagation when the affected code accepts callback managers or passes child callbacks into nested chains.
6. Run the nearest unit test target if dependencies are available.

## Commands

Run commands from the `libs/langchain` package directory when working in the monorepo. Use `uv`; do not use `pip`, `poetry`, or `conda` directly for LangChain development.

Representative commands:

```bash
uv sync --group test
uv run --group test pytest tests/unit_tests/chains/test_conversation_retrieval.py
uv run --group test pytest tests/unit_tests/chains tests/unit_tests/memory
uv run --group test pytest tests/unit_tests/retrievers/test_multi_vector.py
uv run --group test pytest tests/unit_tests/document_loaders/test_imports.py
uv run --group test pytest tests/unit_tests/agents/test_public_api.py
uv run --group test pytest tests/unit_tests/evaluation
uv run --group lint ruff check langchain_classic tests/unit_tests
```

Use narrower targets first, then broaden only when the touched code is shared. If `uv` is not available, do not claim tests ran; record that validation was skipped and use static review plus the bundled smoke script when possible.

## Import Compatibility Workflow

Use this when old import paths fail or deprecation messages confuse users:

1. Identify the legacy import path the user used.
2. Check whether the symbol is implemented under `langchain_classic` or forwarded through a dynamic lookup to `langchain_community` or another package.
3. For local symbols, preserve the old import path and add or update import tests.
4. For forwarded symbols, keep the classic mapping small and explicit. Do not copy provider/community implementations into classic.
5. Make missing optional dependency messages name the package or extra needed by the symbol.
6. Run a targeted import smoke check such as:

```bash
python scripts/classic_import_smoke.py
python scripts/classic_import_smoke.py --include-optional
```

The optional mode is expected to report skipped or failed optional imports in environments without community/provider packages; use it to diagnose, not as a hard gate unless those dependencies are installed.

## Conversational Retrieval Bug Workflow

Use this for issues in `ConversationalRetrievalChain` and related retrieval QA chains:

1. Verify inputs: `question` and `chat_history` are present and shaped as expected.
2. Verify generated question behavior: empty chat history should bypass the question generator; non-empty history should pass `question`, `chat_history`, and child callbacks.
3. Verify retriever behavior: `_get_docs` / `_aget_docs` should accept run managers where supported and return `list[Document]`.
4. Verify combine-docs behavior: downstream chains receive `input_documents`, callbacks, and the correct `question` depending on `rephrase_question`.
5. Verify outputs: default `answer`, optional `source_documents`, optional `generated_question`, and `response_if_no_docs_found` behavior.
6. Add tests around exact input and output keys rather than only checking final text.

## Migration-Aware Workflow

Use this when a user asks to move classic usage to v1/core equivalents:

1. Preserve the old behavior in a unit test or compact before/after assertion: inputs, outputs, memory state, retrieved documents, and callback side effects.
2. Identify which parts are truly classic and which are shared primitives from core.
3. Replace legacy agent construction with v1 agent APIs only when the user asked for migration; otherwise route new agent design to `../agents-and-middleware/SKILL.md`.
4. Replace classic memory in agent workflows with v1 checkpointing or store-backed memory where appropriate.
5. Preserve prompt variables and chain output keys, or provide a compatibility adapter if callers depend on old key names.
6. Document any intentional behavior changes clearly in the response or migration note.

## Validation and Skip Conditions

Good validation signals:

- Targeted unit tests pass for the touched area.
- Import smoke checks pass for required public paths.
- Deprecated import warnings remain intentional and actionable.
- Chain key assertions cover both happy path and mismatch failures.
- Optional dependency paths fail with clear install guidance rather than cryptic `ImportError` / `ModuleNotFoundError`.

Skip or defer:

- Network/provider calls without credentials.
- Vectorstore service integration tests that require external databases.
- Document loaders requiring unavailable local binaries or external services.
- Full package test suites when a targeted deterministic test proves the compatibility fix and broader runs are too slow for the task.
- Any command requiring `uv` when `uv` is unavailable in the host; state the skip explicitly.
