# Server Troubleshooting

Start with the safest check that matches the symptom. Prefer validating YAML and imports before starting servers or opening large indexes.

## Config and Alias Failures

Run:

```bash
python scripts/validate_server_config.py server.yaml
```

Common messages and fixes:

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Config root must be a mapping/object` | YAML top level is a list/scalar. | Use a mapping with `indexes:` and/or `api_keys:`. |
| `Index aliases in config must be non-empty` | Empty alias key. | Rename to a non-empty alias such as `local_sparse`. |
| `must map to a non-empty path` | Missing/blank path. | Set `path` or short-form string path. |
| `unsupported index_type` | Typo or unsupported type. | Use `tf`, `impact`, `lucene_flat`, `lucene_hnsw`, or `faiss`. |
| `requires encoder` | Dense/impact/Faiss alias lacks `encoder`. | Add a query encoder id appropriate for that index. |
| `points to missing path` | Directory does not exist or relative path resolves differently than expected. | Create the index first or fix the path relative to the YAML file. |
| `references unknown base_index` | Dense/Faiss alias names a missing sparse alias. | Add the sparse alias or update `base_index`. |
| `must reference a TF base_index` | `base_index` points to another dense/Faiss/impact alias. | Point `base_index` to a `tf` alias with stored documents. |

Dense, impact, and Faiss search often need a sparse base index because server responses fetch stored documents through Lucene. If search succeeds but document rendering fails, re-check `base_index` and whether the sparse index was built with stored raw contents.

## REST Startup Fails

| Symptom | Cause | Fix |
| --- | --- | --- |
| `--no-prebuilt-indexes requires --config` | Locked-down mode has no alias source. | Pass `--config server.yaml`. |
| `--no-prebuilt-indexes requires at least one entry under indexes` | Config has no usable aliases. | Add `indexes:` entries. |
| `--port must be in [1, 65535]` | Invalid port. | Choose a valid TCP port. |
| `--load-shedding-threshold must be >= 0` | Negative threshold. | Use `0` for aggressive test shedding or a positive threshold. |
| Import error mentioning `faiss` | Server backend imports Faiss search support. | Install a compatible `faiss-cpu` or GPU Faiss package; route dependency work to `../../install-and-runtime/SKILL.md` or `../../dense-encoding/SKILL.md`. |
| Java/JVM or Anserini classpath error | Lucene-backed Pyserini cannot load Java resources. | Route to `../../install-and-runtime/SKILL.md`; source checkout resource builds belong in `../../repo-development/SKILL.md`. |

Use help-only checks before live startup when dependencies are uncertain:

```bash
python -m pyserini.server.rest --help
python -m pyserini.server.mcp --help
```

`pyserini.server.mcp --help` can still fail in source-checkout environments when optional Faiss or evaluation resources are unavailable; treat that as runtime-resource evidence, not necessarily a syntax issue.

## REST Request Errors

| HTTP code | Meaning | Fix |
| --- | --- | --- |
| `400` with `Parameter 'query' is required` | Search query missing/blank. | Add `query=...`. |
| `400` with `hits` | Non-integer or non-positive hit count. | Use `hits=1` or another positive integer. |
| `400` with `parse` | `parse` is not `true` or `false`. | Use lowercase `true` or `false`. |
| `400` with `k1 and b must be set together` | Only one BM25 parameter was sent. | Send both `k1` and `b`, or omit both. |
| `400` with `BM25 ... sparse` | BM25 override sent to dense/Faiss/impact alias. | Remove `k1`/`b` or use a `tf` alias. |
| `400` with `max_doc_length requires parse=true` | Tried to truncate a raw string response. | Omit `parse=false` or omit `max_doc_length`. |
| `400` with `Unable to open index` | Alias/path/prebuilt cannot be opened. | Validate config, confirm index exists, check Java/Faiss/resources. |
| `401` | Missing/invalid API token. | Send `Authorization: Bearer <token>` or `X-API-Key: <token>`. |
| `404` document not found | Index opened but docid is absent. | Verify docid from search results or fetch from the correct base index. |
| `405` | Used POST/PUT/etc. | REST server supports GET only. |
| `429` | Load shedding for a busy authenticated key. | Honor `Retry-After`, back off with jitter, lower concurrency, or raise the threshold after diagnosis. |

## Auth Header Confusion

If `api_keys` is absent or empty, REST `/v1/*` routes are anonymous. If `api_keys` is present, both of these are valid and equivalent:

```bash
-H "Authorization: Bearer token-value"
-H "X-API-Key: token-value"
```

When both are present, the server accepts the request if either supplied token is valid. Auth logs record a short hash fingerprint, not the raw token.

## Cache, Load Shedding, and Logs

Search and document caches are in-process LRU caches. Increase sizes only after measuring repeated request patterns:

```bash
python -m pyserini.server.rest --search-cache-size 4096 --document-cache-size 8192
```

Load shedding only activates when API keys are configured. A threshold of `0` is useful for testing 429 behavior, but too aggressive for normal service. If legitimate traffic gets 429s:

1. Check whether one key is generating most traffic.
2. Lower client concurrency and add retry-with-jitter.
3. Increase `--load-shedding-threshold` after confirming server health.
4. Use `--auth-log-file` to attribute request bursts without exposing token values.

## MCP Client Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Client cannot find `mcpyserini` | Config not reloaded or wrong JSON location. | Restart the client and verify its MCP config format. |
| `stdio` server appears to hang | Normal stdio behavior: server waits for MCP messages. | Use the client UI/tool list, or use HTTP transport for manual connectivity tests. |
| HTTP client cannot connect | Wrong port/path or missing port forwarding. | Use `--transport http --port 8000`, then configure URL `http://127.0.0.1:8000/mcp`. |
| Tool call opens a prebuilt index unexpectedly | Prompt used a prebuilt name instead of configured alias. | Prompt with the alias and validate `server.yaml`. |
| Tool fails on `eval_hits` | Java-backed eval resources missing. | Route package/runtime checks to `../../install-and-runtime/SKILL.md`; source checkout builds to `../../repo-development/SKILL.md`. |
| Multimodal query fails | Index/backend does not support the query fields or image source. | Use a text query on ordinary indexes; route dense/multimodal backend choice to `../../dense-encoding/SKILL.md`. |

## Prebuilt Indexes Disabled

With REST `--no-prebuilt-indexes`, any `/v1/{index}/...` request must use an alias declared in `server.yaml`. Prebuilt names such as `msmarco-v1-passage` and arbitrary filesystem paths are rejected. This is intentional for deployments that should not download indexes or expose local paths.

If a user expects prebuilt names to work, remove `--no-prebuilt-indexes` for a trusted local workflow or add explicit aliases pointing at prepared local index directories.
