---
name: integrations
description: "Work on LangChain partner integration packages under libs/partners
  and provider model-profile data: package metadata, provider clients,
  chat/LLM/embedding/vector store classes, credentials, tests, cassettes,
  optional dependencies, and profile refresh workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Integrations

Use this sub-skill for practical work on LangChain-maintained partner packages and provider model-profile data. It covers provider-specific packages such as OpenAI, Anthropic, Ollama, Qdrant, Chroma, DeepSeek, Fireworks, Groq, Hugging Face, MistralAI, Nomic, Perplexity, OpenRouter, xAI, and Exa.

## When to Use

- The user asks to add, change, or debug a provider package under `libs/partners/<provider>`.
- The work touches provider chat models, LLMs, embeddings, vector stores, retrievers, tools, provider clients, middleware, output parsers, optional dependencies, credentials, or environment-variable handling.
- The user asks about package-local `pyproject.toml`, extras/dependency groups, import/version scripts, provider-specific unit or integration tests, VCR/cassette isolation, or model-profile refresh for provider data directories.
- The user needs safe validation that avoids network calls by default and escalates only when credentials, services, and permission are available.

## Route Elsewhere

- For package-agnostic `langchain-core` primitives, use `../core-primitives/SKILL.md`.
- For high-level `langchain` v1 agent construction, middleware routing, or `init_chat_model` behavior outside a provider package, use `../agents-and-middleware/SKILL.md`.
- For monorepo-wide package metadata, CI labels, release wiring, contributor conventions, or root development workflow, use `../monorepo-development/SKILL.md`.
- For implementing shared standard-test suites or model-profile CLI internals, route to `../testing-and-profiles/SKILL.md` when that sibling is present; this sub-skill only covers partner-side usage and provider data refresh.

## Reference Map

- Start with [references/provider-patterns.md](references/provider-patterns.md) for partner package layout, representative public classes, dependency patterns, source/test locations, edit workflows, and validation signals.
- Use [references/credentials-and-testing.md](references/credentials-and-testing.md) for API keys, local service checks, no-network unit tests, integration-test skip conditions, VCR cassette handling, and OpenAI Codex cassette safety.
- Use [references/model-profiles.md](references/model-profiles.md) for provider profile data directories, `langchain-profiles refresh`, augmentation files, generated profile diffs, and profile drift review.
- Use [references/troubleshooting.md](references/troubleshooting.md) for missing optional SDKs, credential failures, cassette isolation, model-profile drift, vector store service availability, and provider response/tool-call shape mismatches.
- Run [scripts/partner_package_check.py](scripts/partner_package_check.py) for a read-only metadata/layout check of a partner package when a Python interpreter is available.

## Fast Workflow

1. Identify the provider package, then work from its package directory: `libs/partners/<provider>`.
2. Inspect `pyproject.toml`, the `langchain_<provider>/` package root, `tests/unit_tests/`, `tests/integration_tests/`, and package-local `scripts/` before editing.
3. Keep provider-specific behavior in the partner package. Shared interfaces, message schemas, callbacks, base vector-store contracts, and standard-test framework changes belong to sibling skills.
4. Add deterministic unit tests for new behavior. Network-backed tests must be opt-in, credential-gated, and isolated from default no-network unit test runs.
5. Validate narrowly first with package-local `uv` commands when `uv` is available; do not use `pip`, `poetry`, `conda`, or ad-hoc virtual environments for this monorepo.

## Safe Validation

From a partner package directory, prefer targeted checks such as:

```bash
uv run --group test pytest tests/unit_tests/test_imports.py
uv run --group test pytest tests/unit_tests/test_chat_models.py
uv run --group test pytest tests/unit_tests/test_embeddings.py
uv run --group test pytest tests/unit_tests/test_vectorstores.py
uv run --group lint python scripts/check_imports.py $(find langchain_* -name '*.py')
uv run python scripts/check_version.py
```

Adjust test filenames to the package. Some packages use `make test`, `make check_imports`, `make check_version`, `make lint_package`, or `make type`; run these from the package directory only after confirming the package Makefile supports them. Skip network-heavy integration tests unless the user explicitly provides credentials or a local service and asks for those checks.

For a safe metadata/layout check that does not import provider SDKs or contact services:

```bash
python skills/langchain/sub-skills/integrations/scripts/partner_package_check.py libs/partners/openai
```

## Guardrails

- Preserve public provider class signatures and exported names unless the user explicitly accepts a breaking change.
- Do not add a provider SDK dependency to an unrelated package; partner SDKs belong in that partner package's metadata.
- Do not run credentialed examples, cassette recording, vector database services, or live provider calls without explicit user permission.
- Do not manually edit generated `_profiles.py` as the primary fix for profile drift; refresh through the model-profile workflow and review the generated diff.
- Do not link runtime instructions to source checkout docs, examples, or scripts; use the bundled references and scripts in this sub-skill.
