# Search API and Response Shape

## Endpoint

`GET /api/search` returns a JSON list of `SearchResponse` objects for the authenticated user.

Query parameters:

| Parameter | Type | Default | Meaning |
| --- | --- | --- | --- |
| `q` | string, required | none | Natural-language query plus optional filter tokens. Empty or missing queries return no results. |
| `n` | integer | `5` | Number of results returned after collation, sorting, and slicing. Internally each text search asks the adapter for up to `10` candidates before final slicing. |
| `t` | enum | `all` | Search type/content type selector. |
| `r` | boolean | `false` | Request cross-encoder reranking. Reranking can also occur when the configured cross-encoder inference server is enabled and there is more than one result. |
| `max_distance` | float or null | route passes infinity when omitted | Maximum cosine distance accepted from the vector query. Lower means stricter semantic similarity. |
| `dedupe` | boolean | `true` | Remove repeated results with the same `corpus_id` or hashed content during initial collation. |

`/api/search` requires an authenticated request. The route extracts `request.user.object` and searches that user's entries. Internal helper calls can also supply an `agent`; if both `user` and `agent` are provided, the agent must be accessible by the user.

## SearchType Values

The enum values are:

- `all`
- `org`
- `markdown`
- `image`
- `pdf`
- `github`
- `notion`
- `plaintext`
- `docx`

Text search maps these values to database entry types for `org`, `markdown`, `plaintext`, `pdf`, `github`, and `notion`; `all` searches all text entry types. `image` is not routed through text embedding search. `docx` exists in the enum, but the observed text-search branch does not include it in the same text query list.

## Execution Flow

1. Strip and validate `q`; empty input returns `[]`.
2. Build a user-scoped query-cache key from query text, `n`, `t`, `r`, `max_distance`, and `dedupe`.
3. Remove date, word, and file filters from the text that is embedded.
4. Embed the defiltered natural-language query using the configured default search model.
5. Search the entry table with owner isolation, filter predicates, content-type filter, vector distance annotation, and `distance <= max_distance`.
6. Collate raw database hits into `SearchResponse` objects; optionally dedupe by hash or `corpus_id`.
7. Sort by bi-encoder distance and optionally cross-encoder score; slice to `n` results.
8. Cache user-scoped results when a user is present.

## Response Fields

Each result has this shape:

```json
{
  "entry": "matched raw entry text",
  "score": 0.123,
  "cross_score": 0.456,
  "additional": {
    "source": "content source",
    "file": "path or source identifier",
    "uri": "file://... or URL when known",
    "compiled": "compiled text used for embedding/reranking",
    "heading": "nearest heading when known"
  },
  "corpus_id": "entry corpus id as a string"
}
```

`cross_score` is optional and appears when reranking adds it. `score` is the vector distance; smaller is better. When reranking is active, Khoj stores `cross_score` as `1 - model_score`, so smaller is still better.

Chat-side search can attach `additional.query` before deduplicating across inferred queries. Plain `/api/search` results should not be assumed to include `additional.query`.

## Collation, Dedupe, and Reranking

Initial collation skips a hit when `dedupe=true` and either its content hash or `corpus_id` was already seen. With `dedupe=false`, repeated chunks can be returned if they pass filters and distance checks.

Reranking is active when either:

- request parameter `r=true`, or
- the configured cross-encoder has both an API key and inference endpoint, and more than one hit is present.

Sorting always starts with bi-encoder `score`; when reranking is active, a second sort by `cross_score` makes cross-encoder distance primary. If cross-encoder inference raises an HTTP error, Khoj logs the failure, assigns all cross scores to `0.0`, and still returns bi-encoder-backed results.
