# Models, Resources, and Vector Troubleshooting

## Symptoms and Recovery

| Symptom | Likely cause | Recovery |
|---|---|---|
| Provider validation says invalid key | Placeholder/incorrect key, provider mismatch, or network failure. | Confirm provider name and real credential before making a live validation call. |
| Local LLM requests fail | `OPENAI_API_BASE` points to a service that is not running or not OpenAI-compatible. | Verify the local endpoint separately and check Docker/local LLM setup. |
| Resource upload works but summarization fails | Celery worker missing, provider key invalid, optional parser missing, or vector DB unavailable. | Check worker, model provider, document parser dependencies, and vector config. |
| S3 resource path fails | `STORAGE_TYPE` is S3 but bucket or AWS keys are missing. | Use the config checker and confirm S3 permissions. |
| Pinecone/Weaviate/Qdrant errors | Missing credentials, service unavailable, wrong index/collection settings, or dimension mismatch. | Inspect vector config and sample embedding dimension before creating indexes. |
| Chroma or LanceDB route is requested | Enum value exists but factory support may be incomplete in this checkout. | Verify the target checkout implementation before promising support. |
| Missing `unstructured` or parser package | Document loader dependency not installed in the environment. | Install only the parser package required for the user's file type in an isolated env. |

## Safe Checks

- Use `scripts/check_provider_config.py` for structural config checks.
- Do not call provider verification or create vector DB indexes without explicit
  authorization and real credentials.
- Prefer mocked/unit tests or static checks when credentials/services are absent.
