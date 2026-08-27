# GraphRAG CLI Command Map

## Purpose

Use this reference to route GraphRAG command-line tasks to the correct sub-skill before reading deeper workflow guidance.

## Verified Commands

The public console script is `graphrag`. CLI help was verified for GraphRAG `3.1.0` and exposes these commands:

| Command | Use for | Owning sub-skill |
| --- | --- | --- |
| `graphrag init` | Create `.env`, `settings.yaml`, prompt files, and input directory for a new workspace. | `../sub-skills/configuration-data/` then `../sub-skills/indexing/` |
| `graphrag index` | Build a GraphRAG index from configured inputs. | `../sub-skills/indexing/` |
| `graphrag update` | Incrementally update an existing index with new/changed documents. | `../sub-skills/indexing/` |
| `graphrag prompt-tune` | Generate indexing prompt templates from a corpus. | `../sub-skills/prompt-tuning/` |
| `graphrag query` | Query a completed index with global, local, DRIFT, or basic search. | `../sub-skills/querying/` |

## Command Selection

- Use `init` before the first index in a workspace or after a version/config migration when the user wants current default templates.
- Use `index` for first full builds or rebuilt outputs.
- Use `update` only when previous output exists and the user wants incremental behavior.
- Use `prompt-tune` before indexing when default extraction/report prompts are underperforming for the domain, language, or entity vocabulary.
- Use `query` only after required output tables and vector stores exist for the chosen method.

## Safe Checks

These checks do not call hosted models:

```bash
graphrag --help
graphrag init --help
graphrag index --help
graphrag update --help
graphrag prompt-tune --help
graphrag query --help
```

Prefer the bundled validators in each sub-skill before running commands that may call LLMs, Azure services, LanceDB/Cosmos/Azure AI Search, or long indexing pipelines.
