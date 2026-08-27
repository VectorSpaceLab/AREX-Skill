# Repository Provenance

schema: `disco.repo-provenance.v1`

This skill was generated from the LangGraph monorepo evidence listed below.

## Source Snapshot

- VCS: Git
- Branch: `main`
- Commit: `711b31550286585b3793857b2a99c8dafd98b785`
- Exact tag: none detected
- Remote URL: public `https://github.com/langchain-ai/langgraph.git`
- Dirty state at generation: dirty because the generated `skills/` tree was untracked during creation.

## Package Versions Observed

- `langgraph`: `1.2.6`
- `langgraph-prebuilt`: `1.1.0`
- `langgraph-checkpoint`: `4.1.1`
- `langgraph-checkpoint-sqlite`: `3.1.0`
- `langgraph-checkpoint-postgres`: `3.1.0`
- `langgraph-cli`: `0.4.30`
- `langgraph-sdk`: `0.4.2`

## Evidence Paths

- `README.md`
- `libs/langgraph/README.md`
- `libs/langgraph/pyproject.toml`
- `libs/langgraph/langgraph/`
- `libs/langgraph/tests/`
- `libs/prebuilt/README.md`
- `libs/prebuilt/pyproject.toml`
- `libs/prebuilt/langgraph/prebuilt/`
- `libs/prebuilt/tests/`
- `libs/checkpoint/README.md`
- `libs/checkpoint/pyproject.toml`
- `libs/checkpoint/langgraph/checkpoint/`
- `libs/checkpoint/tests/`
- `libs/checkpoint-sqlite/README.md`
- `libs/checkpoint-sqlite/pyproject.toml`
- `libs/checkpoint-sqlite/langgraph/checkpoint/sqlite/`
- `libs/checkpoint-sqlite/tests/`
- `libs/checkpoint-postgres/README.md`
- `libs/checkpoint-postgres/pyproject.toml`
- `libs/checkpoint-postgres/langgraph/checkpoint/postgres/`
- `libs/checkpoint-postgres/tests/`
- `libs/cli/README.md`
- `libs/cli/pyproject.toml`
- `libs/cli/langgraph_cli/`
- `libs/cli/schemas/schema.json`
- `libs/cli/examples/`
- `libs/cli/tests/`
- `libs/sdk-py/README.md`
- `libs/sdk-py/pyproject.toml`
- `libs/sdk-py/langgraph_sdk/`
- `libs/sdk-py/tests/`
- `libs/sdk-js/README.md`
- `examples/README.md`
- `examples/`

## Refresh Guidance

Refresh this skill if any of these change materially:

- Public signatures in `langgraph.graph`, `langgraph.types`, `langgraph.prebuilt`, checkpoint savers, CLI commands/config schema, or SDK client factories.
- Version constraints, optional dependencies, or package split/merge behavior.
- CLI command names/options, `langgraph.json` schema, API server deployment behavior, or SDK streaming semantics.
- Checkpointer/store security recommendations, Postgres setup requirements, or serializer defaults.
