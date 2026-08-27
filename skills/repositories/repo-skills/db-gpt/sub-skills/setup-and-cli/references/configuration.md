# DB-GPT TOML configuration

## Minimal safe shape

A web configuration normally has system, web/database, storage, and model sections. Start with a reviewed provider example, remove credentials, and adapt only the fields needed for the task:

```toml
[system]
language = "${env:DBGPT_LANG:-en}"
log_level = "INFO"
api_keys = []
encrypt_key = "replace-with-a-reviewed-secret-or-secret-reference"

[service.web]
host = "127.0.0.1"
port = 5670

[service.web.database]
type = "sqlite"
path = "pilot/meta_data/dbgpt.db"

[rag.storage]
[rag.storage.vector]
type = "chroma"
persist_path = "pilot/data"

[models]
[[models.llms]]
name = "${env:LLM_MODEL_NAME:-gpt-4o}"
provider = "${env:LLM_MODEL_PROVIDER:-proxy/openai}"
api_base = "${env:OPENAI_API_BASE:-https://api.openai.com/v1}"
api_key = "${env:OPENAI_API_KEY}"

[[models.embeddings]]
name = "${env:EMBEDDING_MODEL_NAME:-text-embedding-3-small}"
provider = "${env:EMBEDDING_MODEL_PROVIDER:-proxy/openai}"
api_url = "${env:EMBEDDING_MODEL_API_URL:-https://api.openai.com/v1/embeddings}"
api_key = "${env:OPENAI_API_KEY}"
```

The generated setup profile uses `host = "0.0.0.0"` and `port = 5670`; binding to `127.0.0.1` in a manually reviewed config limits local exposure. Do not expose a service publicly merely to make a client test pass. Authentication/CORS and API-key behavior belong in the application/API route when that is the task.

`[models]` is an array-of-tables model catalog. Provider/model-specific fields such as local paths, quantization, controller addresses, and backend flags are owned by `models-and-serving`; do not add guessed fields here.

## Environment interpolation

DB-GPT configuration uses string substitutions of the form:

```toml
api_key = "${env:OPENAI_API_KEY}"
api_base = "${env:OPENAI_API_BASE:-https://api.openai.com/v1}"
```

- `${env:NAME}` reads `NAME` and has no configured fallback.
- `${env:NAME:-fallback}` uses `fallback` when `NAME` is absent.
- The value remains a TOML string until DB-GPT's configuration manager resolves it. An interpolation marker is not proof that the environment variable exists.
- Keep keys and passwords as interpolation references. Do not replace them with sample-looking credentials in a production file; a profile's generated fallback is a placeholder and may allow startup to proceed only to fail at provider call time.
- Environment names in profile generation are provider-specific. For Kimi, the LLM key and embedding key are separate in the 0.8.1 profile spec (`MOONSHOT_API_KEY` and `OPENAI_API_KEY`). Verify this before assuming one provider key can serve both components.

Useful cross-cutting variables include:

| Variable | Use |
|---|---|
| `DBGPT_HOME` | User home and managed profile directory |
| `DBGPT_LOG_DIR` | Runtime log/trace directory override |
| `DBGPT_LANG` | Generated profile language setting |
| `DBGPT_API_KEY` | Click fallback for `setup`/`start web --api-key` |
| `API_ADDRESS` | Default address override for the knowledge CLI |
| `OPENAI_API_KEY`, `OPENAI_API_BASE` | OpenAI-compatible profile/model values |
| `DASHSCOPE_API_KEY` | Tongyi/Qwen profile |
| `MOONSHOT_API_KEY` | Moonshot/Kimi LLM |
| `MINIMAX_API_KEY` | MiniMax profile |
| `ZHIPUAI_API_KEY` | z.ai/Zhipu profile |
| `DBGPT_LOG_LEVEL` | Environment used by some deployed/logging configurations; use `--log-level` or `[system].log_level` when needing an explicit CLI/config setting |

Provider-specific environment names (DeepSeek, SiliconFlow, Ollama, cloud storage, database credentials, and others) are determined by the selected provider/config reference. Route model/backend or connector-specific questions to their owning sub-skill.

## Path and schema facts

- Managed profiles are named TOML files under `$DBGPT_HOME/configs/`; `$DBGPT_HOME/config.toml` stores the active profile under `[default].profile`.
- Relative runtime paths such as `pilot/meta_data/dbgpt.db` and `pilot/data` are rooted at the pip-install workspace under `$DBGPT_HOME/workspace`, not automatically at the directory of the config file.
- `[service.web].host` and `[service.web].port` control the web bind. `start web` has no `--port` option in 0.8.1; change this table and use the same config to start. `stop webserver --port` is a process-selection filter.
- `[service.web.database]` supports the app's configured datasource parameter. The integrated migration helper currently accepts SQLite only, and it resolves a relative SQLite path against the runtime root before creating metadata/migration state.
- `[rag.storage.vector]` selects the vector backend. A parseable Chroma block still requires the corresponding package and writable storage. RAG data shape and backend setup belong to `data-and-rag`.
- Optional sections such as `[service.web.agent_context]`, `[rag]`, `[[models.rerankers]]`, `[[serves]]`, and datasource-specific tables must be copied from a known 0.8.1 public configuration contract. Unknown keys can be ignored, rejected, or fail later depending on the parsed parameter class; do not assume TOML syntax validation equals schema validation.

## Read-only validation

Run the bundled checker against a file before `start` or migration:

```bash
python scripts/inspect_config.py path/to/config.toml
python scripts/inspect_config.py --json path/to/config.toml
```

It checks TOML syntax, expected top-level/table shapes, a valid web port range, SQLite path presence when type is SQLite, model table presence, and the syntax of environment references. It reports model names/providers and only redacted key statuses. It does not read the referenced environment values, access a database, import optional backends, contact a provider, or write a normalized config.

Then ask the installed package for the exact command parser:

```bash
dbgpt start web --help
dbgpt setup --help
dbgpt db migration -c path/to/config.toml upgrade --help
```

For a no-secret smoke test, use a temporary `DBGPT_HOME` and a small TOML fixture. Do not pass a literal production key merely to prove parsing.

## Provider/config route boundary

This route owns whether a config is selected and structurally safe. It does not own:

- model class/provider parameters, controller/worker topology, local model paths, GPU or quantization (`models-and-serving`);
- document parsers, chunk sizes beyond CLI pass-through, vector/graph stores, embedding dimensions, and knowledge internals (`data-and-rag`);
- endpoint request models, API auth, client CRUD, or sandbox policy (`apis-client-and-sandbox`).

When a config mixes these concerns, validate the shared TOML here and hand the specialized sections to the appropriate route rather than duplicating their defaults.
