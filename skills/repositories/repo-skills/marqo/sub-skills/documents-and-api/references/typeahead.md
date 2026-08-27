# Typeahead API

Marqo typeahead stores query strings in an index-specific suggestions schema and serves prefix/fuzzy suggestions. This reference covers HTTP request shapes, model aliases, response structures, and common mistakes.

## Feature and schema notes

- Typeahead requires an index whose schema supports the typeahead feature. Current evidence shows the feature gate at Marqo schema version `2.23.0` or newer.
- Query strings are normalized before indexing and lookup: accents are removed and text is lowercased.
- Prefixes are generated per token. For example, a token contributes incremental prefixes such as `m`, `ma`, `mar`, `marq`, `marqo`.
- During lookup, tokens shorter than `minFuzzyMatchLength` use exact prefix matching; longer tokens can use fuzzy matching with `fuzzyEditDistance`.
- `matchAllTokens=false` joins token retrieval with OR logic; `matchAllTokens=true` requires all tokens.
- Empty suggestion query `q: ""` is valid and returns the top indexed queries, usually ordered by ranking features such as popularity.

## Route summary

| Method and path | Purpose | Body |
|---|---|---|
| `POST /indexes/{index_name}/suggestions/queries` | Index query strings into the typeahead store. | `{"queries": [{"query": "...", "popularity": 1.0, "metadata": {}}]}` |
| `POST /indexes/{index_name}/suggestions` | Return suggestions for a partial user query. | `{"q": "mar", "limit": 10}` plus optional fuzzy/ranking controls. |
| `GET /indexes/{index_name}/suggestions/queries` | Fetch exact indexed query records. | JSON list body, e.g. `["marqo api smoke"]`. |
| `DELETE /indexes/{index_name}/suggestions/queries` | Delete selected indexed query records. | JSON list body, e.g. `["marqo api smoke"]`. |
| `GET /indexes/{index_name}/suggestions/stats` | Count indexed typeahead queries. | No body. |
| `DELETE /indexes/{index_name}/suggestions/queries/delete-all` | Delete all indexed typeahead queries. | No body; requires `MARQO_ENABLE_BATCH_APIS=true`. |

## Request and response models

### `TypeaheadRequest`

Used by `POST /indexes/{index_name}/suggestions`.

| Field | Required | Default | Validation / behavior |
|---|---:|---:|---|
| `q` | Yes | None | Partial user query. Empty string is allowed and returns top queries. |
| `limit` | No | `10` | Must be greater than `0`. |
| `fuzzyEditDistance` | No | `2` | Must be `>= 0`. Used for tokens at or above `minFuzzyMatchLength`. |
| `minFuzzyMatchLength` | No | `3` | Must be `>= 0`. Shorter tokens use exact prefix matching. |
| `popularityWeight` | No | `null` | Adds a popularity ranking feature when provided. |
| `bm25Weight` | No | `null` | Adds a BM25/exact-match ranking feature when provided. |
| `matchAllTokens` | No | `false` | `true` switches token retrieval from OR to AND. |

Response shape:

```json
{
  "suggestions": [
    {"suggestion": "marqo api smoke", "_score": 0.95, "metadata": {"source": 1.0}}
  ],
  "processingTimeMs": 25
}
```

### `TypeaheadIndexingRequest`

Used by `POST /indexes/{index_name}/suggestions/queries`.

| Field | Required | Default | Validation / behavior |
|---|---:|---:|---|
| `queries` | Yes | None | Non-empty list, capped by the configured maximum document batch size. |
| `queries[*].query` | Yes | None | Trimmed; must not be empty after stripping. |
| `queries[*].popularity` | No | `0.0` | Numeric popularity value. |
| `queries[*].metadata` | No | `{}` | String-to-float map for additional ranking metadata. |

Indexing response shape:

```json
{
  "indexed": 2,
  "errors": [],
  "processingTimeMs": 80
}
```

Per-query errors use:

```json
{"query": "bad query", "message": "Invalid query", "code": 400}
```

Duplicate queries after normalization are not indexed twice. For example, `"Café"` and `"cafe"` normalize to the same key; later duplicates can appear in the `errors` list.

### `TypeaheadGetQueriesResponse`

Used by `GET /indexes/{index_name}/suggestions/queries`.

```json
{
  "queries": [
    {
      "query": "marqo api smoke",
      "queryWords": ["marqo", "api", "smoke"],
      "queryIndex": "m ma mar marq marqo a ap api s sm smo smok smoke",
      "popularity": 10.0,
      "metadata": {"source": 1.0},
      "lastUpdatedAt": 1234567890
    }
  ]
}
```

### `TypeaheadStatsResponse`

Used by `GET /indexes/{index_name}/suggestions/stats`.

```json
{"indexedQueries": 5}
```

## End-to-end workflow

1. Create or choose a typeahead-capable index.
2. Index query strings:

   ```http
   POST /indexes/{index_name}/suggestions/queries
   Content-Type: application/json

   {
     "queries": [
       {"query": "machine learning algorithms", "popularity": 10.0, "metadata": {"hit_count": 3.0}},
       {"query": "machine learning basics", "popularity": 8.0},
       {"query": "deep learning", "popularity": 7.0}
     ]
   }
   ```

3. Check stats:

   ```http
   GET /indexes/{index_name}/suggestions/stats
   ```

4. Query suggestions:

   ```http
   POST /indexes/{index_name}/suggestions
   Content-Type: application/json

   {"q": "machine", "limit": 5, "fuzzyEditDistance": 2, "minFuzzyMatchLength": 3}
   ```

5. Fetch exact stored query records when debugging:

   ```http
   GET /indexes/{index_name}/suggestions/queries
   Content-Type: application/json

   ["machine learning algorithms", "deep learning"]
   ```

6. Delete selected typeahead queries when cleaning up:

   ```http
   DELETE /indexes/{index_name}/suggestions/queries
   Content-Type: application/json

   ["machine learning algorithms", "deep learning"]
   ```

## Common mistakes

| Symptom | Likely cause | Fix |
|---|---|---|
| `422` with missing `q` | Suggestions request did not include required `q`. | Send `{"q": "..."}`. Use `q: ""` for top suggestions. |
| `422` for `limit` | `limit` was not an integer or was `<= 0`. | Use a positive integer. |
| `422` or `400` while indexing | `queries` is missing, not a list, too large, or contains non-object entries. | Send a non-empty list of query objects and keep it below the batch limit. |
| `query is required and must not be an empty string` | A query object had empty/whitespace `query`. | Strip or drop empty queries before indexing. |
| No suggestions for expected prefix | Query strings were never indexed, normalized differently, or indexed into another index. | Check stats, fetch exact query records, and remember normalization removes accents and lowercases. |
| Duplicate query not added twice | Two input queries normalized to the same string. | This is expected; keep one canonical query and use metadata/popularity for ranking hints. |
| Delete-all returns `403` | The batch-gated delete-all route is disabled. | Enable `MARQO_ENABLE_BATCH_APIS=true` only for explicit destructive maintenance; otherwise delete selected queries. |
| Feature unsupported error | Index schema predates typeahead support. | Recreate or upgrade the index through the appropriate index/Vespa workflow. |
