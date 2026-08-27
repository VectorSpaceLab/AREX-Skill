---
name: langchain
description: "Work on the LangChain Python monorepo: package routing, core
  primitives, v1 agents and middleware, classic APIs, partner integrations,
  standard tests, model profiles, and safe validation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# LangChain Python Monorepo

Use this skill when a task targets the LangChain Python repository, its package-local development workflow, or one of its maintained Python packages.

## Start Here

1. Identify the package and workflow with [repository-map.md](references/repository-map.md).
2. Use the sub-skill that owns the change instead of scanning the whole monorepo.
3. Follow [development-commands.md](references/development-commands.md) for package-local `uv`, pytest, lint, type, import, and version checks.
4. Use [troubleshooting.md](references/troubleshooting.md) for environment, import, optional dependency, integration-test, and source-layout failures.
5. Check [repo-provenance.md](references/repo-provenance.md) when deciding whether this skill is stale relative to the current checkout.

## Route by Task

- Monorepo navigation, package metadata, validation commands, public API guardrails, PR conventions, and docs/model-reference rules: use [monorepo-development](sub-skills/monorepo-development/SKILL.md).
- `langchain-core` primitives such as runnables, messages, prompts, tools, documents, embeddings, vector stores, model interfaces, callbacks, parsers, serialization, and deprecation utilities: use [core-primitives](sub-skills/core-primitives/SKILL.md).
- Actively maintained `langchain` v1 APIs such as `init_chat_model`, `create_agent`, structured output, tools, middleware, embeddings, provider routing, and agent runtime customization: use [agents-and-middleware](sub-skills/agents-and-middleware/SKILL.md).
- `langchain-classic` chains, retrievers, document loaders/transformers, memory, indexes, classic agents, evaluation, and legacy maintenance or migration: use [classic-chains](sub-skills/classic-chains/SKILL.md).
- Partner packages under `libs/partners`, provider SDK dependencies, credentials, unit/integration test split, cassettes, vector-store services, and provider model profile data: use [integrations](sub-skills/integrations/SKILL.md).
- `langchain-tests`, native verification selection, pytest marker/snapshot safety, model-profile CLI internals, and safe test/profile command planning: use [testing-and-profiles](sub-skills/testing-and-profiles/SKILL.md).

## Package Boundaries

- `libs/core` publishes `langchain-core`, the stable abstraction layer used by other packages.
- `libs/langchain_v1` publishes `langchain`, the actively maintained high-level package.
- `libs/langchain` publishes `langchain-classic`, a legacy compatibility package; avoid new feature work there unless explicitly requested.
- `libs/text-splitters` publishes `langchain-text-splitters`, focused on chunking documents and text.
- `libs/partners/<provider>` publish maintained provider integrations such as OpenAI, Anthropic, Ollama, Qdrant, Chroma, DeepSeek, Fireworks, Groq, Hugging Face, MistralAI, Nomic, Perplexity, OpenRouter, xAI, and Exa.
- `libs/standard-tests` publishes `langchain-tests`, shared conformance tests for integrations.
- `libs/model-profiles` contains the model profile refresh CLI and provider profile tooling.

## Default Development Workflow

Run commands from the owning package directory unless a package reference says otherwise:

```bash
cd libs/<package>
uv sync --group test
uv run --group test pytest tests/unit_tests/path/to/test_file.py
make lint_package
make type
```

Use narrower commands first. Add `--group lint`, `--group typing`, `--group test_integration`, or `--all-groups` only when the package metadata and task require those dependencies. Do not use `pip`, `poetry`, `conda`, or ad-hoc virtual environments for normal LangChain development.

## Safety and Validation

- Preserve public function/class signatures, argument order, names, defaults, and exported symbols unless the user accepts a breaking change.
- Add deterministic unit tests for bug fixes and feature changes; avoid network, credentials, provider services, or long-running checks by default.
- Use integration tests only when explicitly requested and credentials/services are available.
- For provider model examples in docs, verify current generally available model IDs against provider docs before updating examples.
- Use bundled scripts only as local helpers; they are read-only smoke/inspection utilities and do not replace package test suites.

## Bundled References and Scripts

- [Repository map](references/repository-map.md) gives the capability-to-package map and sub-skill ownership.
- [Development commands](references/development-commands.md) gives command patterns and validation escalation rules.
- [Troubleshooting](references/troubleshooting.md) covers cross-cutting failures and recovery decisions.
- [Repo provenance](references/repo-provenance.md) records the source snapshot and evidence paths.
- [Skill health check](scripts/check_skill_links.py) validates generated skill links and common leakage patterns.
