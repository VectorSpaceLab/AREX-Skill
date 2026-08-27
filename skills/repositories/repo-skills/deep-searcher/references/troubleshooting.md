# DeepSearcher Troubleshooting

## Purpose

Read this first when installation, import, or startup fails before you know which sub-skill is responsible.

## Common cross-cutting failures

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `ImportError: cannot import name 'ScrapeOptions' from 'firecrawl'` | The installed FireCrawl client is newer than the one this checkout expects. | Pin `firecrawl-py==2.16.5` and re-run [scripts/check_deepsearcher_environment.py](../scripts/check_deepsearcher_environment.py). Then continue in `provider-configuration` or `cli-and-service`. |
| `ConnectionConfigException: milvus-lite is required for local database connections` | The local Milvus Lite extra is missing. | Install `pymilvus==2.5.8`, `milvus-lite==2.5.1`, and `setuptools<81`. Use a unique working directory if multiple processes share the default `./milvus.db`. |
| `Protocol message ShowCollectionsResponse has no "shards_num" field` | `pymilvus` / `milvus-lite` 3.x mismatch with this checkout. | Downgrade to the compatibility pins above. |
| `ModuleNotFoundError: pkg_resources` inside `milvus_lite` | `setuptools` is too new for the pinned Milvus Lite client. | Install `setuptools<81`. |
| `OpenAIError: Missing credentials` during CLI help or service startup | The default config initializes OpenAI before the parser or endpoint can finish. | Set a dummy key for help-only checks, or configure providers before calling `init_config(config)`. |
| `DataDirLockedError` or local Milvus lock errors | Multiple runs share the same cwd-relative `./milvus.db`. | Use a temporary working directory or unique `uri` per run. |
| `Unsupported feature` from `Configuration.set_provider_config` | The feature key is not one of `llm`, `embedding`, `file_loader`, `web_crawler`, `vector_db`. | Check `provider-configuration` and use the exact feature name from the public API. |

## How to recover safely

1. Run the bundled environment check:

   ```bash
   python scripts/check_deepsearcher_environment.py
   ```

2. If the error is provider-specific, move to `sub-skills/provider-configuration/`.
3. If the error happens while loading documents or websites, move to `sub-skills/data-ingestion/`.
4. If the error happens during `deepsearcher query` or result interpretation, move to `sub-skills/rag-query/`.
5. If the error happens in the console command or the HTTP service, move to `sub-skills/cli-and-service/`.

## Notes on optional workflows

- Credentialed providers, remote vector DBs, web crawlers, and evaluation runs are optional features. A failure there does not mean the base package is unusable.
- Do not treat a CPU import check as proof that a service-backed or credentialed workflow is ready.
- For CLI help checks, use the CLI sub-skill's bundled helper rather than invoking the source checkout's scripts directly.
