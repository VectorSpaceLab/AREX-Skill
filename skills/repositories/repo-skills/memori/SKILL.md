---
name: memori
description: "Routes Memori Python and TypeScript memory SDK workflows across
  cloud, BYODB, LLM registration, recall/search, CLI, and integrations."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Memori

Memori is a persistent-memory SDK for Python and TypeScript.
Use this repo skill when the request is about Memori Cloud, BYODB, LLM
registration, recall/search, embeddings, CLI operations, MCP integration, or
the Node/TypeScript SDK.

## Start here

- Read `references/package-overview.md` for the package map and install
  variants.
- Read `references/configuration.md` for environment variables and runtime
  defaults.
- Read `references/troubleshooting.md` when an install, import, backend, or
  workflow fails.
- Run `scripts/check_memori_install.py` for a safe package/import/config smoke.

## Route map

| If the user asks for... | Go to | What it owns |
| --- | --- | --- |
| Memori Cloud, `python -m memori`, quota, sign-up, MCP, or agent recall/summary/compaction | `sub-skills/cli-and-cloud/SKILL.md` | CLI, cloud API, MCP, and adjacent agent integrations |
| SQLite/Postgres/MySQL/TiDB/MongoDB/Oracle/CockroachDB/OceanBase BYODB setup or provisioning | `sub-skills/byodb-storage/SKILL.md` | Storage adapters, schema build, database recipes, and provisioning |
| `llm.register(...)`, OpenAI/Anthropic/Gemini/xAI, Agno, LangChain, or provider troubleshooting | `sub-skills/llm-integration/SKILL.md` | Python LLM client registration and wrapper guidance |
| attribution, sessions, recall, search, embeddings, TEI, native Rust core, or memory deletion | `sub-skills/memory-and-search/SKILL.md` | Memory lifecycle, retrieval, embeddings, and native runtime caveats |
| `@memorilabs/memori`, `MemoriRequestScope`, Node storage, or TypeScript CLI/native questions | `sub-skills/typescript-sdk/SKILL.md` | TypeScript SDK, request scopes, storage, and native binding notes |

## Public package facts

- Python distribution: `memori`
- Import root: `memori`
- TypeScript package: `@memorilabs/memori`
- Rust/native core is bundled behind the Python wheel and the Node package.
- Optional backend and provider extras are documented in the bundled
  references; do not install them unless the task needs them.

## Working rules

- Keep runtime guidance self-contained. Do not point future agents back to the
  source checkout for examples, docs, tests, or scripts.
- Use the nearest sub-skill for workflow depth. The root only routes and
  shares package-level facts.
- When a task spans multiple areas, start at the root, then combine the owning
  sub-skills instead of forcing one route to cover everything.
- If the request is just an install/import sanity check, run
  `scripts/check_memori_install.py` first.

## Minimal install check

```bash
pip install memori
python -m memori
python scripts/check_memori_install.py
```
