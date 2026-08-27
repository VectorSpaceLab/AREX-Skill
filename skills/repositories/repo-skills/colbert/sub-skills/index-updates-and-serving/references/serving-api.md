# Serving API

## Source behavior to preserve deliberately

ColBERT's lightweight server pattern exposes a `GET /api/search` endpoint returning ranked JSON for one query. It reads `INDEX_ROOT`, `INDEX_NAME`, and `PORT` from environment variables and caps user-visible `k` at 100.

The source pattern also constructs `Searcher(index=INDEX_NAME, index_root=INDEX_ROOT)` at module import time. Avoid that in generated or adapted services because import-time construction makes `--help`, tests, and config error reporting fail before the server can validate arguments.

## Safer API shape

Use explicit CLI arguments with environment fallback:

```bash
python scripts/serve_search_api.py \
  --index-name my-index \
  --index-root /indexes \
  --collection collection.tsv \
  --checkpoint checkpoint-or-model \
  --port 8893
```

Equivalent environment variables are useful for containers:

```bash
INDEX_NAME=my-index INDEX_ROOT=/indexes PORT=8893 python scripts/serve_search_api.py
```

Recommended endpoint:

```text
GET /api/search?query=Who%20won%20the%202022%20FIFA%20world%20cup&k=25
```

Recommended success response:

```json
{
  "query": "Who won the 2022 FIFA world cup",
  "topk": [
    {"text": "...", "pid": 123, "rank": 1, "score": 17.4, "prob": 0.8}
  ]
}
```

Recommended error response:

```json
{"error": "missing required configuration: index_name"}
```

Use HTTP 400 for bad request parameters, HTTP 503 for index/searcher initialization errors, and HTTP 500 only for unexpected runtime failures.

## Lazy Searcher creation

Create the Flask app without constructing a `Searcher`. Create the `Searcher` lazily on the first request or through an explicit startup path after arguments are parsed.

Benefits:

- `python scripts/serve_search_api.py --help` works without ColBERT, Flask, or an index.
- Missing `INDEX_ROOT` or `INDEX_NAME` can return a clear JSON error instead of crashing at import time.
- Unit/synthetic tests can import `create_app` safely.
- Reload behavior can be controlled by creating a new process after index updates.

## k cap and probabilities

The public server caps `k` at 100 and runs search with enough results to slice the requested top-k. Keep the cap unless there is an explicit performance review.

When converting scores to probabilities, protect against empty results and numeric overflow. A stable softmax over scores is safer than directly exponentiating large scores.

## Searcher reload behavior

A long-running server holds a `Searcher` instance in memory. If another process calls `IndexUpdater.persist_to_disk()` on the same index directory, the server should not be assumed to see a consistent updated state.

Safe options:

- Restart the server after the updated index directory is fully written.
- Serve from immutable versioned index directories and switch traffic to a new server process.
- Add an explicit admin-only reload endpoint only if the deployment can prevent reloads during partial writes.

The bundled `serve_search_api.py` intentionally avoids an unsafe public mutation or reload endpoint.

## Minimal health checks

Expose a simple `/healthz` endpoint that reports whether required configuration exists and whether the `Searcher` has already been initialized. Avoid loading the index merely for a health check unless the deployment wants startup probes to fail on index load errors.

Example response:

```json
{"ok": true, "configured": true, "searcher_loaded": false}
```
