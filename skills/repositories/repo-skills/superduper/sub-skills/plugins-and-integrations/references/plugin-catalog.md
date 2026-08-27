# Superduper Plugin Catalog

This catalog covers first-party Superduper plugin packages and the core plugin-loading routes a future agent is likely to need. Package names are taken from plugin metadata; import modules and exports are taken from each plugin's `__init__.py` behavior. Only `superduper_mongodb` was live-verified in the prepared environment; all other entries should be installed and import-checked before use.

## How Superduper loads plugins

`superduper.misc.importing.load_plugin(name)` imports built-in backends for `local`, `inmemory`, and `simple`; otherwise it imports `superduper_<name>`. That means most plugin failures surface as `ModuleNotFoundError: No module named 'superduper_<name>'` or as a missing dependency imported by that module.

### Data backend URI routing

The data-backend loader maps URI schemes to plugin names and calls the plugin's exported `DataBackend` implementation.

| URI scheme | Plugin loaded | Expected import module | Notes |
|---|---|---|---|
| `mongodb://...` | `mongodb` | `superduper_mongodb` | Real MongoDB service required. |
| `mongodb+srv://...` | `mongodb` with Atlas flavor | `superduper_mongodb` | Atlas/network/credentials required. |
| `mongomock://...` | `mongodb` with mongomock flavor | `superduper_mongodb` | Local fake MongoDB path; this was the only plugin-backed route live-verified. |
| `sqlite://...` | `sql` | `superduper_sql` | Local SQL route backed by ibis/sqlalchemy dependencies. |
| `duckdb://...` | `sql` | `superduper_sql` | Requires SQL plugin plus compatible DuckDB/ibis support. |
| `postgresql://...` | `sql` | `superduper_sql` | Requires a reachable PostgreSQL service and driver support. |
| `mssql://...` | `sql` | `superduper_sql` | Requires a reachable MSSQL service and driver support. |
| `mysql://...` | `sql` | `superduper_sql` | Requires a reachable MySQL service and driver support. |
| `snowflake://...` | `snowflake` | `superduper_snowflake` | Requires Snowflake credentials/session state and service access. |
| `redis://...` | `redis` | `superduper_redis` | Requires a reachable Redis service. |
| `inmemory://...` | built-in `inmemory` | `superduper.backends.inmemory` | Built into the base package; do not install a first-party plugin for this route. |

### Vector search routing

The local/simple cluster builders load a vector search implementation from `CFG.vector_search_engine`: they take the text before `://` when present, call `load_plugin(...)`, and use that module's exported `VectorSearcher`. Therefore an engine such as `qdrant://:memory:` loads `superduper_qdrant`, while `chromadb://localhost:9000` loads `superduper_chromadb`. Import success does not prove the service is running or that vector indexes can be created.

## First-party plugin packages

| Area | Plugin key / common aliases | Package to install | Import module | Exported from `__init__.py` | Dependencies recorded in plugin metadata | Boundary and verification notes |
|---|---|---|---|---|---|---|
| MongoDB data backend and Atlas vector search | `mongodb`, `mongomock`, `atlas` | `superduper_mongodb` | `superduper_mongodb` | `DataBackend`, `DatabaseListener`, `VectorSearcher` | `mongomock`, `pymongo`, `click` | `mongomock://` was live-verified. Real `mongodb://` and `mongodb+srv://` require a service, network, and credentials. Atlas vector search is not proven by a mongomock smoke. |
| SQL data backend | `sql`, `sqlite`, `duckdb`, `postgresql`, `mssql`, `mysql` | `superduper_sql` | `superduper_sql` | `DataBackend`, `DatabaseListener` | `ibis-framework[sqlite]==10.4.0`, `click`, `pandas`, `sqlalchemy>=1.4.0` | `sqlite://` is the lightest route. Other SQL schemes may need service-specific drivers and a reachable database. |
| Snowflake data backend and vector search | `snowflake` | `superduper_snowflake` | `superduper_snowflake` | `DataBackend`, `DatabaseListener`, `VectorSearcher`, `check_secret_updates`, `raise_if_secrets_pending`, `secrets_not_ready` | `snowflake`, `snowflake-snowpark-python[localtest]`, `snowflake-connector-python==3.15.0`, `snowflake-sqlalchemy`, `watchdog>=6.0.0`, `ibis-framework[snowflake]` | Requires Snowflake account/session/token environment and service access. Secret helpers report pending/running secret state; this skill does not provision secrets. |
| Redis data backend | `redis` | `superduper_redis` | `superduper_redis` | `DataBackend` | `redis` | Requires a Redis URI and reachable service. |
| Chroma vector search | `chromadb`, `chroma` | `superduper-chromadb` | `superduper_chromadb` | `VectorSearcher` | `chromadb` | Package name uses a hyphen while the import module uses an underscore. Chroma server/client availability is separate from import success. |
| Lance vector search | `lance` | `superduper_lance` | `superduper_lance` | `VectorSearcher` | `pylance>=0.6.1,<=0.8.14` | Version bounds are narrow; verify dependency resolution before assuming existing environments are compatible. |
| Qdrant vector search | `qdrant` | `superduper_qdrant` | `superduper_qdrant` | `VectorSearcher` | `qdrant-client>=1.10.0,<2` | Can import without a live service, but service or in-memory configuration must be separately validated. |
| OpenAI API models | `openai` | `superduper_openai` | `superduper_openai` | `OpenAIChatCompletion`, `OpenAIEmbedding` | `numpy`, `openai>=1.1.2`; test extra: `vcrpy==5.1.0`, `urllib3==2.2.3` | Imports do not verify `OPENAI_API_KEY`, account quota, network, or live model access. Some model-module classes are not re-exported from `__init__.py`; import them from `superduper_openai.model` only when needed. |
| Anthropic API models | `anthropic` | `superduper_anthropic` | `superduper_anthropic` | `AnthropicCompletions` | `anthropic>=0.25.0`; test extra: `vcrpy>=5.1.0` | Requires provider credentials and live API access for prediction. |
| Cohere API models | `cohere` | `superduper_cohere` | `superduper_cohere` | `CohereEmbed`, `CohereGenerate` | `cohere==4.40`; test extra: `vcrpy>=5.1.0` | Requires provider credentials and live API access for prediction. |
| Jina embedding API | `jina` | `superduper_jina` | `superduper_jina` | `JinaEmbedding` | `aiohttp`; test extra: `vcrpy>=5.1.0` | Requires Jina API credentials/network for live calls. |
| Llama.cpp local models | `llamacpp`, `llama_cpp`, `llama-cpp` | `superduper_llamacpp` | `superduper_llamacpp` | `LlamaCpp`, `LlamaCppEmbedding` | `llama_cpp_python>=0.2.39` | Requires local GGUF/model files and compatible llama-cpp build. Some examples may show `superduper_llama_cpp`; this version's import module is `superduper_llamacpp`. |
| vLLM self-hosted LLMs | `vllm` | `superduper_vllm` | `superduper_vllm` | `VllmChat`, `VllmCompletion` | `vllm`; test extra: `pytest-asyncio` | Usually needs GPU/CUDA-compatible wheels and local model weights or model-cache access. Import does not prove inference can start. |
| Sentence Transformers embeddings | `sentence_transformers`, `sentence-transformers` | `superduper_sentence_transformers` | `superduper_sentence_transformers` | `SentenceTransformer` | `sentence-transformers>=2.2.2` | Model construction may download/cache weights and may use CPU or GPU depending on device settings. |
| Hugging Face Transformers models/training | `transformers`, `huggingface`, `hf` | `superduper_transformers` | `superduper_transformers` | `LLM`, `TextClassificationPipeline`, `LLMTrainer` | `sentence-transformers>=2.2.2`, `datasets>=2.18.0`, `peft>=0.10.0`, `trl==0.12.0` | Large dependencies, model downloads, optional GPU, and training runtime are outside this install-only sub-skill. |
| PyTorch models/training/encoders | `torch`, `pytorch` | `superduper_torch` | `superduper_torch` | `Tensor`, `TorchModel`, `torchmodel`, `TorchTrainer` | `torch>=2.1.2`, `torchvision>=0.17.1` | CPU import is not proof of CUDA availability. Align torch/torchvision wheel variants with the target hardware. |
| scikit-learn estimators | `sklearn`, `scikit-learn`, `scikit_learn` | `superduper_sklearn` | `superduper_sklearn` | `Estimator`, `SklearnTrainer` | `scikit-learn>=1.2.2` | CPU-local ML integration; still validate sklearn version in the target environment. |
| Pillow image encoder | `pillow`, `image` | `superduper_pillow` | `superduper_pillow` | `pil_image` | `pillow>=10.2.0`; test extra: `ibis-framework[sqlite]>=5.1.0` | Local image encoding helper. It is not a service backend. |
| Plugin template | `template` | `superduper_template` | `superduper_template` | none | none | Template/starter package. It is not a runtime integration target unless a task explicitly concerns plugin authoring. |

## Custom `Plugin` component behavior

`superduper.components.plugin.Plugin` is separate from the first-party package catalog. It packages a local plugin file, local package directory, or requirements file as a Superduper component.

Observed behavior:

- Constructor fields include `identifier`, `path`, and `cache_path` with a default cache under the user's home directory.
- A `.py` path is loaded as a standalone module.
- A directory path is treated as a package. If `__init__.py` is missing, the component creates it before import.
- If a package directory or requirements-file path contains `requirements.txt`, the component runs `python -m pip install -r ...` in the active Python environment.
- The component copies the plugin artifact into its cache, imports the module with `importlib.util`, registers it in `sys.modules`, and sets an environment tag so the same component UUID is not repeatedly installed in one process.
- Native tests exercise module plugins, package plugins, package directories, requirements files, serialized `Plugin.read(...)`, repeated loading, and `db.apply(...)` followed by reload.

Safety boundary: use `Plugin` only for trusted local code. Review requirements before applying it, because the component can mutate the active Python environment by invoking pip. Do not depend on a path from an original checkout as a runtime requirement; package or copy the plugin artifact into the user's working context first.
