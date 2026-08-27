# Repository Map

## Primary Packages

| Package directory | Distribution | Import roots | Use for |
| --- | --- | --- | --- |
| `libs/core` | `langchain-core` | `langchain_core` | Stable primitives, schemas, interfaces, serialization, callbacks, runnables, messages, tools, vector stores, language model base classes. |
| `libs/langchain_v1` | `langchain` | `langchain` | Active v1 agent/application APIs, `init_chat_model`, `create_agent`, middleware, tools, embeddings. |
| `libs/langchain` | `langchain-classic` | `langchain_classic` | Legacy chains, retrievers, memory, loaders, classic agents, compatibility fixes, migration support. |
| `libs/text-splitters` | `langchain-text-splitters` | `langchain_text_splitters` | Text and document chunking, splitter optional integrations. |
| `libs/partners/<provider>` | `langchain-<provider>` | `langchain_<provider>` | Provider-specific clients, chat/LLM/embedding/vector-store integrations, credentials and service-specific tests. |
| `libs/standard-tests` | `langchain-tests` | `langchain_tests` | Shared conformance tests for integrations and pytest plugin behavior. |
| `libs/model-profiles` | internal tooling | `langchain_model_profiles` | `langchain-profiles` CLI, profile generation, provider capability data. |

## Ownership Rules

- Shared protocols or base classes belong in `langchain-core`; provider-specific behavior belongs in the provider package.
- New app-level agent behavior belongs in `libs/langchain_v1`, not `langchain-classic`.
- Classic changes should be maintenance, compatibility, or migration-oriented unless the user explicitly requests legacy work.
- Standard test abstractions belong in `libs/standard-tests`; individual provider assertions belong in the partner package.
- Model capability data should be refreshed through the profile tooling and reviewed as generated data, not hand-edited as the first fix.

## Evidence Sources

This skill was derived from package metadata, root development instructions, package source roots, package tests, package scripts, and representative partner/model-profile workflows. It intentionally does not cover every provider implementation in exhaustive detail; use the integration patterns and then inspect the target package.
