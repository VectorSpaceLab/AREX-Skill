# Provider Configuration Troubleshooting

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Unsupported feature: ...` | The feature key is not one of `llm`, `embedding`, `file_loader`, `web_crawler`, or `vector_db`. | Fix the key and re-run the config update. |
| `ImportError` when checking a provider module | The optional SDK for that provider is missing or incompatible. | Install the documented extra/package for that provider and rerun `scripts/validate_provider_config.py --check-imports`. |
| `Missing credentials` from OpenAI-compatible providers | The provider was instantiated without an API key or base URL. | Set the matching environment variable or pass the credential through the provider config. |
| `ImportError: cannot import name 'ScrapeOptions' from 'firecrawl'` | The FireCrawl Python client is too new for this checkout. | Pin `firecrawl-py==2.16.5` and re-check the config. |
| `ConnectionConfigException` or local Milvus Lite errors | The Milvus Lite support packages are missing or too new for this checkout. | Install `pymilvus==2.5.8`, `milvus-lite==2.5.1`, and `setuptools<81`. |
| `MilvusLite` lock errors | Multiple processes are sharing the same local `./milvus.db`. | Use a unique working directory or a unique `uri` per process. |
| Provider name mismatch with a human label | The provider string must be the exported class name, not the doc label. | Copy the exact class name from [provider matrix](provider-matrix.md). |

## Safe recovery steps

1. Validate the config shape locally:

   ```bash
   python scripts/validate_provider_config.py --config deepsearcher-config.yaml
   ```

2. If you need to see every available provider and supported feature key, run:

   ```bash
   python scripts/validate_provider_config.py --list-providers
   ```

3. If a provider import still fails, inspect the relevant optional package or credential requirement in [provider matrix](provider-matrix.md).
4. If the failure is actually about loading files, querying data, or running the service, route to the sibling sub-skill instead of forcing the provider layer.

## Notes

- The helper script intentionally avoids instantiating providers or making API calls.
- If a task requires a remote service or credentialed provider, keep that part optional until the user confirms the service and credentials are ready.
