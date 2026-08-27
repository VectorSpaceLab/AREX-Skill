# Package Selection and Import Namespaces

## Package Split

LlamaIndex is intentionally split into a small core plus many provider packages.

- `llama-index` is the starter distribution. It depends on `llama-index-core` and a default OpenAI-oriented set, including OpenAI LLM and embedding integrations for the current 0.14.x line.
- `llama-index-core` provides framework APIs under `llama_index.core`, including `VectorStoreIndex`, `StorageContext`, `SimpleDirectoryReader`, `Settings`, node parsers, ingestion primitives, retrievers, query engines, tools, callbacks, and simple storage classes.
- `llama-index-integrations/*/*` packages add providers under `llama_index.<category>.<provider>`, not under `llama_index.core`.
- `llama-index-utils/*` packages add utility namespaces such as `llama_index.utils.<provider>`.

Prefer the customized route for production or constrained environments:

```bash
pip install llama-index-core
pip install llama-index-llms-ollama
pip install llama-index-embeddings-huggingface
pip install llama-index-vector-stores-qdrant
```

Use the starter `llama-index` package when the user wants a quick default OpenAI-oriented install and accepts the included integrations.

## Namespace Rule

The README states the practical rule:

```python
from llama_index.core.xxx import ClassABC      # core package
from llama_index.xxx.yyy import ProviderClass  # integration package
```

Concrete examples:

```python
from llama_index.core import Settings, StorageContext, VectorStoreIndex
from llama_index.core.llms import LLM
from llama_index.llms.openai import OpenAI
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
```

A `ModuleNotFoundError` for `llama_index.llms.openai`, `llama_index.embeddings.huggingface`, or `llama_index.vector_stores.qdrant` usually means the integration distribution is not installed, even if `llama-index-core` is installed and importable.

## Distribution Naming Pattern

Most integrations follow this distribution-to-module pattern:

| Capability | Distribution pattern | Import pattern | Example class |
| --- | --- | --- | --- |
| LLMs | `llama-index-llms-<provider>` | `llama_index.llms.<provider>` | `OpenAI`, `Ollama` |
| Embeddings | `llama-index-embeddings-<provider>` | `llama_index.embeddings.<provider>` | `HuggingFaceEmbedding` |
| Vector stores | `llama-index-vector-stores-<provider>` | `llama_index.vector_stores.<provider>` | `QdrantVectorStore`, `ChromaVectorStore` |
| Readers | `llama-index-readers-<provider>` | `llama_index.readers.<provider>` | provider reader classes |
| Tools | `llama-index-tools-<provider>` | `llama_index.tools.<provider>` | provider tool classes |
| Utilities | `llama-index-utils-<provider>` | `llama_index.utils.<provider>` | utility helpers |

Do not blindly transform every provider name: hyphenated distributions may map to underscore module components, and some packages expose multiple classes. When available, package metadata contains a `tool.llamahub.import_path` value that is the authoritative import path for that integration.

## Provider Selection Checklist

Before installing or writing code, ask:

1. Which role is needed: generation LLM, embedding model, vector store, reader/connector, tool, reranker/postprocessor, callback, or utility?
2. Does the user need a local/offline backend, a self-hosted service, or a cloud SaaS?
3. Does the provider package support the current `llama-index-core` line? For this skill, verified core is `0.14.x`; prefer integrations whose metadata allows `<0.15`.
4. Which non-LlamaIndex dependency will be installed, such as `openai`, `ollama`, `sentence-transformers`, `qdrant-client`, `chromadb`, or a cloud SDK?
5. Which credentials, endpoint, region, local daemon, collection/index, or model download is required after import succeeds?
6. Is the user's failure about import/install, model configuration, service availability, or RAG code? Route accordingly.

## Safe Verification Workflow

Use the bundled checker before changing imports or asking the user to reinstall broad packages:

```bash
python sub-skills/integrations-and-storage/scripts/check_integration_imports.py \
  --dist llama-index-core --module llama_index.core \
  --dist llama-index-vector-stores-qdrant --module llama_index.vector_stores.qdrant
```

Interpretation:

- Distribution present and module imports: the package boundary is satisfied; inspect credentials/service/config next.
- Distribution missing and module missing: install the narrow distribution.
- Distribution present but module missing: check distribution/import mismatch, stale environment, namespace collision, or incompatible package version.
- Module imports but distribution metadata missing: the module may come from a source checkout, editable install, namespace package, or differently named distribution; record the ambiguity before changing dependencies.

## Common Minimal Installs

Use these as patterns, not an exhaustive catalog:

```bash
pip install llama-index-core llama-index-llms-openai llama-index-embeddings-openai
pip install llama-index-core llama-index-llms-ollama llama-index-embeddings-huggingface
pip install llama-index-core llama-index-vector-stores-chroma
pip install llama-index-core llama-index-vector-stores-qdrant
pip install llama-index-core llama-index-readers-file
```

For provider-specific model settings, generation parameters, and structured output behavior, route to `../customization-and-structured-outputs/SKILL.md`. For using the selected integration inside a RAG index/query flow, route to `../indexing-and-querying/SKILL.md`.
