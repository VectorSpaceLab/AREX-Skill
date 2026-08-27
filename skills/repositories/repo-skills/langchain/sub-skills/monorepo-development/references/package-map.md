# LangChain Package Map

LangChain is a Python monorepo with independently versioned packages under `libs/`. There is no root `pyproject.toml`; package metadata, lockfiles, dependency groups, Make targets, and tests are package-local.

## Core Package Directories

| Directory | Distribution | Import package | Current sampled version | Use for | Notes |
|---|---|---|---:|---|---|
| `libs/core` | `langchain-core` | `langchain_core` | `1.4.8` | Base abstractions, messages, runnables, tools, callbacks, load/serialization, shared schemas, deprecation/beta APIs. | Highest API-stability sensitivity; many packages depend on it. |
| `libs/langchain_v1` | `langchain` | `langchain` | `1.3.10` | Actively maintained high-level LangChain package, public agent/application APIs, package-level integrations with LangGraph. | Prefer this over classic for new LangChain package behavior. |
| `libs/langchain` | `langchain-classic` | `langchain_classic` | `1.0.8` | Legacy/classic APIs and compatibility fixes. | Do not add new features here unless specifically requested. |
| `libs/text-splitters` | `langchain-text-splitters` | `langchain_text_splitters` | `1.1.2` | Text splitter utilities and chunking behavior. | Depends on `langchain-core`; optional integration tests may need NLP/model packages. |
| `libs/standard-tests` | `langchain-tests` | `langchain_tests` | `1.1.9` | Standardized conformance tests used by integrations. | Changes can affect many provider packages; keep tests generic. |
| `libs/model-profiles` | `langchain-model-profiles` | `langchain_model_profiles` | `0.0.6` | CLI for refreshing model profile data in integration packages. | Provides `langchain-profiles` console script. |
| `libs/partners/<provider>` | `langchain-<provider>` | Usually `langchain_<provider>` | Provider-specific | Team-maintained third-party integrations. | Keep provider dependencies and tests isolated to the provider package. |

Versions above were sampled from package `pyproject.toml` files during skill generation; inspect current package metadata before relying on them.

## Package Boundary Rules

- Put reusable abstractions in `libs/core` only when they are truly cross-package primitives.
- Put active user-facing LangChain APIs in `libs/langchain_v1`, not `libs/langchain`, unless the task targets classic compatibility.
- Put provider SDK dependencies and provider-specific options in `libs/partners/<provider>`.
- Put common integration conformance behavior in `libs/standard-tests`; do not duplicate broad standard tests across each provider unless provider-specific assertions are needed.
- Put text splitting algorithms and splitter-specific optional dependencies in `libs/text-splitters`.
- Put model profile tooling in `libs/model-profiles`; generated profile data belongs in the owning integration package's data area.

## Dependency and Source Patterns

Each package generally has:

- `pyproject.toml` with `[project]`, `[dependency-groups]`, `[tool.uv.sources]`, `[tool.ruff]`, `[tool.mypy]`, and `[tool.pytest.ini_options]` sections.
- `uv.lock` for the package-local lockfile.
- `Makefile` with package-local targets such as `test`, `lint`, `format`, `type`, `check_imports`, and sometimes `check_version`.
- `tests/unit_tests/` for no-network unit tests and `tests/integration_tests/` for network/provider/service tests when present.
- `scripts/check_imports.py` in many packages to load Python files and catch import-time failures.
- `scripts/check_version.py` in packages that maintain separate version artifacts or snapshots.

Local editable sources use relative paths from the package directory. Examples include core and text splitters from top-level packages, and provider packages from `libs/partners/<provider>`. Do not rewrite these paths unless the package layout changes.

## Common Dependency Groups

- `test`: pytest and unit-test dependencies.
- `test_integration`: provider/service/network/VCR/heavy dependencies for integration tests.
- `lint`: ruff and sometimes lint-time package requirements.
- `typing`: mypy and type stubs.
- `dev`: notebooks or developer convenience dependencies when present.

Use only the groups required for the task. Avoid `--all-groups` when it would install large optional dependencies unnecessarily, but use it when the package Makefile expects it for full lint/type coverage.

## Choosing a Package Quickly

- User mentions `Runnable`, `BaseMessage`, `BaseTool`, callback handling, serialization, beta/deprecation decorators, or shared schemas: start in `libs/core`.
- User mentions `create_agent`, `init_chat_model`, agent middleware, or active `langchain` public APIs: start in `libs/langchain_v1`.
- User mentions classic chains, legacy APIs, or `langchain_classic`: start in `libs/langchain`.
- User mentions splitting documents, token splitters, recursive splitters, HTML/Markdown splitters: start in `libs/text-splitters`.
- User mentions provider SDK behavior, chat model adapters, embeddings, vector store wrappers, credentials, or VCR cassettes: start in `libs/partners/<provider>` and route deeper provider details to integrations guidance.
- User mentions conformance tests for integrations: start in `libs/standard-tests` and inspect provider usage before changing shared expectations.
- User mentions model profile refresh, context windows, capability flags, or `langchain-profiles`: start in `libs/model-profiles`.
