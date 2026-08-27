# Cross-Cutting Troubleshooting

## Install Or Import Failures

| Symptom | Likely cause | Next action |
| --- | --- | --- |
| `ModuleNotFoundError: llama_index.core` | Core package is not installed in the active Python | Install `llama-index-core` or `llama-index`, then run `scripts/inspect_llama_index_install.py --module llama_index.core` |
| `ModuleNotFoundError: llama_index.llms.openai` | Provider integration package is missing | Install the matching provider distribution and route to `sub-skills/integrations-and-storage/SKILL.md` |
| Core imports work but provider constructor fails | Missing API key, service dependency, optional extra, or incompatible provider package | Check provider env vars and package metadata before changing core code |
| `pip check` reports conflicts | Mixed incompatible `llama-index-*` versions or provider dependency conflicts | Align versions on the same core minor line and reinstall the smallest needed package set |

## API And Migration Confusion

- Prefer `Settings` over deprecated `ServiceContext` in new code.
- Core application code imports from `llama_index.core`; provider integrations usually import from `llama_index.<category>.<provider>`.
- Use `MockLLM` and `MockEmbedding` for deterministic local checks when no API keys should be required.
- For structured output failures, separate Pydantic schema validation from model/provider behavior.

## Data And RAG Failures

- No files loaded: check reader input paths, hidden/excluded files, extension filters, recursive mode, and encoding.
- Empty retrieval: verify nodes were indexed, embeddings exist, filters match metadata, and `similarity_top_k` is not too narrow.
- Persistence confusion: local `persist_dir` applies to in-memory/simple storage; many vector-store integrations persist in their own service and only need config to reconnect.
- Bad answers despite retrieval: inspect retrieved nodes before tuning prompts or changing LLMs.

## Agent And Workflow Failures

- Tools need short, unique names and descriptions that explain when to call them.
- A `QueryEngineTool` wraps an already-built query engine; build or debug the index/query engine in `indexing-and-querying` first.
- Handoff bugs usually come from overlapping agent descriptions or missing `can_handoff_to` routes.
- Streaming workflows require consuming emitted events/results, not only awaiting the final object.

## Monorepo Safety

- Run targeted tests for changed packages instead of broad monorepo test sweeps by default.
- Treat release, publish, version-bump, and credentialed docs sync scripts as unsafe unless explicitly requested.
- Use read-only package metadata scans before changing pyproject files or dependency groups.
