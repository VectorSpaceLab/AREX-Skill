# Core Primitive Workflows

These workflows assume work in the LangChain monorepo and use package-local commands. They are guidance for future agents; skip commands that require unavailable tooling and record the skip.

## Environment and Command Rules

- Use `uv` for LangChain dependency and test operations. Do not use `pip`, `poetry`, or `conda` directly for this repo.
- Work from `libs/core` for core package commands because the repo has no root `pyproject.toml`.
- Install only when needed and explicit: `uv sync --group test` or `uv sync --all-groups` from `libs/core`.
- If `uv` is unavailable, skip package test commands and run only checks available in the host, such as script syntax compilation or static file inspection.
- Unit tests are no-network by default and live under `libs/core/tests/unit_tests`.

## Fast Smoke Check

Use this after dependency or import-surface edits when an environment already has `langchain-core` importable:

```bash
python skills/langchain/sub-skills/core-primitives/scripts/core_import_smoke.py
```

Expected signal: `OK core_import_smoke` and a JSON summary of sampled behavior. Skip if `python` cannot import `langchain_core`; do not install dependencies with non-`uv` tools just to run it.

## Runnable Changes

Use for `Runnable`, LCEL composition, config propagation, async/batch/streaming, retry/fallback, event streaming, or schema issues.

1. Inspect the public import from `langchain_core.runnables` before using deeper modules.
2. Preserve sync, async, batch, and streaming semantics. If implementing a custom runnable, define `invoke`; override `ainvoke`, `batch`, `abatch`, `stream`, or `astream` only for real native behavior.
3. Pass `RunnableConfig` through nested calls using existing helpers such as `ensure_config`, `patch_config`, and executor helpers.
4. Add or adjust focused tests near `libs/core/tests/unit_tests/runnables`.
5. Prefer targeted validation:

```bash
cd libs/core
uv run --group test pytest tests/unit_tests/runnables/test_runnable.py
```

Use a narrower `-k` expression when only one behavior changed. Also consider event/config/fallback tests when touched.

## Message and Content-Block Changes

Use for `BaseMessage`, content blocks, tool calls, chunk merging, OpenAI conversion helpers, serialization dicts, or provider-normalization edge cases.

1. Decide whether data is a chat content block or a retrieval `Document`; do not mix the two abstractions.
2. Preserve provider-agnostic block fields and store provider-specific details in `extras` or `NonStandardContentBlock` unless a standard block exists.
3. Ensure conversion utilities do not mutate caller-provided messages unless the API explicitly says they do.
4. For provider translation, test both normalized content blocks and the provider-shaped output.
5. Run focused tests when possible:

```bash
cd libs/core
uv run --group test pytest tests/unit_tests/messages
uv run --group test pytest tests/unit_tests/messages/block_translators
```

Skip provider-network tests; this layer should be unit-testable without credentials.

## Tool Schema Changes

Use for `@tool`, `BaseTool`, `StructuredTool`, runnable-to-tool conversion, args schemas, tool messages, and docstring parsing.

1. Keep tool functions annotated; schema inference depends on type hints.
2. If using `parse_docstring=True`, keep Google-style `Args:` entries synchronized with function parameters.
3. Validate explicit `args_schema` annotations with Pydantic v2, and preserve existing v1 compatibility paths where already supported.
4. Test invalid docstrings, missing descriptions, injected args, and `response_format` behavior when relevant.
5. Run the closest unit tests. In this repository, tool tests may be package-level rather than under a `tools` subdirectory, so discover first:

```bash
cd libs/core
rg -n "BaseTool|StructuredTool|@tool|create_schema_from_function|convert_runnable_to_tool" tests/unit_tests
uv run --group test pytest tests/unit_tests/test_tools.py
```

If the discovered file differs, run that specific file instead.

## Prompt and Output Parser Changes

Use for prompt schemas, formatting validation, output parser runnable behavior, parser async wrappers, and parser deprecations.

1. For prompt templates, preserve reserved variable validation for `stop`, missing-variable messages, partial-variable overlap checks, and input schema generation.
2. For parsers, preserve `invoke` and `ainvoke` behavior over both strings and messages.
3. Add tests near prompt or output parser unit tests.
4. Validate targeted files:

```bash
cd libs/core
uv run --group test pytest tests/unit_tests/output_parsers
rg -n "PromptTemplate|ChatPromptTemplate|BasePromptTemplate" tests/unit_tests
```

Run the discovered prompt test file if prompt behavior changed.

## Documents, Embeddings, and Vector Stores

Use for retrieval data primitives, embedding interfaces, vector store base methods, and local vector store behavior.

1. Keep `Document`/`Blob` for retrieval and data-processing content; use message content blocks for LLM chat multimodality.
2. For `Embeddings`, ensure sync methods remain abstract and async methods either use executor defaults or native async implementations.
3. For `VectorStore`, preserve metadata/id count validation, get-by-id semantics, async wrappers, and retriever conversion behavior.
4. Prefer `InMemoryVectorStore` and fake embeddings for no-network tests.
5. Validate:

```bash
cd libs/core
uv run --group test pytest tests/unit_tests/vectorstores
```

## Chat/LLM Interface Changes

Use for `BaseChatModel`, `BaseLLM`, model profiles, fake models, structured output, tool binding, generation/result shaping, and callback integration.

1. Avoid provider credentials and network calls; use fake chat/LLM classes for unit coverage.
2. Preserve message normalization, streaming chunk aggregation, callback events, tracing metadata, and model profile warnings.
3. When touching `bind_tools` or structured output behavior, also check tool schema expectations.
4. Validate:

```bash
cd libs/core
uv run --group test pytest tests/unit_tests/language_models
```

Use narrower subdirectories/files for large test suites.

## Callback, Tracing, Serialization, and Deprecation Changes

Use for callback managers, tracers, `dumpd`/`dumps`/`loads`, `Serializable`, `asdict`, deprecated methods, and compatibility shims.

1. Preserve parent/child run propagation, tags, metadata, and deterministic test behavior.
2. For serializable classes, opt in explicitly with `is_lc_serializable` and keep `get_lc_namespace` stable unless a migration mapping is also maintained.
3. Use `lc_secrets` for secret redaction and `lc_attributes` only for constructor-compatible values.
4. For deprecations, use `deprecated` or `warn_deprecated`, include since/removal/alternative when known, and keep tests asserting warning behavior.
5. Validate the nearest tests plus import smoke. Examples:

```bash
cd libs/core
uv run --group test pytest tests/unit_tests/runnables/test_runnable.py -k "deprecated or serialization or dumps"
uv run --group test pytest tests/unit_tests/output_parsers/test_base_parsers.py
```

## Skip Conditions

Skip and record why when:

- `uv` is unavailable in the host.
- Dependencies have not been synced and installing them would require non-`uv` tooling.
- A test needs provider credentials, network access, or a service backend.
- The task is app-level agent orchestration or legacy chain behavior better handled by sibling sub-skills.
