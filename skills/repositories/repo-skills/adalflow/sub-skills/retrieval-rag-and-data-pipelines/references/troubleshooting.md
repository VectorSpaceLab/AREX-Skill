# Troubleshooting

Use this guide when a retrieval or data-pipeline step fails. Start with the smallest safe check: `Document` shape, splitter settings, embedding width, then retriever availability, then persistence.

## Optional backend imports fail

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Import error for FAISS, LanceDB, Qdrant, SQLAlchemy, or pgvector | The optional backend is not installed in the current environment. | Switch to `BM25Retriever` or install the missing extra before retrying the retrieval step. |
| Import error for a vector-store client | The retriever depends on a service-side client package that is not available. | Gate the retriever behind an availability check and fall back to the local backend. |
| Connection or collection/table errors | The service is not running, the endpoint is wrong, or the collection/table has not been created. | Verify the service first, then rebuild or reconnect to the target index. |

## Empty or malformed documents

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `TextSplitter.call(...)` raises a type error | The input is not a list of `Document` objects. | Convert your records into `Document` first, then call the splitter. |
| `TextSplitter.call(...)` raises a value error for text | One or more `Document.text` values are missing. | Skip empty records or fill the text before splitting. |
| `Document.from_dict(...)` fails | The input dict is missing `text` or `meta_data`. | Supply both fields explicitly before constructing the document. |
| Retrieval returns no context | The corpus is empty or the filter removed every item. | Check the loaded document count, then relax the filter or add corpus data. |

## Splitter settings are invalid

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `chunk_size` must be greater than zero | A zero or negative chunk size was passed. | Use a positive chunk size. |
| `chunk_overlap` is invalid | Overlap is negative or larger than/equal to the chunk size. | Reduce overlap so it is strictly smaller than `chunk_size`. |
| Unsupported `split_by` | The separator name is not in the allowed set. | Use `word`, `sentence`, `page`, `passage`, or `token`, or pass a custom separator map. |

## Embedding and vector mismatch

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| FAISS build/search dimension assertion fails | The persisted vectors do not match the current embedding width. | Re-embed the corpus and rebuild the index with the new dimension. |
| Retrieval quality suddenly drops after an embedder swap | The old vectors are stale for the new model. | Recompute vectors and clear the old index file or table. |
| Cosine search behaves oddly | The embedding vectors are not normalized for cosine-style retrieval. | Normalize the vectors or let the FAISS cosine path normalize them during indexing. |
| Score thresholds do not transfer between backends | Different retrievers use different score semantics. | Recalibrate the threshold for each metric/back end instead of reusing one number. |

## Retriever-specific issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| BM25 returns weak lexical matches | The query is semantic but the corpus is sparse or the chunk text is too short. | Combine title + content in `document_map_func`, or switch to vector retrieval for semantics. |
| FAISS search fails with empty index | The index was never built or was reset after a failed build. | Rebuild the index before calling retrieval. |
| LanceDB/Qdrant/Postgres results look stale | Old rows/chunks are still present in the external store. | Recreate the table/collection or use a clean namespace before reingesting. |
| Postgres vector search returns no rows | The database schema or distance operator does not match the stored vectors. | Verify the table schema, the vector column, and the operator choice. |

## RAG assembly issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| The same chunks appear multiple times in the context string | The same documents were reindexed or query expansion produced duplicates. | Enable deduplication in the context builder and rebuild a clean index if needed. |
| The context string is unexpectedly short | Too few chunks were retrieved, or the corpus filter was too strict. | Increase `top_k`, loosen the filter, or inspect the chunking settings. |
| Indexing after corpus updates seems inconsistent | Old transformed items are still being reused. | Rebuild the `LocalDB` state from the updated source data and overwrite the cached index. |
| Saved state does not reload cleanly | The save path was missing or the state file is stale. | Use an explicit save path and verify the file exists before loading. |

## External credential boundary

This sub-skill does not create or validate provider credentials. If the failure is inside `Embedder` construction or downstream generation, move to the model-client-and-generator-workflows sub-skill.

## Suggested hard verification cases

1. Start with raw dict documents, filter them through `LocalDB`, split them, embed them, and swap BM25 for FAISS without changing the context builder.
2. Save a vector index, change the embedding dimension, and verify that the old index is rejected and rebuilt instead of silently reused.
