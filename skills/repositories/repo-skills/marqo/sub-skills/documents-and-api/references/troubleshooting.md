# Documents and API troubleshooting

Start with the HTTP status code and body shape, then identify whether the failure happened at the service connection layer, FastAPI/Pydantic request validation, Marqo validation, or backend/model/media execution.

## Fast triage table

| Symptom | Likely layer | What to check |
|---|---|---|
| Connection refused, DNS failure, timeout before status code | Service unavailable or wrong `base-url` | Confirm the Marqo API is listening at the requested host/port. Start with `GET /` and `GET /health`. |
| `403` and message says an API endpoint is disabled | Route gate | Check whether the route is batch, upgrade, debug, or ops-gated. Do not bypass unless the task explicitly calls for that internal operation. |
| `422` with `detail` list | FastAPI request validation | Wrong field name, wrong JSON primitive type, missing required body field, or a body/query mismatch. Inspect `detail[*].loc` and `detail[*].msg`. |
| `400` with Marqo error envelope | Request-model or Marqo validation | Empty batch, bad document ID, invalid field name, conflicting media headers, bad search query combination, typeahead batch issue, or model-auth shape error. |
| `404` index/document not found | Resource state | Check the target `index_name`, document ID, or whether a previous create/add call failed. |
| `409` operation conflict | Concurrent index/backend operation | Retry after deployment/index operation completes; avoid overlapping schema/index operations. |
| `5xx` backend communication or timeout | Vespa/inference/backend issue | Health-check the service and route to `index-and-vespa`, `inference-and-models`, or `local-development` depending on the failing dependency. |

## Unavailable service

Use the smoke script without network first:

```bash
python scripts/marqo_http_smoke.py --base-url http://localhost:8882 --index-name smoke --print-only
```

Then test a live service only when intended:

```bash
python scripts/marqo_http_smoke.py --base-url http://localhost:8882 --index-name smoke --send
```

If `--send` reports the service is unreachable:

1. Confirm the base URL and port.
2. Try `GET /` and `GET /health` directly.
3. If the API process/container is not running, route to `local-development` for startup/container guidance.
4. If health shows backend or inference unhealthy, route to the owning backend sub-skill rather than retrying payload changes blindly.

## Disabled route gates

A disabled gate returns `403` and a message naming the required variable.

| Gate family | Enable variable | Examples | Safe response |
|---|---|---|---|
| Batch APIs | `MARQO_ENABLE_BATCH_APIS=true` | Batch index create/delete, delete all documents, delete all typeahead queries. | Prefer selected document/query deletes. Enable only for explicit destructive maintenance. |
| Upgrade APIs | `MARQO_ENABLE_UPGRADE_API=true` | Upgrade and rollback. | Route to maintenance/local-development planning. |
| Debug APIs | `MARQO_ENABLE_DEBUG_API=true` | Memory profiling. | Avoid in public smoke; enable only for debug sessions. |
| Ops APIs | `MARQO_ENABLE_OPS_API=true` | Schema-template update, index-settings patch, schema validation. | Route to `index-and-vespa` before use. |

Do not treat a gated `403` as a missing route. It is an intentionally disabled internal/ops surface.

## Invalid JSON and Pydantic validation

Common `422` causes:

- Body is not valid JSON or lacks `Content-Type: application/json` for routes expecting JSON.
- Public aliases are wrong: use `documentIds`, `contentType`, `fuzzyEditDistance`, `minFuzzyMatchLength`, `popularityWeight`, `bm25Weight`, `allowMissingDocuments`, and `allowMissingEmbeddings` where applicable.
- Create-index payload used snake_case keys. Public create-index settings use camelCase.
- `GET` or `DELETE` routes that take JSON list bodies were called without a body.
- A list field was sent as an object/string, e.g. `documentIds: {}` or `queries: "not a list"`.
- Numeric fields such as typeahead `limit`, `popularity`, or fuzzy parameters were sent as strings.

Common Marqo validation (`400`) causes:

- Empty add/update/typeahead batch.
- Batch size exceeds configured maximum.
- Search query has a disallowed combination.
- `imageDownloadHeaders`/`image_download_headers` and `mediaDownloadHeaders` are both set.
- `modelAuth` is empty or includes more than one auth family.

## Bad document IDs and field names

Document ID rules:

- If `_id` is supplied, it must be a non-empty string.
- Integer IDs such as `4` fail even if the visual ID looks simple; send `"4"`.
- Partial update requires `_id` for each document.
- Get/delete calls target IDs as strings.

Document and field rules:

- Each document must be a non-empty object.
- Documents must be JSON-serializable.
- A configured maximum document byte size can raise a document-too-large error.
- Field names must be strings and cannot be empty.
- Field names cannot start with protected prefixes such as `__vector_` or protected names such as `__chunks`.
- Protected output/internal fields such as `_score`, `_highlights`, `_tensor_facets`, and `_embedding` should not be used as customer field names.
- Flexible-index list fields must contain only one primitive type among string, int, or float; mixed-type lists are rejected.
- Object/dict fields are interpreted as map fields, custom-vector fields, or multimodal-combination fields depending on schema/mappings; invalid nested or non-numeric map values are rejected.

## Add/update/get response counts

A `200` can still contain partial failures. Inspect:

- `x-count-success`
- `x-count-failure`
- `x-count-error`
- per-item `status`, `_id`, and `error` fields in the response body

Example: a batch with three valid string IDs and one integer `_id` can return HTTP `200` with one per-item failure.

## Embed, recommend, media, and model authentication

Embed route issues:

- `content` must be a string, a non-empty string-to-float dictionary, or a list of those. Empty lists/dicts are rejected.
- `contentType` is `query` by default; use `document` when embedding content as document/chunk text.
- Private image/media URLs need `mediaDownloadHeaders`. Deprecated `imageDownloadHeaders` may be accepted alone and copied into `mediaDownloadHeaders`, but sending both is rejected.
- Private models need `modelAuth`; exactly one auth family such as `hf` or `s3` must be present.
- Model download/auth failures can appear as invalid-argument or model errors. Confirm the model name, auth block, and whether the service can reach model storage.

Recommend route issues:

- `documents` must identify indexed documents that have stored embeddings for the requested tensor fields.
- If input documents are missing or lack embeddings and the corresponding `allowMissing...` flags are false, recommendation fails.
- Recommend generally reuses stored vectors rather than downloading a model for the recommendation call itself. If failures mention models or private media, check the original indexing/embed step and model/index configuration.
- Ranking and scoring interpretation belongs in `search-and-ranking`.

## Media/image headers

Use these rules for add-docs, embed, and minimal search-route triage:

- Prefer `mediaDownloadHeaders` for all media types.
- Treat `imageDownloadHeaders` and `image_download_headers` as legacy aliases.
- Never provide a legacy image header and `mediaDownloadHeaders` in the same request.
- If a private image URL returns `403` or cannot be downloaded, the document item or embed call fails with a media download error.
- For containerized deployments, ensure the URL is reachable from the Marqo service process, not only from the caller's shell/browser.

## Typeahead indexing/query mistakes

| Mistake | Signal | Fix |
|---|---|---|
| Missing `q` in suggestions request | `422` detail mentions `q`. | Send `{"q": "prefix"}`. Empty `q` is allowed for top queries. |
| `limit <= 0` or string limit | `422` detail mentions `limit`. | Use a positive integer. |
| Empty `queries` batch | Marqo error says empty index queries request. | Drop the request or provide at least one query object. |
| Query object has no `query` | `422` detail mentions missing `query`. | Include a string `query`. |
| Query string is empty/whitespace | Validation message says query must not be empty. | Strip and filter empty query strings before indexing. |
| Duplicate suggestions after normalization | Per-item error says duplicate after normalization. | Keep one canonical query and adjust popularity/metadata. |
| No suggestions for expected prefix | Stats are zero, wrong index, old schema, or normalization mismatch. | Check stats, fetch exact queries, and remember lowercasing/accent stripping. |
| Delete-all is forbidden | `403` batch-gate message. | Use selected delete or deliberately enable the batch API gate. |

## Search payload triage at the API boundary

Use this section only for request-shape errors. Route deeper search behavior to `search-and-ranking`.

Common invalid search payloads:

- Lexical search without `q`.
- Tensor search with neither `q` nor valid `context`.
- `q` as an integer, list, set, or empty dictionary.
- Dictionary `q` with non-string keys or non-numeric values.
- Dictionary `q` used with lexical search.
- Dictionary `q` used directly with hybrid search instead of `hybridParameters.queryTensor`.
- `hybridParameters` supplied when `searchMethod` is not `HYBRID`.
- `facets`, recency parameters, or total-hit tracking supplied outside hybrid search.
- Negative `rerankDepth`, or `rerankDepth` with lexical search.
- Conflicting `imageDownloadHeaders` and `mediaDownloadHeaders`.

When a payload fails, reduce it to this minimal shape and add parameters back one at a time:

```json
{"q": "smoke query", "searchMethod": "TENSOR", "limit": 3}
```
