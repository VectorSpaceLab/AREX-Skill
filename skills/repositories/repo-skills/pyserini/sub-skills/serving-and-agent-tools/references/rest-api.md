# REST API

Pyserini REST exposes a FastAPI service aligned with Anserini's REST API. It serves package-bundled OpenAPI at `/openapi.yaml`, Swagger UI at `/docs`, and GET-only `/v1` search/document routes.

## Start the Server

```bash
python -m pyserini.server.rest
python -m pyserini.server.rest --host 127.0.0.1 --port 8081 --config server.yaml
python -m pyserini.server.rest --host 127.0.0.1 --port 8081 --config server.yaml --no-prebuilt-indexes
```

Defaults are host `0.0.0.0` and port `8081`. Use `127.0.0.1` for local-only development.

## Discovery URLs

| URL | Purpose |
| --- | --- |
| `/` | JSON metadata with server name, version, OpenAPI path, and docs path. |
| `/openapi.yaml` | Bundled OpenAPI 3.1 document. |
| `/openapi.json` | FastAPI schema generated from the bundled OpenAPI schema. |
| `/docs` | Swagger UI. |

## Index Path Resolution

The `{index}` path component in `/v1/{index}/...` is resolved in this order:

1. Alias from `--config`, when a config file is supplied.
2. Existing local index directory path, unless `--no-prebuilt-indexes` is set.
3. Known Pyserini prebuilt index name, unless `--no-prebuilt-indexes` is set.

When `--no-prebuilt-indexes` is set, only configured aliases are accepted. This is the safest mode for shared deployments.

`{index}` may contain slashes. For a relative path, call a URL like `/v1/project/indexes/demo/search`. For an absolute path, preserve the leading slash with an extra slash after `/v1`, such as `/v1//data/indexes/demo/search`.

## Search Endpoint

`GET /v1/{index}/search`

| Parameter | Required | Default | Notes |
| --- | --- | --- | --- |
| `query` | yes | none | String query only. Empty strings return 400. |
| `hits` | no | `10` | Positive integer. |
| `parse` | no | `true` | `true` parses JSON-backed stored raw fields; `false` returns raw stored strings. |
| `k1` | no | omit | BM25 k1 for sparse `tf` indexes only; must be sent with `b`. |
| `b` | no | omit | BM25 b for sparse `tf` indexes only; must be sent with `k1` and in `[0, 1]`. |
| `max_doc_length` | no | none | Positive integer character cap for parsed candidate docs; requires `parse=true`. |

REST does not expose multimodal query dictionaries, `encoder`, `ef_search`, or `query_generator`. Use MCP or Python APIs for those controls.

Examples:

```bash
curl "http://127.0.0.1:8081/v1/msmarco-v1-passage/search?query=what%20is%20a%20lobster%20roll&hits=1"

curl "http://127.0.0.1:8081/v1/cacm/search?query=information%20retrieval&hits=5&k1=0.8&b=0.3"

curl "http://127.0.0.1:8081/v1/msmarco-v1-passage/search?query=what%20is%20a%20lobster%20roll&hits=5&max_doc_length=500"
```

Response shape:

```json
{
  "api": "v1",
  "index": "msmarco-v1-passage",
  "query": {"text": "what is a lobster roll"},
  "candidates": [
    {"docid": "7157707", "score": 11.0083, "rank": 1, "doc": "..."}
  ]
}
```

Scores are rounded to six decimal places before response serialization.

## Document Endpoint

`GET /v1/{index}/doc/{docid}`

| Parameter | Required | Default | Notes |
| --- | --- | --- | --- |
| `parse` | no | `true` | Same semantics as search. |
| `max_doc_length` | no | none | Positive integer character cap for parsed document; requires `parse=true`. |

Examples:

```bash
curl "http://127.0.0.1:8081/v1/msmarco-v1-passage/doc/7157707"
curl "http://127.0.0.1:8081/v1/msmarco-v1-passage/doc/7157707?parse=false"
curl "http://127.0.0.1:8081/v1/msmarco-v1-passage/doc/7157707?max_doc_length=500"
```

Response shape:

```json
{
  "api": "v1",
  "index": "msmarco-v1-passage",
  "docid": "7157707",
  "doc": "..."
}
```

`doc` may be `null`, a string, JSON object, array, number, or boolean depending on stored contents and `parse`.

## Auth, Load Shedding, and Logs

When `api_keys` is configured, every `/v1/*` route requires one valid token. Either header form works:

```bash
curl -H "Authorization: Bearer replace-with-a-secret-token" \
  "http://127.0.0.1:8081/v1/local_sparse/search?query=test&hits=1"

curl -H "X-API-Key: replace-with-a-secret-token" \
  "http://127.0.0.1:8081/v1/local_sparse/doc/doc1"
```

With API keys enabled, Pyserini tracks a rolling one-minute p99 latency and per-key request counts. If p99 exceeds `--load-shedding-threshold`, the busiest key or keys may receive 429 with `Retry-After: 1`.

Operational logging flags:

```bash
python -m pyserini.server.rest \
  --config server.yaml \
  --no-prebuilt-indexes \
  --server-log-file logs/rest.server.log \
  --auth-log-file logs/rest.auth.log \
  --no-access-log
```

Auth logs contain short token fingerprints, not raw token values.

## Status Codes

| Code | Meaning |
| --- | --- |
| `200` | Successful search or document fetch. |
| `400` | Missing/invalid parameters, unsupported BM25 combination, unable to open index, or index not configured. |
| `401` | Missing or invalid API key when `api_keys` is set. |
| `404` | Unknown route or document not found. |
| `405` | Non-GET method; REST supports GET only. |
| `429` | Load shedding for the busiest authenticated key. |
| `500` | Unhandled server error. |

## When to Route Elsewhere

- Route explanations of BM25, analyzers, query builders, local indexing, stored fields, and document fetch semantics to `../../index-search-fetch/SKILL.md`.
- Route Faiss, dense encoders, OpenAI/model backends, GPU/CPU model issues, and hybrid dense/sparse retrieval to `../../dense-encoding/SKILL.md`.
- Route missing Python packages, Java/JVM failures, source checkout jars, and import checks to `../../install-and-runtime/SKILL.md`.
