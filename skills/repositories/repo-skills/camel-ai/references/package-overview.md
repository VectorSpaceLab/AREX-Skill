# CAMEL-AI Package Overview

CAMEL-AI is a Python framework for building communicative and multi-agent systems. The package distribution is `camel-ai`, the import root is `camel`, and the inspected source version was `0.2.91a4`.

## Major User-Facing Surfaces

| Surface | Main modules | Skill owner |
| --- | --- | --- |
| Agents, messages, tasks, societies, workforce | `camel.agents`, `camel.messages`, `camel.tasks`, `camel.societies`, `camel.terminators` | `agents-and-societies` |
| Model providers and config | `camel.models`, `camel.configs`, `camel.types`, `camel.schemas` | `models-and-configuration` |
| Tools, runtimes, interpreters, services | `camel.toolkits`, `camel.runtimes`, `camel.interpreters`, `camel.services` | `tools-runtimes-and-services` |
| Memory, RAG, storage, loaders, datasets | `camel.memories`, `camel.retrievers`, `camel.embeddings`, `camel.storages`, `camel.loaders`, `camel.datahubs`, `camel.datasets` | `memory-rag-and-data` |
| Data generation, benchmarks, verifiers, environments | `camel.datagen`, `camel.data_collectors`, `camel.benchmarks`, `camel.verifiers`, `camel.extractors`, `camel.environments` | `datagen-evaluation-and-benchmarks` |

## Optional Extras Strategy

Use the smallest extra set that matches the active workflow:

- `model_platforms`: additional provider SDKs for cloud/local model backends.
- `huggingface`: transformer/diffusion/dataset workflows and HF-backed model/data surfaces.
- `rag`, `storage`, `document_tools`: retrieval, vector stores, document loaders, graph/object stores, and document processing.
- `web_tools`, `communication_tools`, `data_tools`, `research_tools`, `media_tools`, `dev_tools`: toolkit families and optional integrations.
- `all`: broad feature install; reserve for interactive development or fully provisioned environments, not default CI smoke checks.

## Support Modules

CAMEL also exposes prompts, personas, caches, parsers, responses, configs, schemas, and utility modules. Route them through the nearest workflow owner:

- Prompt templates, role/persona generation, and response formatting usually support `agents-and-societies`.
- Provider configs and schema converters usually support `models-and-configuration`.
- Caches and utilities are cross-cutting; inspect the specific module and owner reference before modifying behavior.
