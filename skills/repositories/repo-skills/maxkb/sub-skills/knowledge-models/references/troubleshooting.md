# Troubleshooting

## Common failures
- Empty retrieval results: confirm embeddings exist, the correct knowledge id is used, and the reranker/search model is available.
- `pgvector` or PostgreSQL issues: verify the vector extension, connection settings, and table state.
- Embedding task failures: check the model id, provider credential, and Celery task status.
- Provider catalog errors: confirm the requested model type is registered and supported.
- Local model failures: verify `SERVER_NAME=local_model`, host/port settings, and that the model artifact is available.
- Knowledge sync or export issues: check the document state machine and the workspace source.

## Safe response pattern
- Separate the search problem from the indexing problem.
- Separate provider availability from knowledge data quality.
- If something was not live-verified, say so directly.

## Do not do
- Do not assume a missing result means a bad query until embeddings and the vector backend are confirmed.
- Do not expose credential payloads in a handoff.
