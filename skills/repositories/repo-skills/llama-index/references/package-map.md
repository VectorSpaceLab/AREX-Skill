# LlamaIndex Package Map

## Package Split

- `llama-index`: starter distribution for common application use. It depends on `llama-index-core`, OpenAI LLM/embedding integrations, and `nltk` in this checkout’s metadata.
- `llama-index-core`: core framework distribution. It provides `llama_index.core` and the main abstractions for documents, indexes, retrievers, query engines, agents, workflows, prompts, storage, and callbacks.
- `llama-index-workflows`: installed as a core dependency and used by agent/workflow surfaces.
- `llama-index-integrations/*/*`: many provider packages such as LLMs, embeddings, readers, vector stores, retrievers, tools, postprocessors, graph stores, and callbacks.
- `llama-index-utils/*`: utility packages that support selected providers or platforms.
- `llama-dev`: monorepo maintenance CLI, not an application runtime dependency.

## Import Conventions

Core imports include `core` explicitly:

```python
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, Settings
from llama_index.core.agent.workflow import FunctionAgent, AgentWorkflow
```

Integration imports omit `core` and include the category/provider path after the matching distribution is installed:

```python
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
```

If `from llama_index.llms.openai import OpenAI` fails, installing or repairing `llama-index-core` alone is not enough; verify the provider package, for example `llama-index-llms-openai`.

## Version Alignment

- Keep integration packages compatible with the installed core minor line.
- Prefer installing core plus only needed integrations for production or constrained environments.
- Prefer the starter package when a quick default OpenAI-backed setup is acceptable.
- Avoid installing every integration in the monorepo; many packages require external services, credentials, compiled dependencies, or provider-specific constraints.

## Evidence Baseline

This skill was generated from LlamaIndex source metadata where root `llama-index` and `llama-index-core` were both version `0.14.22`, and live inspection verified `llama-index-core==0.14.22`.
