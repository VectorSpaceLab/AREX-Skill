# Service Reference

## Purpose

Use this reference for the bundled FastAPI service helper that mirrors the public DeepSearcher HTTP surface using installed package APIs.

## Bundled helper

Run:

```bash
python scripts/serve_deepsearcher_api.py --host 0.0.0.0 --port 8000 --enable-cors
```

Useful flags:

- `--config-path PATH`: load an alternate DeepSearcher YAML config before serving.
- `--eager-init`: initialize the default configuration before serving so provider or vector DB failures surface at startup instead of on the first request.
- `--help`: show the helper's own command-line help.

The helper is source-free: it does not depend on the original checkout's `main.py` at runtime.

## Endpoints

| Method | Path | Purpose | Key payload fields |
| --- | --- | --- | --- |
| POST | `/set-provider-config/` | Update a feature's provider and re-initialize DeepSearcher | `feature`, `provider`, `config` |
| POST | `/load-files/` | Load local files or directories into a collection | `paths`, `collection_name`, `collection_description`, `batch_size` |
| POST | `/load-website/` | Crawl one or more URLs into a collection | `urls`, `collection_name`, `collection_description`, `batch_size` |
| GET | `/query/` | Ask a question against loaded data | `original_query`, `max_iter` |

## Request shapes

### `/set-provider-config/`

```json
{
  "feature": "llm",
  "provider": "OpenAI",
  "config": {
    "model": "o1-mini"
  }
}
```

The helper redacts sensitive fields in its response. Use `feature` values from `provider-configuration`.

### `/load-files/`

- `paths` can be a string or a list of strings.
- Paths may be local files, local directories, or a mix of local values that should be loaded together.
- The helper calls the DeepSearcher loading API after provider readiness is established.

### `/load-website/`

- `urls` can be a string or a list of strings.
- The bundled endpoint mirrors the source service fields shown above; configure crawler-specific behavior through the provider configuration.
- FireCrawl or other crawler-specific credentials still need to be configured through the provider layer.

### `/query/`

- `original_query` is the question string.
- `max_iter` defaults to `3`.
- The response mirrors the source service shape: result text plus consumed token count.

## Route discovery check

Use `scripts/check_service_routes.py` to import the helper and confirm the route list without launching a server.

## Operational notes

- The service helper is lazy by default so it can be imported without immediately constructing providers.
- If you want eager startup validation, pass `--eager-init`.
- If the default Milvus config points at a locked `./milvus.db`, use a fresh working directory or change the vector DB configuration first.
