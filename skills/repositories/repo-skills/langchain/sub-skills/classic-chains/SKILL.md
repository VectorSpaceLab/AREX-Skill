---
name: classic-chains
description: "Maintain and migrate langchain-classic legacy chains, retrievers,
  document loaders, memory, indexes, classic agents, evaluation, and callbacks.
  Use for compatibility fixes in libs/langchain-style classic APIs; route new v1
  agent work elsewhere."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Classic Chains

## When to Use

Use this sub-skill when the task is about `langchain-classic` legacy workflows: classic `Chain` subclasses, retrieval QA, conversational retrieval, document loaders and transformers, memory classes, indexes, classic agents, evaluation chains, callbacks, or compatibility-preserving maintenance.

Do not use this sub-skill for new v1 agent APIs, middleware, or graph/checkpoint design; route those to `../agents-and-middleware/SKILL.md`. For shared primitives such as `Document`, `BaseRetriever`, runnables, callbacks interfaces, messages, prompts, or vector store base contracts, route to `../core-primitives/SKILL.md`.

## Legacy Policy

`langchain-classic` is the legacy package. Prefer maintenance, bug fixes, import compatibility, deprecation cleanup, and migration guidance over adding new classic-only features. Preserve public signatures and behavior unless the user explicitly asks for migration and the replacement is validated.

## Reference Map

- Read [references/legacy-api-map.md](references/legacy-api-map.md) to identify classic modules, import ownership, optional community/provider boundaries, and sibling routing.
- Read [references/maintenance-workflows.md](references/maintenance-workflows.md) for compatibility-safe edit workflows, local validation commands, and skip conditions.
- Read [references/troubleshooting.md](references/troubleshooting.md) for deprecated imports, optional dependency errors, chain key mismatches, retriever/document-loader failures, and signature preservation.
- Use [scripts/classic_import_smoke.py](scripts/classic_import_smoke.py) for a read-only installed-package import smoke check after changing import surfaces or compatibility routing.

## Practical Workflow

1. Classify the request as maintenance, compatibility, migration, or new feature. Decline or reroute new classic-only feature work unless it is needed for compatibility.
2. Locate the affected classic area: chains, agents, retrievers, document loaders/transformers, memory, indexes, evaluation, callbacks, or schema compatibility.
3. Check whether the symbol is owned by `langchain_classic`, dynamically re-exported from `langchain_community`, or shared from `langchain_core`.
4. Preserve public constructor and method signatures. Add keyword-only parameters only when unavoidable, and cover behavior with deterministic unit tests.
5. Prefer package-local validation from the classic package directory, for example `uv run --group test pytest tests/unit_tests/chains/test_conversation_retrieval.py`, when `uv` and dependencies are available.
6. If the task is migration-oriented, produce v1/core-equivalent code paths while preserving behavior with tests around inputs, outputs, memory variables, callbacks, and returned documents.

## Validation Signals

- Unit tests pass for the nearest `tests/unit_tests/...` file or directory.
- Import smoke checks pass for touched public modules in an installed package.
- Deprecation warnings remain intentional and point users toward the modern package or API.
- Chain `input_keys`, `output_keys`, memory variables, callback propagation, and async/sync behavior remain backward compatible.

## Skip Conditions

Skip network-heavy integration tests, provider API calls, vector database services, browser automation, and credential-dependent loaders unless the user explicitly supplies safe credentials and asks for those checks. If `uv` is unavailable, record that package-local tests were skipped and rely on static inspection plus the safe smoke script when a usable Python interpreter already has the packages installed.
