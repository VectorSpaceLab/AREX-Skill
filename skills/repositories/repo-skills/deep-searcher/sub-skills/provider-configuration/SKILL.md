---
name: provider-configuration
description: "Configure DeepSearcher providers, provider dictionaries,
  credentials, optional dependencies, and setup troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Provider Configuration

Use this sub-skill when a task is about selecting or diagnosing DeepSearcher providers for LLMs, embeddings, file loaders, web crawlers, or vector databases. DeepSearcher provider strings are exact Python class names, and `init_config(config)` constructs every configured provider before ingestion or query work begins.

## Route here for

- Building a `Configuration(config_path=...)` object from defaults or YAML.
- Updating providers with `set_provider_config(feature, provider, provider_configs)` and checking them with `get_provider_config(feature)`.
- Choosing exact feature keys: `llm`, `embedding`, `file_loader`, `web_crawler`, `vector_db`.
- Mapping provider names to credential variables, optional packages, and common config dictionaries.
- Diagnosing provider import failures, missing SDKs, missing credentials, FireCrawl `ScrapeOptions` errors, or local Milvus Lite setup failures.

## Route elsewhere

- Loading files, crawling websites, chunking, collections, and indexing: `data-ingestion`.
- `query`, `retrieve`, `DeepSearch`, `ChainOfRAG`, `NaiveRAG`, and result interpretation: `rag-query`.
- Console command behavior, FastAPI service endpoints, or help output: `cli-and-service`.
- 2WikiMultiHopQA or benchmark/evaluation workflows: `evaluation`.

## Reference map

- [Provider matrix](references/provider-matrix.md): exact provider names, feature keys, credentials, optional dependencies, and default provider choices.
- [Configuration workflows](references/configuration-workflows.md): Python/YAML setup patterns, `ModuleFactory` behavior, `init_config` side effects, and safe provider switches.
- [Troubleshooting](references/troubleshooting.md): provider-name mismatches, optional dependency errors, FireCrawl and Milvus Lite version constraints, and credential handling.

## Safe bundled helper

Use [scripts/validate_provider_config.py](scripts/validate_provider_config.py) to validate a DeepSearcher YAML config or the built-in default provider set without calling provider APIs:

```bash
python scripts/validate_provider_config.py --config deepsearcher-config.yaml
python scripts/validate_provider_config.py --list-providers
python scripts/validate_provider_config.py --print-example ollama-fastembed-milvus
```

`--check-imports` is optional. It imports configured provider classes to expose missing packages or incompatible SDK versions, but it still does not instantiate providers, read credentials, contact networks, or open vector databases.

## Operating rules

1. Treat provider strings as exact class names. `JiekouAI` is valid; `Jiekou.AI` is not a `ModuleFactory` provider string.
2. Prefer environment variables for credentials. If a config dictionary contains `api_key`, `token`, `password`, or cloud access keys, redact values in any output.
3. Keep optional, credentialed, network, or service-backed workflows optional until the user explicitly chooses them and provides credentials/service readiness.
4. When switching providers, update every affected feature before `init_config(config)`, because `init_config` constructs all configured providers, including unused defaults such as `FireCrawlCrawler` and `Milvus`.
5. For local Milvus Lite, use a unique working directory or explicit `uri` per concurrent process to avoid locking the default `./milvus.db`.
