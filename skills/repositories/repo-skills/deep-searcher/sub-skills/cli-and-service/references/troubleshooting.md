# CLI and Service Troubleshooting

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `OpenAIError: Missing credentials` during `deepsearcher --help` | The CLI initializes the default configuration before argparse finishes. | Use `scripts/check_cli_help.py` in a temp working directory with a dummy `OPENAI_API_KEY`, or configure the providers first. |
| `ConnectionConfigException` or local Milvus Lite errors during help/startup | The default vector DB points at cwd-relative `./milvus.db`, which can be missing or locked. | Use a fresh temp directory or give Milvus a unique `uri` before starting the CLI or service. |
| `ImportError: cannot import name 'ScrapeOptions' from 'firecrawl'` | The installed FireCrawl client version is too new for this checkout. | Pin `firecrawl-py==2.16.5` and retry. |
| `DataDirLockedError` | Multiple processes are sharing the same local Milvus Lite database file. | Move the probe to a new temp directory or isolate the `uri`. |
| The HTTP helper starts but the first load/query fails | Providers were not initialized yet. | Either call `/set-provider-config/` first or start `scripts/serve_deepsearcher_api.py --eager-init ...` to surface setup failures at launch. |
| The service routes differ from the source `main.py` | The bundled helper is meant to be source-free and importable without the original checkout. | Use `scripts/check_service_routes.py` to inspect the bundled app and keep future agents on the bundled helper, not the source file. |

## Safe recovery steps

1. Run the CLI help checker:

   ```bash
   python scripts/check_cli_help.py --command all
   ```

2. Inspect the bundled service routes:

   ```bash
   python scripts/check_service_routes.py
   ```

3. If the failure is provider-specific, route to `provider-configuration`.
4. If the failure is about loading files or websites, route to `data-ingestion`.
5. If the failure is about retrieval or answer generation, route to `rag-query`.

## Notes

- The CLI helper uses a temporary working directory so local Milvus Lite locks do not leak across probes.
- The service helper is source-free and should be used instead of the repository's `main.py` when future agents need a reusable HTTP surface.
- For background details on command flags and API routes, see [CLI reference](cli-reference.md) and [service reference](service-reference.md).
