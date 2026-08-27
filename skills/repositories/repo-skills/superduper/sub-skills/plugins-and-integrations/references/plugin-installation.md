# Plugin Selection and Installation

Use the smallest plugin set that matches the task. Do not install all optional plugins just to fix one `ModuleNotFoundError`; first identify the URI, model provider, vector engine, or encoder that triggered the missing import.

## Quick selection recipes

| User intent | Choose this plugin | Minimum check | Boundary before deeper work |
|---|---|---|---|
| Build a local SQLite-backed Datalayer, or a SQL Datalayer for `sqlite://...` | `superduper_sql` | `python scripts/check_superduper_plugins.py sqlite` | SQL query semantics and table workflows belong to the data/query skills after import succeeds. |
| Build a local fake MongoDB Datalayer with `mongomock://...` | `superduper_mongodb` | `python scripts/check_superduper_plugins.py mongomock` | This route was live-verified in the prepared environment; it still does not prove Atlas vector search. |
| Connect to MongoDB or Atlas | `superduper_mongodb` | `python scripts/check_superduper_plugins.py mongodb` | Real service URI, network, auth, and Atlas vector-search setup are outside this sub-skill. |
| Connect to Snowflake with `snowflake://...` | `superduper_snowflake` | `python scripts/check_superduper_plugins.py snowflake` | Requires Snowflake session/token/environment and service access; do not provision credentials here. |
| Use Redis as a data backend | `superduper_redis` | `python scripts/check_superduper_plugins.py redis` | Requires a reachable Redis service. |
| Use OpenAI embeddings/chat, including simple RAG-style examples | `superduper_openai` | `python scripts/check_superduper_plugins.py openai` | Import success does not validate API keys, quotas, network, or live model names. |
| Use Anthropic, Cohere, or Jina API-backed models | `superduper_anthropic`, `superduper_cohere`, or `superduper_jina` | Check the chosen provider only | Provider credentials and live API calls are excluded from this sub-skill. |
| Use local/self-hosted LLMs | `superduper_llamacpp`, `superduper_transformers`, or `superduper_vllm` | Check the exact plugin | Model weights, GPU/CUDA/runtime servers, and downloads are separate readiness gates. |
| Use ML framework wrappers | `superduper_torch`, `superduper_sklearn`, or `superduper_sentence_transformers` | Check the exact plugin | Training and model-workflow details belong to sibling model/training skills. |
| Use image encoding | `superduper_pillow` | `python scripts/check_superduper_plugins.py pillow` | This is an encoder helper, not a data service. |
| Use Chroma, Lance, Qdrant, Mongo Atlas, or Snowflake vector search | `superduper_chromadb`, `superduper_lance`, `superduper_qdrant`, `superduper_mongodb`, or `superduper_snowflake` | Check the selected vector plugin | Import success does not prove the vector service, index creation, or native search behavior. |
| Use custom local package code as a Superduper component | Base package `Plugin` component, not a first-party plugin package | Import the resulting local module after `Plugin(...)` prepares it | The component can run pip against local requirements; use only trusted code. |

## Install the base package and selected plugins

Install the base package first, then install only the selected plugin package names from the catalog.

```bash
python -m pip install superduper-framework
python -m pip install superduper_mongodb      # MongoDB, Atlas, mongomock
python -m pip install superduper_sql          # sqlite/duckdb/postgresql/mssql/mysql routes
python -m pip install superduper_snowflake    # Snowflake backend/vector search
python -m pip install superduper_redis        # Redis backend
python -m pip install superduper_openai       # OpenAI models
python -m pip install superduper_torch        # PyTorch wrappers
```

Notes:

- `superduper-chromadb` is the package name recorded for the Chroma plugin, while the import module is `superduper_chromadb`.
- Most package managers normalize hyphens and underscores, but import statements always use underscores.
- Do not install provider, GPU, or service plugins unless the task actually uses them.
- In an existing environment, inspect version constraints first. Some plugins pin narrow dependency ranges.

## Import checks without network or credentials

From the generated skill's sub-skill directory, run the bundled checker:

```bash
python scripts/check_superduper_plugins.py --list-known
python scripts/check_superduper_plugins.py sqlite openai
python scripts/check_superduper_plugins.py --all-known
```

The checker imports requested plugin modules and prints install hints for missing plugins. It does not install packages, open sockets, contact cloud APIs, read secrets, download model weights, or create databases.

Use it as a narrow gate:

1. Request only the plugin(s) needed by the task.
2. If a plugin is missing, install that plugin package, not every optional plugin.
3. Re-run the checker.
4. After import succeeds, route task-specific usage to the relevant sibling skill.

## Minimal import snippets

These snippets prove import spelling only; they are not full workflow examples.

```python
from superduper_mongodb import DataBackend as MongoDataBackend
from superduper_sql import DataBackend as SQLDataBackend
from superduper_snowflake import DataBackend as SnowflakeDataBackend
from superduper_openai import OpenAIChatCompletion, OpenAIEmbedding
from superduper_torch import Tensor, TorchModel, TorchTrainer
from superduper_pillow import pil_image
```

For modules whose `__init__.py` does not re-export every class shown in README/API material, import from the submodule explicitly only after the package import works, for example:

```python
from superduper_openai.model import OpenAIEmbedding
from superduper_llamacpp.model import LlamaCpp
```

Use `superduper_llamacpp`, not `superduper_llama_cpp`, for the Llama.cpp plugin in this version.

## URI-driven backend workflow

When a user starts from a Superduper URI, identify the plugin from the URI before doing anything else:

```text
mongomock://test_db       -> install/check superduper_mongodb
mongodb://host/db         -> install/check superduper_mongodb, then separately validate service/auth
mongodb+srv://...         -> install/check superduper_mongodb, then separately validate Atlas/auth
sqlite://...              -> install/check superduper_sql
duckdb://...              -> install/check superduper_sql
snowflake://...           -> install/check superduper_snowflake, then separately validate Snowflake session/token
redis://...               -> install/check superduper_redis, then separately validate Redis service
inmemory://...            -> built-in backend; no first-party plugin package
```

If the loader raises `No support for uri`, check the scheme spelling first. If the URI scheme is supported but import fails, install the mapped plugin package.

## Vector-search workflow

For `CFG.vector_search_engine`, Superduper loads the plugin named before `://` and expects a `VectorSearcher` export. Use these checks before configuring a vector index:

```bash
python scripts/check_superduper_plugins.py chromadb
python scripts/check_superduper_plugins.py qdrant
python scripts/check_superduper_plugins.py lance
python scripts/check_superduper_plugins.py snowflake
python scripts/check_superduper_plugins.py mongodb
```

Then validate the service or native vector capability outside this sub-skill. For example, Chroma/Qdrant may need a running service, MongoDB vector search may require Atlas/native vector-search setup, and Snowflake vector search requires Snowflake session state.

## Custom `Plugin` component workflow

Use `superduper.components.plugin.Plugin` only for trusted local code that should be loaded as a Superduper component.

```python
from superduper.components.plugin import Plugin

plugin = Plugin(identifier="my_plugin", path="my_plugin.py")
# or: Plugin(identifier="my_package", path="my_package_directory")
```

Operational rules:

- A `.py` file becomes a standalone module.
- A directory becomes a package; the component can create a missing `__init__.py`.
- A `requirements.txt` file can trigger `python -m pip install -r ...` in the active Python environment.
- Applying the component stores the copied artifact and reloads from cache later.

Safety rules:

- Inspect requirements before applying a plugin component.
- Do not use untrusted plugin paths.
- Do not depend on the source checkout path remaining available; keep the plugin artifact in the user's working context or package it normally.
- Do not use this component as a shortcut for provider credentials, service provisioning, or model downloads.
