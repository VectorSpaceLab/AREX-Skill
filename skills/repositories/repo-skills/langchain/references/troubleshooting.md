# Cross-Cutting Troubleshooting

## `uv` or Dependencies Are Missing

- Symptom: `uv: command not found`, imports fail, or pytest cannot resolve dependencies.
- Recovery: install/use `uv` per LangChain development guidance, run commands from the owning package directory, and sync only the required dependency group. Do not repair this by invoking `pip`, `poetry`, `conda`, or an ad-hoc virtual environment in normal repo work.

## Wrong Package Directory

- Symptom: no root `pyproject.toml`, pytest cannot find package config, or Makefile targets are missing.
- Recovery: route to the package under `libs/`, then run package-local commands. Use `references/repository-map.md` or the monorepo-development sub-skill to choose the owner.

## Optional Dependency Errors

- Symptom: provider SDK, tokenizer, parser, vector database, or NLP package import fails.
- Recovery: identify whether the dependency belongs to a selected workflow. Install/sync only the relevant group or extra, and skip workflows tied to unselected providers or expensive optional integrations.

## Network, Credentials, or Services

- Symptom: provider tests fail with missing API keys, socket blocking, VCR cassette errors, or unavailable vector database services.
- Recovery: prefer mocked unit tests. Run integration tests only when credentials/services are intentionally provided. Record skipped native checks as skips, not passes.

## Public API Breakage

- Symptom: tests or examples fail because an exported name, argument, default, return type, or import path changed.
- Recovery: preserve signatures when possible; add keyword-only new parameters; update tests and docs; warn the user before likely breaking public interfaces.

## Classic vs V1 Confusion

- Symptom: a task mixes `langchain_classic` chains/retrievers with v1 `langchain.agents` or `langchain_core` primitives.
- Recovery: keep legacy compatibility changes in classic; use v1/core routes for new agent work; add migration notes rather than duplicating new features in classic.
