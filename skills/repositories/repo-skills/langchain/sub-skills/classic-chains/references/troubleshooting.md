# Troubleshooting

## Deprecated Imports and Migration Confusion

Symptoms:

- User imports from `langchain_classic` and sees a deprecation warning.
- User imports old `langchain` or `langchain_classic` paths and asks why v1 examples differ.
- A classic symbol dynamically forwards to `langchain_community` but the modern package is not installed.

Actions:

1. Determine whether the task is maintenance of old behavior or migration to modern APIs.
2. Keep legacy imports working when they are part of the public classic surface.
3. Do not add new classic-only APIs for modern agent patterns. Route new v1 agent design to `../agents-and-middleware/SKILL.md`.
4. For shared primitives, update imports toward `langchain_core` and route design questions to `../core-primitives/SKILL.md`.
5. If a deprecation warning is expected, leave it in place and ensure the alternative is accurate.

Validation:

- Import tests cover the legacy path.
- Warning text points to a modern equivalent or owning package.
- Migration examples preserve inputs, outputs, and side effects that user code depends on.

## Optional Community or Provider Dependency Errors

Symptoms:

- `ModuleNotFoundError` for `langchain_community`, provider packages, vector database clients, parsers, or local document-processing libraries.
- Dynamic re-exported retrievers or document loaders fail at import or construction time.

Actions:

1. Identify whether the missing dependency is required by core classic or by an optional integration.
2. Keep base classic imports lightweight. Do not import optional provider packages at module import time unless the existing design already requires it.
3. Make errors actionable by naming the missing package or optional extra.
4. For provider/community implementation bugs, route to the owning package rather than copying code into classic.
5. Add unit tests with missing-dependency simulation only when adjacent tests already use that pattern.

Validation:

- Required classic imports pass without optional providers.
- Optional paths either work when dependencies are installed or fail with clear install guidance.
- No network or credential checks are required for a pure import fix.

## Chain Input and Output Key Mismatches

Symptoms:

- `ValueError` about missing prompt variables, overlapping keys, or multiple output keys.
- `KeyError` for `question`, `chat_history`, `input_documents`, `history`, or a custom `memory_key`.
- A chain returns `answer` but caller expects another output key, or source documents disappear.

Actions:

1. Inspect `input_keys`, `output_keys`, prompt `input_variables`, memory variables, and downstream chain expectations.
2. For `ConversationalRetrievalChain`, verify `question`, `chat_history`, `output_key`, `return_source_documents`, `return_generated_question`, `rephrase_question`, and `response_if_no_docs_found` behavior.
3. For memory-backed chains, align `memory_key`, `input_key`, and `output_key`; avoid collisions between prompt variables and memory variables.
4. For combine-document chains, ensure documents are passed as `input_documents` and metadata requirements in document prompts are satisfied.
5. Preserve legacy default keys unless the user explicitly asks for migration.

Validation:

- Tests assert exact input and output key sets.
- Tests cover custom key names when the bug involves customization.
- Both sync and async paths are covered if the chain implements both.

## Retriever, Vectorstore, and Document Loader Dependency Issues

Symptoms:

- A retriever returns the wrong document type or an empty list unexpectedly.
- Vectorstore-backed retrievers fail because a client package, local service, or docstore dependency is missing.
- Document loaders fail because a parser, file-format library, binary, or external service is unavailable.

Actions:

1. Confirm the expected retriever contract: query in, `list[Document]` out.
2. Use fake vectorstores, fake retrievers, `InMemoryStore`, and local `Document` objects for unit tests.
3. Keep optional integrations optional; do not add unconditional imports that make lightweight tests require external services.
4. For document loaders, separate import compatibility from actual file parsing or network loading.
5. Mark provider, vector database, browser, and credential-dependent checks as skipped unless explicitly configured.

Validation:

- Unit tests exercise local fake/in-memory paths.
- Optional dependency errors are clear and scoped to the optional feature.
- Returned objects are `Document` instances from the shared core contract.

## Preserving Backward-Compatible Signatures

Symptoms:

- Existing user code fails after a constructor, method, or class field changes.
- Tests fail because positional arguments, defaults, or pydantic field names changed.
- Deprecation decorators are removed or alternatives change unexpectedly.

Actions:

1. Treat public classic APIs as stable compatibility surfaces even when deprecated.
2. Check package exports, `__all__`, import tests, and adjacent usage before changing signatures.
3. Prefer internal helpers over public signature changes.
4. If a new option is unavoidable, make it keyword-only and default-preserving.
5. Keep aliases and dynamic import lookups unless removing them is the explicit task.

Validation:

- Existing public API tests continue to pass.
- Added tests demonstrate old call patterns still work.
- Deprecation warnings remain compatible with the intended release/removal path.

## Smoke Script Interpretation

Run `scripts/classic_import_smoke.py` in an environment where the target package is installed. The default mode checks required, lightweight imports only. `--include-optional` checks common optional re-export names and may fail or skip if community/provider dependencies are absent.

Use failures as triage:

- Required import failure: likely a package install, import cycle, or core compatibility issue.
- Optional import failure with missing dependency: expected unless that optional package should be installed for the task.
- Optional import failure after dependency is installed: inspect dynamic lookup mappings and owning integration package behavior.
