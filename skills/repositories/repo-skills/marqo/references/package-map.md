# Marqo Package Map

Read this when you need the component/package/import layout, public service routes, or cross-component dependencies before choosing a sub-skill.

## Components and distributions

| Component | Distribution | Import name | Role | Primary sub-skill |
| --- | --- | --- | --- | --- |
| Main Marqo API | `marqo-api` | `marqo` | FastAPI API service, index/document/search/typeahead routes, core models, Vespa clients, inference clients. | `documents-and-api`, `index-and-vespa`, `search-and-ranking` |
| Shared registry | `marqo-common` | `marqo_common` | Shared model registry and version helpers. | `inference-and-models` |
| Inference orchestrator | `marqo-inference-orchestrator` | `inference_orchestrator` | Direct `/vectorise` service, preprocessing schemas, random/HF/OpenCLIP pipelines, Triton client, inference cache. | `inference-and-models` |
| Model management | `marqo-model-management` | `model_management` | Model load/unload API and Triton model repository/download helpers. | `inference-and-models` |
| Vespa custom searchers | Maven project | Java package under Vespa app | Custom Vespa searcher build/deploy inputs for Marqo ranking. | `index-and-vespa`, `local-development` |

All Python components require Python 3.11 according to the component metadata. Development and final test commands should install only the component and dependency groups needed for the selected task.

## Verified service routes

Installed-package inspection found these important routes.

### Marqo API service

- Health and basic info: `GET /`, `GET /health`, `GET /device/cpu`, `GET /memory`.
- Indexes: `GET /indexes`, `POST /indexes/{index_name}`, `DELETE /indexes/{index_name}`, `GET /indexes/{index_name}/settings`, `PATCH /indexes/{index_name}/index-settings`, `GET /indexes/{index_name}/health`, `GET /indexes/{index_name}/stats`, `POST /indexes/{index_name}/apply-latest-schema-template`.
- Documents: `POST /indexes/{index_name}/documents`, `PATCH /indexes/{index_name}/documents`, `GET /indexes/{index_name}/documents/{document_id}`, `GET /indexes/{index_name}/documents`, `POST /indexes/{index_name}/documents/get-batch`, `POST /indexes/{index_name}/documents/delete-batch`, gated `DELETE /indexes/{index_name}/documents/delete-all`.
- Search/recommend/embed: `POST /indexes/{index_name}/search`, `POST /indexes/{index_name}/recommend`, `POST /indexes/{index_name}/embed`.
- Models: `GET /models`, `DELETE /models`.
- Typeahead: `POST /indexes/{index_name}/suggestions`, `POST /indexes/{index_name}/suggestions/queries`, `DELETE /indexes/{index_name}/suggestions/queries`, `GET /indexes/{index_name}/suggestions/queries`, `GET /indexes/{index_name}/suggestions/stats`, gated delete-all.
- Gated ops: batch index create/delete, upgrade, rollback, rollback-vespa, schema validation.

### Inference orchestrator

- `GET /`, `GET /healthz`, `POST /vectorise`, `GET /models`, `DELETE /models`.
- `/vectorise` is a direct inference service route. It expects msgpack payloads and complete model properties; it is not the same as the public Marqo API search route.

### Model-management service

- `GET /v1/healthz`.
- `POST /v1/models/load`.
- `POST /v1/models/{model_name}/unload`.

## Important enums and payload fields

- Search methods: `TENSOR`, `LEXICAL`, `HYBRID`.
- Device values: `cpu`, `cuda`.
- Index types: `structured`, `unstructured`, `semi-structured`; new work should prefer semi-structured over legacy unstructured and should not add behavior only to deprecated structured internals.
- Field types include scalar text/bool/numeric fields, arrays, image/video/audio pointers, multimodal combinations, custom vectors, and text-to-number map fields.
- Distance metrics include `euclidean`, `angular`, `dotproduct`, `prenormalized-angular`, `geodegrees`, and `hamming`.
- Vector numeric types include `float` and `bfloat16`.
- Text split methods include `character`, `word`, `sentence`, and `passage`.
- Patch methods include `simple`, `frcnn`, `dino-v1`, `dino-v2`, and `marqo-yolo`.

## Environment variables and runtime gates

Use these names when diagnosing runtime configuration. Keep actual values private unless the user provides them for the task.

| Area | Variables |
| --- | --- |
| Vespa endpoints | `VESPA_CONFIG_URL`, `VESPA_QUERY_URL`, `VESPA_DOCUMENT_URL`, `VESPA_CONTENT_CLUSTER_NAME`, `VESPA_SEARCH_TIMEOUT_MS`, pool-size variables |
| API route gates | `MARQO_ENABLE_BATCH_APIS`, `MARQO_ENABLE_UPGRADE_API`, `MARQO_ENABLE_DEBUG_API`, `MARQO_ENABLE_OPS_API` |
| Model/inference | `MARQO_REMOTE_INFERENCE_URL`, `MARQO_MODELS_TO_PRELOAD`, `MARQO_PATCH_MODELS_TO_PRELOAD`, `MARQO_MAX_CPU_MODEL_MEMORY`, `MARQO_MAX_CUDA_MODEL_MEMORY`, `MARQO_MAX_VECTORISE_BATCH_SIZE`, inference cache variables |
| Limits | `MARQO_MAX_DOC_BYTES`, `MARQO_MAX_RETRIEVABLE_DOCS`, `MARQO_MAX_SEARCH_LIMIT`, `MARQO_MAX_SEARCH_OFFSET`, `MARQO_MAX_DOCUMENTS_BATCH_SIZE`, `MARQO_MAX_DELETE_DOCS_COUNT` |
| Concurrency and locks | `MARQO_MAX_CONCURRENT_INDEX`, `MARQO_MAX_CONCURRENT_SEARCH`, `MARQO_MAX_CONCURRENT_PARTIAL_UPDATE`, `ZOOKEEPER_HOSTS`, `ZOOKEEPER_CONNECTION_TIMEOUT` |
| Observability | `MARQO_LOG_LEVEL`, `MARQO_LOG_FORMAT`, StatsD and OpenTelemetry-related settings |

## Local service topology

The common development topology is:

1. Vespa configuration/document/query endpoints are available.
2. Marqo API runs on port `8882` and points at Vespa.
3. Optional model-management service runs on port `8883` and manages Triton model repository state.
4. Optional inference orchestrator runs on port `8884` and calls Triton plus model-management.
5. Optional Triton exposes HTTP/gRPC ports for model execution.
6. Optional Redis throttling can be disabled if Redis is not configured.

Open `sub-skills/local-development/references/local-services.md` before starting or changing services.
