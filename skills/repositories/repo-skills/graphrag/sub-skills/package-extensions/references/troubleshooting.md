# Package Extension Troubleshooting

## Unknown Factory Key

Symptoms:

- `ValueError` says a strategy, type, provider, writer, or processor is not registered.
- The error lists registered keys but not the custom key.

Checks:

- Import and execute the module that calls `register_*` before calling `create_*`.
- Confirm the config `type`, `store`, `writer`, or method string exactly matches the registered key.
- Register in the same Python process that creates the object.
- Avoid relying on notebook cell execution order; put registration in an importable module or startup hook.

## Duplicate Factory Key

Symptoms:

- A custom provider silently behaves like a different implementation.
- Built-in behavior changes after tests run.

Checks:

- GraphRAG factories replace existing keys on repeated registration.
- Use unique keys for custom providers.
- If intentionally overriding a built-in, isolate the process or restore the previous initializer after the test.

## Singleton Scope Misuse

Symptoms:

- State leaks across tests, users, or indexing runs.
- A client created for one namespace appears in another run.

Checks:

- Singleton cache keys include strategy and non-`None` init args.
- Use transient scope for mutable stores, caches, test doubles, queues, and captured calls.
- Use singleton only for shareable clients whose init args fully identify endpoint, namespace, credentials source, and schema.

## Dropped `None` Init Args

Symptoms:

- Initializer defaults are used even though config set a field to `None`.
- A custom provider cannot tell whether a field was omitted or explicitly set to `None`.

Checks:

- The shared factory removes all `None` values from `init_args` before calling the initializer.
- Use a non-`None` sentinel string/boolean or include the distinction inside a nested dict if the initializer must see it.
- Make initializer defaults match the desired GraphRAG behavior.

## Extra Config Fields

Symptoms:

- Custom fields disappear, raise validation errors, or arrive in unexpected kwargs.

Checks:

- Many GraphRAG config models allow extra fields and pass them through with `model_dump()` or `model_extra`.
- Confirm whether the specific config model permits extras.
- Add `**kwargs` to custom initializers when forward compatibility matters.
- For LLM completion/embedding providers, custom knobs commonly come from `ModelConfig.model_extra`.

## Azure, Cosmos, and LanceDB Failures

Symptoms:

- Credential errors, missing account/container/index, package import errors, or network timeouts.

Checks:

- Import cloud/database packages only inside selected provider code paths.
- Validate endpoint, account, database, container, index, and credential source before creating clients.
- Keep retries and timeouts bounded for agent-driven tests.
- For Cosmos table providers, prefer passing an `AzureCosmosStorage` object so shared connection details can be inherited.
- Fall back to memory/file/mock providers when the task does not require live service verification.

## Optional Package Failures

Symptoms:

- `ImportError` or data/model lookup failures for pyarrow, MarkItDown, NLTK, spaCy, graspologic, LiteLLM, tiktoken, or Jinja.

Checks:

- pyarrow is needed for Parquet-backed paths.
- MarkItDown and format-specific dependencies are needed for converted document inputs.
- NLTK or spaCy data/models may need installation before sentence or NLP extraction paths.
- graspologic-style graph algorithms are optional; use deterministic pandas graph helpers for offline checks.
- LiteLLM/tiktoken dependencies depend on selected model/provider and tokenizer config.

## Vector Filter Mismatches

Symptoms:

- Search returns too many/few results.
- Backend rejects a compiled filter.
- Date filters do not match expected rows.

Checks:

- `FilterExpr` supports `eq`, `ne`, `gt`, `gte`, `lt`, `lte`, `contains`, `startswith`, `endswith`, `in`, `not_in`, and `exists`.
- Test filters in memory with `filters.evaluate(document)` before compiling to a backend query language.
- Honor `select` and `include_vectors` in custom search results.
- Declare custom date fields as `fields={"published_at": "date"}` so the base `VectorStore` expands `published_at_year`, `published_at_month`, and related components.
- Call `_prepare_document()` before insert and `_prepare_update()` before update.

## Timestamp Explosion Errors

Symptoms:

- `datetime.fromisoformat` fails.
- Filterable date component fields are missing.

Checks:

- Provide ISO 8601 strings for `create_date`, `update_date`, and custom date fields.
- Call the base preparation helpers in custom vector stores.
- If a backend requires a different date format, normalize before constructing `VectorStoreDocument` or provide a custom `timestamp_exploder`.

## Input Reader Finds No Files

Symptoms:

- Reader logs that no files match storage.
- Iteration yields no documents.

Checks:

- `InputReader` compiles `file_pattern` as a regex and applies it to storage keys.
- Ensure `storage.find()` returns keys that match the regex, not absolute local paths unless that is the storage key convention.
- Test the pattern with a minimal in-memory storage.

## Workflow Pipeline Key Errors

Symptoms:

- `PipelineFactory.create_pipeline` fails while building a `Pipeline`.

Checks:

- Register every workflow name used by the selected pipeline method.
- If `config.workflows` is set, it overrides registered method defaults.
- Keep custom method names distinct from standard, fast, and update methods unless intentionally replacing behavior.

## Graph Helper Surprises

Symptoms:

- Degree counts differ from directed graph expectations.
- Stable LCC changes case, spacing, or HTML entities.

Checks:

- `compute_degree` treats reversed pairs as the same undirected edge.
- `stable_lcc` uppercases, strips whitespace, unescapes HTML, stabilizes edge direction, deduplicates reversed edges, and sorts rows.
- Use these helpers for deterministic validation, not for preserving original casing or directed edge order.
