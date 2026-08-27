# Root Troubleshooting

Use this root page for quick triage, then route to the focused sub-skill page for the detailed fix.

## Import or installation fails

| Symptom | Likely cause | First action | Deeper route |
| --- | --- | --- | --- |
| `ModuleNotFoundError: No module named 'nano_graphrag'` | Package not installed in the active environment. | Run `pip install nano-graphrag` or install the local checkout with `pip install -e .` in the environment that will run the code. | [package overview](package-overview.md) |
| `ModuleNotFoundError: No module named 'transformers'` while importing `nano_graphrag` | This version imports `transformers.AutoTokenizer` even if package metadata did not install it. | Run `pip install transformers`, then retry `from nano_graphrag import GraphRAG`. | [core troubleshooting](../sub-skills/core-graphrag-workflows/references/troubleshooting.md) |
| Native package build errors for `hnswlib` or scientific packages | Missing compiler/wheel for the platform or Python version. | Prefer Python 3.10/3.11, install build tools if compiling is acceptable, or use the default NanoVectorDB storage until HNSW is needed. | [storage troubleshooting](../sub-skills/storage-backends/references/troubleshooting.md) |

## Query mode or lifecycle fails

| Symptom | Likely cause | First action | Deeper route |
| --- | --- | --- | --- |
| `enable_local is False, cannot query in local mode` | `GraphRAG` was created with local mode disabled. | Recreate with `enable_local=True` before inserting/querying local graph context. | [core workflows](../sub-skills/core-graphrag-workflows/SKILL.md) |
| `enable_naive_rag is False, cannot query in naive mode` | Naive vector index was not enabled at construction/insertion time. | Recreate with `enable_naive_rag=True` and reinsert content into that working directory. | [core workflows](../sub-skills/core-graphrag-workflows/SKILL.md) |
| Reloaded results look inconsistent after changing embeddings or vector backend | Old working directory artifacts no longer match current config. | Use a fresh `working_dir` or deliberately migrate/rebuild stored artifacts. | [core API](../sub-skills/core-graphrag-workflows/references/core-api.md) and [storage backends](../sub-skills/storage-backends/SKILL.md) |

## Provider/model failures

| Symptom | Likely cause | First action | Deeper route |
| --- | --- | --- | --- |
| Hosted API returns authentication, rate limit, or endpoint errors | Missing/incorrect credentials, base URL, deployment/model ID, or region. | Verify provider-specific env vars and model IDs; do not test with real calls until network/credential policy is explicit. | [provider troubleshooting](../sub-skills/provider-and-model-integrations/references/troubleshooting.md) |
| Provider rejects `response_format`, `max_tokens`, or unknown kwargs | Custom provider is not fully OpenAI-compatible. | Strip unsupported kwargs in the custom `best_model_func`/`cheap_model_func` before calling the SDK. | [provider recipes](../sub-skills/provider-and-model-integrations/references/provider-recipes.md) |
| Global/community report JSON cannot be parsed | Model output is malformed or prompt/response format is too loose. | Probe the raw response with the JSON repair script, then tighten provider prompt or set `convert_response_to_json_func`. | [customization troubleshooting](../sub-skills/customization-and-troubleshooting/references/troubleshooting.md) |

## Empty graph or entity extraction failures

| Symptom | Likely cause | First action | Deeper route |
| --- | --- | --- | --- |
| `Processed ... 0 entities ... 0 relations` | LLM did not emit the expected entity/relationship tuple format, or context was too small. | Inspect model output format; for Ollama, increase model context (`num_ctx`) before blaming storage. | [customization troubleshooting](../sub-skills/customization-and-troubleshooting/references/troubleshooting.md) |
| `Leiden.EmptyNetworkError` or empty graph clustering failure | No entities/relationships were inserted into the graph. | Debug entity extraction/provider output first; storage replacement rarely fixes an empty graph by itself. | [customization troubleshooting](../sub-skills/customization-and-troubleshooting/references/troubleshooting.md) |

## Storage/backend failures

| Symptom | Likely cause | First action | Deeper route |
| --- | --- | --- | --- |
| `Missing neo4j_url or neo4j_auth in addon_params` | `Neo4jStorage` requires explicit service config. | Pass `addon_params={"neo4j_url": ..., "neo4j_auth": (user, password)}` and verify Neo4j 5.x plus GDS plugin. | [storage troubleshooting](../sub-skills/storage-backends/references/troubleshooting.md) |
| HNSW insertion overflows `max_elements` | Index capacity is fixed at construction/load time. | Set a larger `vector_db_storage_cls_kwargs={"max_elements": ...}` before building the index. | [storage backends](../sub-skills/storage-backends/SKILL.md) |
| Vector query returns dimension or shape errors | Embedding function output does not match `embedding_func.embedding_dim`, or an old index was created with a different dimension. | Validate the embedding wrapper and use a fresh working directory when dimensions change. | [embedding functions](../sub-skills/provider-and-model-integrations/references/embedding-functions.md) |

## Safe validation helpers

- Run the root [environment check](../scripts/check_nano_graphrag_env.py) for import and basic API validation.
- Run the core [no-network smoke](../sub-skills/core-graphrag-workflows/scripts/core_smoke.py) for deterministic insert/query coverage.
- Run the storage [storage smoke](../sub-skills/storage-backends/scripts/storage_smoke.py) for local storage classes.
- Run the JSON [repair probe](../sub-skills/customization-and-troubleshooting/scripts/json_repair_probe.py) on raw model output before changing application code.
