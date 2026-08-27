# Configuration Troubleshooting

Read this when Cognee import, config construction, or backend selection fails.
The symptoms below are the ones a future agent is most likely to see first.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ProviderNotDeducibleError` or a provider/model mismatch | `LLM_MODEL` / `EMBEDDING_MODEL` uses a prefix that Cognee cannot infer, or the provider was never set explicitly. | Set `LLM_PROVIDER` or `EMBEDDING_PROVIDER` explicitly, then re-import `cognee`. Use `references/configuration.md` to confirm the provider names. |
| Vector write fails with a dimension mismatch | The embedding model does not match the configured vector dimension, or auto-detection fell back to the wrong size. | Set `EMBEDDING_DIMENSIONS` explicitly for the selected model. Rebuild or isolate the vector store if it already contains incompatible vectors. |
| Relational/graph/vector paths land in the wrong place | `SYSTEM_ROOT_DIRECTORY`, `DATA_ROOT_DIRECTORY`, or the database provider changed after the store was created. | Set the root directories before first import/use, or move to a fresh runtime directory if the existing store should be preserved. |
| `DATABASE_CONNECT_ARGS`, `POOL_ARGS`, or `VECTOR_POOL_ARGS` fails to parse | The value is not valid JSON, or it is not a JSON object. | Reformat the value as a JSON object string. Avoid shell-escaped Python dict syntax. |
| `GRAPH_DATASET_DATABASE_HANDLER` or `VECTOR_DATASET_DATABASE_HANDLER` looks wrong | The selected provider and the dataset handler disagree. | Align the handler with the provider (`pgvector` with `pgvector`, `turso` with `turso`, etc.). |
| S3-backed storage behaves differently from local storage | Local path assumptions leaked into an S3-backed root/cache config. | Use S3 URLs and S3-compatible cache settings; do not rely on an on-disk relative path when `STORAGE_BACKEND=s3`. |
| Session or cache features are unavailable | `CACHING` is off, or the selected cache backend is not installed/configured. | Turn on caching only when needed and install the selected cache backend/extras. Route session-memory questions to [agent-session-memory](../../agent-session-memory/SKILL.md). |
| Import works in one shell but not another | The environment variables were set after `cognee` was already imported, so pydantic-settings cached the earlier configuration. | Restart the process and set environment variables before the first `import cognee`, or use explicit `cognee.config` setters in-process. |
| Auth posture seems inconsistent | `ENABLE_BACKEND_ACCESS_CONTROL`, `REQUIRE_AUTHENTICATION`, and token secrets are not aligned. | Check the access-control section of `references/configuration.md` and restart the service after changing env vars. |
| Optional provider extras are missing | The base install does not include the provider-specific package. | Install only the extra needed for the selected backend or provider; do not install all extras by default. |

## Safe next checks

1. Run the bundled checker:

   ```bash
   python scripts/check_cognee_environment.py --json
   ```

2. If you changed env vars in-process, restart the interpreter or service.
3. If a backend or optional provider is missing, decide whether to install the
   matching extra or narrow the workflow to the base install.
