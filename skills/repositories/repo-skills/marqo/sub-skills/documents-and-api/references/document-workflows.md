# Document, embed, recommend, and route-level search workflows

Use these workflows for HTTP payload construction and validation triage. They are intentionally service-facing: they do not explain Vespa schema generation, ranking algorithms, model runtime internals, or local startup commands.

## 1. Create an index for document API smoke work

For new generic HTTP smoke checks, prefer a semi-structured index and a small no-download model when the running Marqo build supports it:

```json
{
  "type": "semi-structured",
  "model": "random/small"
}
```

Alternative patterns:

| Pattern | Create-index settings | Document add behavior |
|---|---|---|
| Text-only notebook or wiki ingestion | `type: "semi-structured"` or the current default, text model already available in the service. | Add title/content fields and set `tensorFields` on the add-docs request for flexible indexes. |
| Structured catalog | `type: "structured"`, explicit `allFields`, and explicit `tensorFields`. | Add documents without `tensorFields`; the index schema declares them. |
| Image/media catalog | Media-capable model such as an OpenCLIP model, and `treatUrlsAndPointersAsMedia: true` for flexible indexes. | Add URL or pointer fields as tensor fields; include `mediaDownloadHeaders` for private assets. |
| Legacy unstructured examples | Older examples use `type: "unstructured"` or client defaults. | Translate the idea to semi-structured for new smoke work unless compatibility with a legacy index is the goal. |

Distilled example patterns:

- Clothing-style image demo: create a media-aware index, store image URLs plus labels, and add both image and text fields as tensor fields.
- Simple-wiki text demo: normalize and split very large text records before add-docs, then index `title` and `content` as tensor fields.
- Podcast transcript demo: assign stable string `_id` values, index `name`, `description`, and transcript text fields, then read highlights from search results.

## 2. Add or replace documents

Route:

```http
POST /indexes/{index_name}/documents
```

Minimal flexible-index payload:

```json
{
  "documents": [
    {
      "_id": "doc-1",
      "title": "Marqo API smoke",
      "text": "Documents can be added and read back.",
      "category": "demo"
    },
    {
      "_id": "doc-2",
      "title": "Typeahead smoke",
      "text": "Typeahead query examples use separate suggestion routes.",
      "category": "demo"
    }
  ],
  "tensorFields": ["title", "text"]
}
```

Useful optional fields:

| Field | When to use | Validation notes |
|---|---|---|
| `tensorFields` | Flexible indexes where the add request chooses tensorized fields. | Do not pass for structured indexes; use the index schema's `tensorFields` instead. |
| `useExistingTensors` | Reuse supplied tensor facets rather than re-embedding. | Only use when the document vector payload is intentionally supplied and valid. |
| `mappings` | Object fields such as custom vectors or multimodal combinations. | Field names and mapping types are validated strictly. |
| `mediaDownloadHeaders` | Private image/audio/video URLs or media pointers. | Preferred over deprecated `imageDownloadHeaders`; do not send both. |
| `modelAuth` | Private model artifacts, e.g. private HF or S3 locations. | Must specify exactly one auth family such as `hf` or `s3`. |
| `imageDownloadThreadCount` / `mediaDownloadThreadCount` | Request-level media download parallelism. | Do not set both thread-count forms at once. |
| `textChunkPrefix` | Override text prefix for document chunks. | Model and inference details belong in `inference-and-models`. |

Always inspect the response body and count headers. A successful HTTP status can include per-item failures such as invalid `_id`, unsupported field type, media download failure, or structured-field mismatch.

## 3. Partially update documents

Route:

```http
PATCH /indexes/{index_name}/documents
```

Payload:

```json
{
  "documents": [
    {"_id": "doc-1", "category": "updated-demo"}
  ]
}
```

Rules:

- Each update document needs a valid string `_id`.
- Empty batches are rejected.
- Batches larger than the configured maximum are rejected.
- Structured indexes validate updated field types against the index schema.
- Count headers identify how many updates succeeded, failed, or errored.

## 4. Read documents

Get one:

```http
GET /indexes/{index_name}/documents/{document_id}
```

Get batch via explicit JSON object:

```http
POST /indexes/{index_name}/documents/get-batch
Content-Type: application/json

{"documentIds": ["doc-1", "doc-2"]}
```

The GET batch route currently accepts a JSON list body of IDs, but the POST batch route is easier for generic tooling because the body has a named `documentIds` field.

Use `?expose_facets=true` only when tensor facet vectors are needed. It increases response size and can expose internal vector/debug information that is unnecessary for ordinary reads.

## 5. Delete documents

Route:

```http
POST /indexes/{index_name}/documents/delete-batch
Content-Type: application/json

["doc-1", "doc-2"]
```

The response is a deletion report with the index name, operation status, per-document items, and received/deleted counts. Backend behavior may report a successful delete operation even if a document ID did not exist.

For deleting every document, there is an internal batch-gated route. Use it only when `MARQO_ENABLE_BATCH_APIS=true` has deliberately been set and the task is explicitly destructive.

## 6. Embed content

Route:

```http
POST /indexes/{index_name}/embed
```

Request body examples:

```json
{"content": "a query to embed", "contentType": "query"}
```

```json
{
  "content": [
    "first document chunk",
    {"weighted term": 1.0, "second term": 0.5}
  ],
  "contentType": "document"
}
```

Rules:

- `content` can be a string, a weighted dictionary of string-to-float, or a list of those shapes.
- Empty lists and empty dictionaries are rejected.
- `contentType` is `query` by default. Use `document` when the vector should use the index model's document/chunk prefix.
- Private media or model artifacts require the appropriate `mediaDownloadHeaders` or `modelAuth` block.
- Do not send deprecated `imageDownloadHeaders` together with `mediaDownloadHeaders`.

## 7. Recommend from existing documents

Route:

```http
POST /indexes/{index_name}/recommend
```

Minimal request:

```json
{"documents": ["doc-1", "doc-2"], "limit": 5}
```

Useful route-level fields:

| Field | Meaning |
|---|---|
| `documents` | Required list of document IDs or a map of IDs to weights. |
| `tensorFields` | Restrict which stored tensor fields are used. |
| `excludeInputDocuments` | Defaults to `true`; avoids returning the input documents as recommendations. |
| `limit`, `offset` | Pagination. |
| `allowMissingDocuments`, `allowMissingEmbeddings` | When `false`, missing input docs or missing vectors cause an error. |

Recommendation quality, interpolation, filters, reranking, score modifiers, and search/ranking trade-offs belong in `search-and-ranking`. This sub-skill only records the HTTP route and request-model mechanics.

## 8. Minimal search-route validation triage

Search is primarily owned by `search-and-ranking`, but route-level validation failures often surface while exercising document workflows. Use these checks before escalating:

```http
POST /indexes/{index_name}/search
Content-Type: application/json

{"q": "smoke query", "searchMethod": "TENSOR", "limit": 3}
```

Common request-shape rules:

- `searchMethod` is case-normalized but must be one of `TENSOR`, `LEXICAL`, or `HYBRID`.
- `q` can be a string, a string-to-number dictionary, `null` when a valid tensor context is supplied, or a custom-vector query object.
- Dictionary `q` is valid for tensor search, rejected for lexical search, and must move under `hybridParameters.queryTensor` for hybrid search.
- `hybridParameters`, facets, recency controls, and total-hit tracking are hybrid-only; detailed semantics are not covered here.
- `rerankDepth` is rejected for lexical search and must not be negative.
- `imageDownloadHeaders`/`image_download_headers` and `mediaDownloadHeaders` are mutually exclusive.

## 9. Safe smoke generation

Use the bundled script to preview the route sequence without network:

```bash
python scripts/marqo_http_smoke.py --index-name documents-and-api-smoke --print-only
```

Use `--send` only against a Marqo API service you intend to mutate:

```bash
python scripts/marqo_http_smoke.py --base-url http://localhost:8882 --index-name my-smoke-index --send
```

The send sequence creates the named index, adds/updates/reads/deletes sample documents, exercises embed/recommend/search/typeahead routes, and deletes the index at the end. Use a fresh index name to avoid create-index conflicts.
