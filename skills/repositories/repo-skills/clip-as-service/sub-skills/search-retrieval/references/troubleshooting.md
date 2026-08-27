# Search Retrieval Troubleshooting

## Setup failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `No module named 'annlite'` | Search extra was not installed. | Install `clip-server[search]` on the search server environment, or install a compatible AnnLite package. |
| `/index` or `/search` returns endpoint errors | Flow contains only `CLIPEncoder`, not `AnnLiteIndexer`. | Add the indexer executor from [workflows.md](workflows.md) and restart the service. |
| Server starts but client URI fails | Protocol/port mismatch or server unreachable. | Use [client-api troubleshooting](../../client-api/references/troubleshooting.md) to verify URI scheme, TLS, and network. |
| Model download starts during search server startup | The encoder stage needs model weights before indexing/searching. | Approve/cache model downloads or use a smaller model for smoke tests. |

## Dimension and workspace failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Indexer complains about vector dimension | AnnLite `n_dim` does not match the encoder model output. | Run `check_search_config.py --model-name <name>`, update `n_dim`, and rebuild the workspace. |
| Search results are nonsensical after changing models | Old index workspace contains embeddings from a different model. | Create a new workspace or rebuild the index from source documents. |
| Search returns no matches after indexing | Documents were indexed into a different workspace, index call failed, or the server restarted with a new workspace. | Confirm workspace path, inspect server logs, re-index a tiny known fixture, then query it. |
| Limit is lower than expected | Indexer default `limit` or client `limit` is too small, or fewer docs are indexed. | Pass `client.search(..., limit=k)` and ensure at least `k` documents are indexed. |

## Sharding failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Sharded search misses obvious matches | `/search` polling is `ANY`, so only one shard is queried. | Set `/search: ALL`; restart and retest. |
| Duplicate documents appear after indexing | `/index` polling is `ALL`, so every shard stores each document. | Set `/index: ANY`; rebuild the index to remove duplicates. |
| Update/delete affects only part of the corpus | `/update` or `/delete` polling is not `ALL`. | Set `/update`, `/delete`, and `/status` to `ALL` for shard consistency. |

## Memory and scale issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Index build consumes too much memory | High `n_dim`, many documents, high HNSW connectivity, stored metadata columns, or too few shards. | Estimate memory using [workflows.md](workflows.md); shard, reduce stored columns, use a lower-dimensional model, or scale host memory. |
| Query latency increases after sharding | `/search: ALL` fans out to every shard. | Balance shard count against latency; use enough shards for memory but not so many that fanout dominates. |
| Image ingestion is slow | Client loads or sends large images and server preprocesses them before embedding. | Use accessible URIs, smaller batches, and [server-runtime](../../server-runtime/SKILL.md) minibatch/prefetch tuning. |

## Safe checks

```bash
python sub-skills/search-retrieval/scripts/check_search_config.py sub-skills/search-retrieval/scripts/search-flow.yml --model-name ViT-B-32::openai
```

This catches config issues before starting model downloads or writing an index.
