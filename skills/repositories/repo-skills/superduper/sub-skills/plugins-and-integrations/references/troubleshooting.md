# Plugin Troubleshooting

Start with the narrowest failure surface: import spelling, package installation, dependency import, URI routing, then runtime service/credential/GPU readiness. A plugin import check is intentionally network-free and does not validate live services.

## Missing plugin module

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'superduper_mongodb'` after `mongomock://`, `mongodb://`, or `mongodb+srv://` | MongoDB plugin is not installed in the active Python environment. | Install `superduper_mongodb`, then run `python scripts/check_superduper_plugins.py mongodb`. |
| `ModuleNotFoundError: No module named 'superduper_sql'` after `sqlite://`, `duckdb://`, `postgresql://`, `mssql://`, or `mysql://` | SQL plugin is not installed. | Install `superduper_sql`, then run `python scripts/check_superduper_plugins.py sqlite`. |
| `ModuleNotFoundError: No module named 'superduper_snowflake'` after `snowflake://` | Snowflake plugin is not installed. | Install `superduper_snowflake`, then separately validate Snowflake session/credentials. |
| `ModuleNotFoundError: No module named 'superduper_redis'` after `redis://` | Redis plugin is not installed. | Install `superduper_redis`, then separately validate Redis service access. |
| Missing `superduper_<provider>` for OpenAI/Anthropic/Cohere/Jina | Provider plugin is absent. | Install only the chosen provider plugin; do not install every API plugin. |

If a URI scheme is supported but its mapped plugin is absent, installing the mapped plugin is the fix. If the loader says no URI is supported at all, check the scheme spelling against the catalog before installing anything.

## Package name vs import name mismatches

Superduper first-party plugin imports use underscore modules even when package names are normalized differently by package indexes.

- Chroma: install package `superduper-chromadb`, import `superduper_chromadb`, and check with `python scripts/check_superduper_plugins.py chromadb`.
- Llama.cpp: install/import module `superduper_llamacpp`. If an example shows `superduper_llama_cpp`, treat that as stale spelling for this version.
- SQL/Mongo/Snowflake package names may be shown with hyphens in prose but import as `superduper_sql`, `superduper_mongodb`, and `superduper_snowflake`.
- The bundled checker accepts common aliases such as `sqlite`, `mongomock`, `llama_cpp`, `pytorch`, `sentence-transformers`, and `scikit-learn`.

## Dependency import failures

A plugin module may exist but fail during import because one of its dependencies is missing or incompatible. Examples include `openai`, `cohere`, `qdrant_client`, `chromadb`, `torch`, `snowflake`, or `ibis` packages.

Diagnose without network or credentials:

```bash
python scripts/check_superduper_plugins.py <plugin-name>
python -m pip check
python - <<'PY'
import importlib.metadata as md
for dist in ["superduper-framework", "superduper_mongodb", "superduper_sql"]:
    try:
        print(dist, md.version(dist))
    except md.PackageNotFoundError:
        print(dist, "not installed")
PY
```

Fix by reinstalling the selected plugin package and aligning dependency versions in the target environment. Do not broaden to all plugins unless the task genuinely uses them.

## Credentials and live API calls

Provider plugins can import successfully but still fail at prediction time.

| Plugin | Common runtime boundary |
|---|---|
| `superduper_openai` | Requires OpenAI credentials, model access, network, quota, and compatible `openai` SDK behavior. |
| `superduper_anthropic` | Requires Anthropic credentials, model access, network, and quota. |
| `superduper_cohere` | Requires Cohere credentials, model access, network, and quota. |
| `superduper_jina` | Requires Jina API credentials/network for embedding calls. |

This sub-skill can tell an agent which plugin to install and how to import it. It should not create, request, store, or test real provider credentials unless a higher-level workflow explicitly authorizes those live calls.

## Service connection failures

Import checks do not contact services. Treat these as separate readiness gates:

- `mongodb://...`: validate MongoDB host, port, auth, database name, and network route.
- `mongodb+srv://...`: validate Atlas cluster DNS, credentials, network access list, and any vector-search index requirements.
- `snowflake://...`: validate Snowflake host/account/warehouse/database/session token and secret status. Secret helper exports can report pending/running secret state after a Snowflake-backed Datalayer is available.
- `redis://...`: validate Redis URI, auth, TLS mode if used, and connectivity.
- `chromadb://...` and `qdrant://...`: validate client/server version and service endpoint or in-memory mode.
- `lance`: validate local storage paths and dependency version bounds.

If a service route fails after import succeeds, stop treating it as an installation problem and route to the workflow/backend skill that owns that service.

## GPU, model downloads, and heavy ML runtimes

Imports are not proof of model runtime readiness.

- `superduper_torch`: CPU import does not prove CUDA. Align `torch` and `torchvision` wheel variants with the target hardware before training or GPU inference.
- `superduper_transformers`: model construction may download tokenizer/model weights and may require GPU memory for large models or training.
- `superduper_sentence_transformers`: construction may download sentence-transformer weights and use device settings.
- `superduper_vllm`: usually requires CUDA-compatible GPUs, vLLM-compatible Python/torch stacks, and available model weights.
- `superduper_llamacpp`: requires local GGUF/model files and a compatible llama-cpp build; GPU acceleration depends on build flags and hardware.

For offline or restricted environments, pre-stage model artifacts and test the exact model runtime in the owning model/training skill rather than in this install layer.

## Version mismatch and stale exports

The prepared environment verified `superduper-framework` and `superduper_mongodb`; optional plugins beyond MongoDB were not installed there. If an import or class lookup fails:

1. Compare base and plugin versions with `importlib.metadata.version(...)`.
2. Check the plugin's `__version__` attribute after import.
3. Import names from the plugin's `__init__.py` first; use submodule imports only when the catalog or task requires a class that is not re-exported.
4. Re-run the bundled checker after any package changes.

Common stale-export patterns:

- README/API material may mention classes that exist in a submodule but are not exported from `__init__.py`.
- The OpenAI plugin exports `OpenAIChatCompletion` and `OpenAIEmbedding` from `__init__.py`; additional OpenAI classes may require `superduper_openai.model` imports.
- The Llama.cpp plugin import module is `superduper_llamacpp` in this version.

## Custom `Plugin` component failures

| Symptom | Cause | Fix |
|---|---|---|
| Assertion that plugin path was not found | `Plugin(path=...)` points to a file/directory that does not exist in the runtime environment. | Provide a real local file/package path in the user's working context. Do not depend on a vanished source checkout. |
| ValueError that path is not valid | Path is neither a `.py` file, package directory, nor `requirements.txt`. | Package the plugin as a Python file/directory or provide a requirements file intentionally. |
| Pip install failure during `Plugin(...)` | A package directory or requirements file triggered `python -m pip install -r ...` and dependency resolution failed. | Inspect requirements, retry in an isolated environment, or remove unsafe/heavy dependencies. |
| Import succeeds once but repeated load skips import | The component sets a `_PLUGIN_<uuid>` environment tag to avoid repeated installation in one process. | Restart the process or use a new component UUID if a true reload is needed. |
| Serialized plugin reload points to cache | Applying the component copies artifacts to cache and reloads from there. | Keep plugin artifacts self-contained and avoid hard-coded local paths. |

Security rule: `Plugin` executes local Python and may install requirements. Use only trusted code, and never use it as a credential or service-provisioning mechanism.

## Synthetic diagnostic patterns

Use these patterns when verifying this sub-skill:

1. Given four requests (`sqlite://...`, `mongomock://...`, `snowflake://...`, and OpenAI chat), choose only `superduper_sql`, `superduper_mongodb`, `superduper_snowflake`, and `superduper_openai`, then explain why only MongoDB/mongomock was live-verified in the prepared environment.
2. Given `ModuleNotFoundError: No module named 'superduper_qdrant'` while building a vector index, diagnose the missing optional plugin, run the checker for `qdrant` only, and avoid installing unrelated provider/GPU packages.
