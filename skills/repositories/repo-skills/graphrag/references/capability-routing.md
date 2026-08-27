# Capability Routing

## Purpose

Use this reference when a user request mentions several GraphRAG concepts and you need to choose the first sub-skill to read.

## Routing Matrix

| User asks about | Start with | Then read |
| --- | --- | --- |
| Install/import smoke checks, `.env`, `settings.yaml`, model provider, auth, data source layout | `../sub-skills/configuration-data/` | `../sub-skills/indexing/` when ready to build |
| OpenAI vs Azure OpenAI, managed identity, model deployment fields, LiteLLM args | `../sub-skills/configuration-data/` | `../references/troubleshooting.md` for cross-cutting auth failures |
| CSV/text/JSON/JSONL/Parquet/MarkItDown input behavior | `../sub-skills/configuration-data/` | `../sub-skills/indexing/` for output workflows |
| `graphrag init`, `index`, `update`, standard/fast indexing, BYOG tables, output parquet validation | `../sub-skills/indexing/` | `../sub-skills/configuration-data/` for config fields |
| Global/local/DRIFT/basic search, streaming query, query table/vector prerequisites | `../sub-skills/querying/` | `../sub-skills/configuration-data/` for vector-store config |
| Domain/language/entity-type prompt generation, prompt output filenames, auto prompt tuning | `../sub-skills/prompt-tuning/` | `../sub-skills/indexing/` after prompts are generated |
| Custom cache/storage/input/vector/LLM/chunker implementations or factory registration | `../sub-skills/package-extensions/` | `../sub-skills/configuration-data/` if exposing the extension through YAML |
| Graph helper behavior, connected components, degree, stable LCC, vector filters, timestamps | `../sub-skills/package-extensions/` | `../sub-skills/indexing/` if used inside a pipeline |

## Deliberate Exclusions

- The web demo app is not part of this runtime skill.
- Release scripts, docs build scripts, spellcheck, semver checks, and workspace dependency update scripts are not user-facing GraphRAG operation guidance.
- Original notebooks and tests are verification evidence, not runtime dependencies. The sub-skills distill their workflows into bundled references and safe scripts.
- Live Azure/OpenAI/storage/vector service calls require explicit credentials and user intent; default validation scripts are offline or guarded.
