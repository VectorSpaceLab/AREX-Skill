---
name: maintainer-apis
description: "Maintain MetaGPT internal APIs for serialization, memory,
  experience pools, skill management, repository parsing, YAML config models,
  and focused diagnostics."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Maintainer APIs

Use this sub-skill when the user asks to fix or inspect MetaGPT internals: serialization/deserialization, `Message`/`Task` schema models, memory persistence, experience pools, skill management, repository symbol parsing, YAML config models, focused maintainer tests, or public API inventories.

## Route Here For

| User intent | Use this sub-skill for | Key reference |
| --- | --- | --- |
| "Fix serialization" or "deserialize a Role/Message/Team" | `BaseSerialization`, `SerializationMixin`, `Message.instruct_content`, polymorphic fields, save/load compatibility | [Serialization workflow](references/workflows.md#serialization-and-schema-maintenance) |
| "Debug memory/storage" | `Memory`, `LongTermMemory`, `MemoryStorage`, `BrainMemory`, `RoleZeroLongTermMemory`, RAG-backed persistence boundaries | [Memory workflow](references/workflows.md#memory-maintenance) |
| "Inspect exp_pool" or "update exp_cache" | `ExperienceManager`, `Experience`, serializers, scorers, context builders, perfect judges, config flags | [Experience pool workflow](references/workflows.md#experience-pool-maintenance) |
| "Update skill management" | `SkillManager`, Chroma-backed retrieval, skill add/delete/get behavior, optional dependency checks | [Skill manager workflow](references/workflows.md#skill-manager-and-repo-parser-updates) |
| "List public symbols" | Safe AST-based class/function inventory without importing provider/config-heavy modules | [Diagnostics workflow](references/workflows.md#public-symbol-inventory) |
| "Run focused maintainer tests" | Targeted pytest commands, ignored-test strategy, optional provider/RAG skips, collection-error handling | [Testing guide](references/testing.md) |

## First Moves

1. Classify the change as serialization/schema, memory, experience pool, skill manager, repo parser, config model, or diagnostics before editing.
2. Prefer direct model construction with explicit `Config`/`LLMConfig` values over `Config.default()` when a placeholder API key may be present.
3. Run a focused test file or directory; avoid the broad pytest suite unless the user explicitly wants coverage and optional dependencies are ready.
4. Use `scripts/list_public_symbols.py` for API inventories instead of the original shell helper; it parses Python AST and does not import MetaGPT modules.

## Runtime References

- [Workflows](references/workflows.md): focused maintainer workflows, commands, edit strategy, coverage/report guidance, and public-symbol diagnostics.
- [API Reference](references/api-reference.md): key classes/modules, config keys, serialization contracts, and common edit points.
- [Testing](references/testing.md): `pytest.ini` behavior, safe focused commands, optional/provider tests, fixtures, and skip decisions.
- [Troubleshooting](references/troubleshooting.md): Pydantic v2, placeholder config, pickle/json compatibility, memory/exp_pool storage, optional dependencies, and generated-file issues.

## Boundaries

- User-facing MetaGPT CLI, project generation, incremental updates, and recovery workflows belong in [`software-company`](../software-company/SKILL.md); return here only for serialization internals behind those workflows.
- Data Interpreter and RoleZero workflow behavior belongs in [`data-interpreter`](../data-interpreter/SKILL.md); return here for RoleZero memory internals or exp_pool serializer/context-builder maintenance.
- RAG, search, browser, vector stores, and tool registry usage belongs in [`rag-and-tools`](../rag-and-tools/SKILL.md); return here only when memory or exp_pool failures surface through those optional backends.
- Provider-specific API calls, browsers, Android devices, downloads, and long LLM runs are prerequisites or skips, not safe maintainer smoke tests.

Evidence provenance distilled from MetaGPT serialization, memory, exp_pool, management, repo parser, YAML config, pytest configuration, maintainer tests, and docs diagnostic scripts. Repo-relative paths in references are provenance/edit-point names for a MetaGPT checkout, not external runtime dependencies.
