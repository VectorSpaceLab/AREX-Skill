# Marqo HTTP API route map

This reference covers route mechanics and request/response validation for the public Marqo API surface owned by this sub-skill. Ranking semantics, Vespa schema details, inference backend internals, and service startup are intentionally routed to the sibling sub-skills named in `SKILL.md`.

## Public route matrix

### Service, index, model, and device routes

| Method and path | Purpose | Request shape | Success response shape | Notes |
|---|---|---|---|---|
| `GET /` | Basic service metadata. | No body. | `{"message": "Welcome to Marqo", "version": "..."}`. | Fast smoke check that does not require an index. |
| `GET /health` | Whole-service health. | No body. | `HealthResponse` with `status`, `inference.status`, and `backend.status`, plus backend memory/storage booleans when available. | Useful before any write call. |
| `GET /indexes` | List indexes. | No body. | `{"results": [{"indexName": "..."}]}`. | Non-mutating index discovery. |
| `POST /indexes/{index_name}` | Create an index. | `IndexSettings` JSON body. | `{"acknowledged": true, "index": "<index_name>"}`. | Prefer `type: "semi-structured"` for new generic smoke payloads; structured indexes require `allFields` and `tensorFields`. |
| `GET /indexes/{index_name}/settings` | Read index settings. | No body. | Settings JSON using public camelCase aliases. | Field/schema meaning belongs in `index-and-vespa`. |
| `GET /indexes/{index_name}/stats` | Read document/vector and backend usage stats. | No body. | `numberOfDocuments`, `numberOfVectors`, `backend.memoryUsedPercentage`, `backend.storageUsedPercentage`. | Useful after add/delete workflows. |
| `GET /indexes/{index_name}/health` | Index-specific health. | No body. | Same `HealthResponse` model as service health, scoped to the index. | Confirms index backend health after writes. |
| `DELETE /indexes/{index_name}` | Delete an index. | No body. | `{"acknowledged": true}`. | Destructive. Use only for cleanup or explicit index removal. |
| `GET /models` | List loaded models. | Optional query `detailed=true|false`. | Model-manager response. | Backend/model internals are handled by `inference-and-models`. |
| `DELETE /models` | Eject a loaded model. | Query `model_name=<name>`. | Model-manager response. | Destructive for model cache state. |
| `GET /device/cpu` | CPU usage snapshot. | No body. | `cpu_usage_percent`, `memory_used_percent`, `memory_used_gb`. | Non-mutating local resource probe. |

### Document and content routes

| Method and path | Purpose | Request shape | Success response shape | Notes |
|---|---|---|---|---|
| `POST /indexes/{index_name}/documents` | Add or replace documents. | `AddDocsBodyParams`: `documents` plus optional `tensorFields`, `useExistingTensors`, `mappings`, `mediaDownloadHeaders`, `imageDownloadHeaders`, `modelAuth`, thread counts, `textChunkPrefix`. | Add-docs response with per-item status and count headers. | `imageDownloadHeaders` is deprecated; do not send it with `mediaDownloadHeaders`. |
| `PATCH /indexes/{index_name}/documents` | Partial update documents. | `UpdateDocumentsBodyParams`: `{"documents": [{"_id": "...", ...}]}`. | Partial update response with per-item status and count headers. | `_id` is required for each partial document. |
| `GET /indexes/{index_name}/documents/{document_id}` | Get one document. | Path `document_id`; optional query `expose_facets=true|false`. | Document JSON. | `expose_facets=true` includes tensor facets when supported and may increase response size. |
| `GET /indexes/{index_name}/documents` | Get multiple documents. | JSON list body of document IDs in the current route contract; optional query `expose_facets=true|false`. | Batch get response with `results`, `errors`, and count headers. | The POST batch route is usually clearer for tooling. |
| `POST /indexes/{index_name}/documents/get-batch` | Get multiple documents via explicit batch body. | `GetBatchDocumentsRequest`: `{"documentIds": ["doc-1", "doc-2"]}`; optional query `expose_facets=true|false`. | Same batch get response as the GET variant. | `documentIds` must be a non-empty list of strings. |
| `POST /indexes/{index_name}/documents/delete-batch` | Delete selected documents. | JSON list body of document IDs. | Deletion response with `index_name`, `status`, `type`, `items`, `details`, and timestamps. | Deleting a missing ID may still be reported as backend-success depending on backend behavior. |
| `POST /indexes/{index_name}/embed` | Embed content using the index model. | `EmbedRequest`: `content`, optional `contentType`, `mediaDownloadHeaders`, deprecated `imageDownloadHeaders`, `modelAuth`. | `content`, `embeddings`, `processingTimeMs`. | `content` can be a string, weighted dict, or list of those. `contentType` is `query` or `document`. |
| `POST /indexes/{index_name}/recommend` | Recommend documents from existing document vectors. | `RecommendQuery`: `documents` plus optional tensor/search attributes, interpolation, flags, paging, and filters. | Search-like response with `hits`. | This route reuses indexed vectors; scoring/ranking details belong in `search-and-ranking`. |
| `POST /indexes/{index_name}/search` | Search route entry point. | `SearchQuery` body. | Search response with `hits`, timings, and optional highlights/facets. | This sub-skill covers only route-level validation and smoke shape. Detailed search/ranking behavior belongs in `search-and-ranking`. |

### Typeahead routes

| Method and path | Purpose | Request shape | Success response shape | Notes |
|---|---|---|---|---|
| `POST /indexes/{index_name}/suggestions` | Fetch typeahead suggestions. | `TypeaheadRequest`: `q`, optional `limit`, `fuzzyEditDistance`, `minFuzzyMatchLength`, `popularityWeight`, `bm25Weight`, `matchAllTokens`. | `TypeaheadResponse`: `suggestions`, `processingTimeMs`. | Empty `q` is allowed and returns top indexed queries. |
| `POST /indexes/{index_name}/suggestions/queries` | Index typeahead query strings. | `TypeaheadIndexingRequest`: `{"queries": [{"query": "...", "popularity": 1.0, "metadata": {}}]}`. | `TypeaheadIndexingResponse`: `indexed`, `errors`, `processingTimeMs`. | Empty query batches are rejected; duplicate normalized queries are ignored with per-item errors. |
| `GET /indexes/{index_name}/suggestions/queries` | Fetch exact indexed typeahead queries. | JSON list body of query strings. | `TypeaheadGetQueriesResponse`: `queries`. | Returned query objects use aliases such as `queryWords` and `lastUpdatedAt`. |
| `DELETE /indexes/{index_name}/suggestions/queries` | Delete selected typeahead queries. | JSON list body of query strings. | JSON string `"Queries deleted successfully"`. | Query strings are normalized and hashed before backend deletion. |
| `GET /indexes/{index_name}/suggestions/stats` | Count indexed typeahead queries. | No body. | `{"indexedQueries": <int>}`. | Non-mutating. |
| `DELETE /indexes/{index_name}/suggestions/queries/delete-all` | Delete all typeahead queries. | No body. | JSON string `"All queries deleted successfully"`. | Batch-gated; see route gates below. |

## Request model quick map

| Model | Where used | Important fields and aliases |
|---|---|---|
| `IndexSettings` | `POST /indexes/{index_name}` | `type`, `allFields`, `tensorFields`, `model`, `modelProperties`, `normalizeEmbeddings`, preprocessing blocks, `treatUrlsAndPointersAsMedia`. Snake_case keys are rejected in create-index payloads; use public camelCase. |
| `AddDocsBodyParams` | Add documents | Required `documents`; optional `tensorFields`, `mappings`, `mediaDownloadHeaders`, deprecated `imageDownloadHeaders`, `modelAuth`, thread counts, `textChunkPrefix`. Unknown fields are forbidden. |
| `UpdateDocumentsBodyParams` | Partial update | Required `documents`; rejects empty batches and batches over the configured maximum. |
| `GetBatchDocumentsRequest` | POST get-batch | `documentIds` is a non-empty list of strings. |
| `EmbedRequest` | Embed | `content`, `contentType`, `mediaDownloadHeaders`, deprecated alias `image_download_headers`, `modelAuth`. Empty content lists/dicts are rejected. |
| `RecommendQuery` | Recommend | Required `documents`; optional `tensorFields`, `interpolationMethod`, paging, highlights, filters, `attributesToRetrieve`, `scoreModifiers`, `allowMissingDocuments`, `allowMissingEmbeddings`. |
| `SearchQuery` | Search | `q`, `searchMethod`, paging, `context`, `hybridParameters`, media/model auth and many ranking fields. This sub-skill only covers common validation errors and route shape. |
| `TypeaheadRequest` | Suggestions | `q` required; `limit > 0`; `fuzzyEditDistance >= 0`; `minFuzzyMatchLength >= 0`; optional ranking weights and `matchAllTokens`. |
| `TypeaheadIndexingRequest` | Typeahead query indexing | `queries` list of `{query, popularity, metadata}`; `query` must be non-empty after stripping; batch size is capped. |

## Response and error handling

Marqo API responses use two broad error forms:

| Source | HTTP status | Body shape | How to triage |
|---|---:|---|---|
| FastAPI request validation | `422` | `{"detail": [...], "code": ..., "type": ..., "link": ...}` | The body shape, field alias, or primitive type is wrong before Marqo core logic runs. Inspect `detail[*].loc` and `detail[*].msg`. |
| Pydantic model validation converted to API error | Usually `400` | `{"message": "[...]", "code": ..., "type": ..., "link": ...}` | A request model or custom validator rejected a combination, e.g. bad search query, empty batch, or conflicting media headers. |
| Marqo web error | Route-specific status | `{"message": "...", "code": ..., "type": "...", "link": ...}` | Use `type` and `message`; common examples include invalid argument, index not found, invalid field name, operation conflict, backend communication, or service unavailable. |
| Internal API error | `500` | `{"message": "...", "code": 500, "type": "internal_error", "link": ""}` | Treat as unexpected unless the call targeted an internal/gated route or backend dependencies are unhealthy. |

Batch document responses often include count headers: `x-count-success`, `x-count-failure`, and `x-count-error`. A `200` response can still contain per-item failures; always inspect both headers and body.

## Route gates and internal routes

The API includes hidden or operational routes that should not be used as ordinary public workflows. When disabled, gated routes return `403` with a message naming the required environment variable.

| Gate | Enable variable | Routes affected |
|---|---|---|
| Batch APIs | `MARQO_ENABLE_BATCH_APIS=true` | `POST /batch/indexes/create`, `POST /batch/indexes/delete`, `DELETE /indexes/{index_name}/documents/delete-all`, `DELETE /indexes/{index_name}/suggestions/queries/delete-all`. |
| Upgrade APIs | `MARQO_ENABLE_UPGRADE_API=true` | `POST /upgrade`, `POST /rollback`. |
| Debug APIs | `MARQO_ENABLE_DEBUG_API=true` | `GET /memory`. |
| Ops APIs | `MARQO_ENABLE_OPS_API=true` | `POST /indexes/{index_name}/apply-latest-schema-template`, `PATCH /indexes/{index_name}/index-settings`, `POST /validate/index/{index_name}`. |

Treat operational routes as explicit-maintenance actions. Do not include them in default smoke checks. The service also exposes an operational `POST /rollback-vespa` route in the current route table; handle it as maintenance/destructive even though it is not part of the public document/typeahead smoke workflow.
