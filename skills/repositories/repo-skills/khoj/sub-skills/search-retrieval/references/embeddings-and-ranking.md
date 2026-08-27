# Embeddings and Ranking

## Default Models

Khoj's local default search configuration uses:

- Bi-encoder: `thenlper/gte-small`
- Cross-encoder/reranker: `mixedbread-ai/mxbai-rerank-xsmall-v1`

The bi-encoder embeds documents during indexing and embeds the defiltered query during search. The cross-encoder scores candidate passages against the query for higher-quality ordering after retrieval.

Search model configs can point embeddings to local sentence-transformer models, Hugging Face inference, OpenAI embeddings, Azure/OpenAI-compatible endpoints, or similar configured APIs. If the bi-encoder changes, the indexed document embeddings must be regenerated because stored vectors no longer live in the same embedding space.

## Query and Document Embeddings

Local embedding behavior normalizes query and document embeddings. Query encoding uses no progress bar; document encoding shows progress and batches remote API embedding calls in chunks of up to 1000 documents.

Text search embeds the defiltered query, not the raw query with filter syntax. The raw query is still passed into the database adapter so word, file, and date filters can constrain candidate entries before distance sorting.

## `max_distance`

`max_distance` is a cosine-distance ceiling applied after vector distance annotation. Smaller values are stricter. Larger values admit less semantically similar results.

Important defaults:

- The public `/api/search` route passes infinity when `max_distance` is omitted.
- The lower-level text query function can fall back to the default search model's bi-encoder confidence threshold when it receives a missing value.
- Search model config documents describe the confidence threshold as a normalized semantic-distance limit between `0.0` and `1.0`, where lower is closer and stricter.

When debugging no results, check whether a caller supplied an overly small `max_distance` even though filters and ownership are correct. When debugging noisy results, lower `max_distance` or set/tune the model config threshold for callers that rely on it.

## Candidate Count and Final Count

Text retrieval asks the database adapter for up to `10` vector candidates per text search branch. `/api/search` then collates, sorts, reranks when enabled, and slices to `n` results, defaulting to `5`.

If `n` is higher than the internal candidate count, increasing only `n` may not be enough for deeper recall unless the implementation's candidate count is also changed.

## Reranking

Reranking runs when `r=true` or when the cross-encoder has an enabled inference server and more than one hit exists. The reranker predicts relevance scores for `[query, compiled_passage]` pairs. Khoj converts each score to a distance-like value with `1 - score` and stores it as `cross_score`.

Sort order:

1. Sort by bi-encoder `score` ascending.
2. If reranking is active, sort by `cross_score` ascending.

If the cross-encoder HTTP inference endpoint fails, Khoj logs the error, assigns fallback scores, and returns results rather than failing the whole search. Local cross-encoder model load or prediction problems may still surface as server/runtime failures depending on where they occur.

## Performance Notes

Typical documented behavior is that semantic search with the default embeddings model is fast, reranking is slower, and filters add a small amount of latency. Practical tuning levers are:

- Disable reranking (`r=false`) for speed when bi-encoder order is good enough and no cross-encoder inference server forces rerank.
- Reduce `n` for faster response and less reranking work.
- Tune `max_distance` or the bi-encoder confidence threshold to reduce noisy candidates.
- Prefer a working inference endpoint for deployments that cannot load local transformer models reliably.
