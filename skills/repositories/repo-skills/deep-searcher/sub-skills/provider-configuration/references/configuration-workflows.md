# Configuration Workflows

## Purpose

Use this reference for Python and YAML setup patterns, provider switching, `ModuleFactory` behavior, and safe configuration validation without calling provider APIs.

## Core flow

```python
from deepsearcher.configuration import Configuration, init_config

config = Configuration()
config.set_provider_config("llm", "OpenAI", {"model": "o1-mini"})
config.set_provider_config("embedding", "OpenAIEmbedding", {"model": "text-embedding-ada-002"})
config.set_provider_config("file_loader", "PDFLoader", {})
config.set_provider_config("web_crawler", "FireCrawlCrawler", {})
config.set_provider_config("vector_db", "Milvus", {"uri": "./milvus.db", "token": "root:Milvus"})
init_config(config)
```

`init_config(config)` constructs all configured providers immediately. In this checkout, that includes the default crawler and vector database, even if a task only cares about one workflow.

## YAML workflow

The inspected repository stores defaults in `deepsearcher/config.yaml` with three major sections:

- `provide_settings`
- `query_settings`
- `load_settings`

A practical pattern is:

```python
from deepsearcher.configuration import Configuration, init_config

config = Configuration(config_path="deepsearcher-config.yaml")
init_config(config)
```

Keep provider names exact and keep feature keys to `llm`, `embedding`, `file_loader`, `web_crawler`, and `vector_db`.

## Safe provider switching patterns

### Switch only the LLM

```python
config = Configuration()
config.set_provider_config("llm", "DeepSeek", {"model": "deepseek-reasoner"})
init_config(config)
```

### Use a local stack

```python
config = Configuration()
config.set_provider_config("llm", "Ollama", {"model": "qwq"})
config.set_provider_config("embedding", "FastEmbedEmbedding", {"model": "BAAI/bge-small-en-v1.5"})
config.set_provider_config("file_loader", "PDFLoader", {})
config.set_provider_config("vector_db", "Milvus", {"uri": "./milvus.db", "token": ""})
init_config(config)
```

### Keep web crawling optional

Only enable `FireCrawlCrawler`, `Crawl4AICrawler`, or `JinaCrawler` when the required service and credentials are ready. Otherwise, the default config can fail before any load/query workflow begins.

## ModuleFactory behavior

`ModuleFactory` imports the configured class from the feature's package and instantiates it with the config dictionary. That means:

- The provider name must match an exported class exactly.
- Unknown feature keys raise a `ValueError`.
- Missing keys or wrong config shapes fail before the workflow begins.
- Some provider classes validate credentials in `__init__`; others fail only when `chat`, `embed_*`, `load_*`, or `crawl_*` is invoked.

## Validation without provider calls

Use the bundled helper to check the config shape and, optionally, import the configured provider classes without contacting services:

```bash
python scripts/validate_provider_config.py --list-providers
python scripts/validate_provider_config.py --config deepsearcher-config.yaml
python scripts/validate_provider_config.py --config deepsearcher-config.yaml --check-imports
```

The helper is designed to stay local: it does not instantiate providers, call APIs, or open a vector database.

## Common setup patterns

- `OpenAI` + `OpenAIEmbedding` + `PDFLoader` + `Milvus` is the default orientation in this checkout.
- `Ollama` + `FastEmbedEmbedding` + `Milvus` is the easiest fully local alternative when the Ollama service is available.
- `DoclingLoader` and `UnstructuredLoader` can be swapped in for richer file parsing, but they add optional packages and may need more system support.
- `FireCrawlCrawler` is network/service-backed and should remain optional until credentials are available.

## When to read troubleshooting

If the failure mentions an import, credential, or compatibility problem, switch to [troubleshooting](troubleshooting.md) for exact recovery steps.
