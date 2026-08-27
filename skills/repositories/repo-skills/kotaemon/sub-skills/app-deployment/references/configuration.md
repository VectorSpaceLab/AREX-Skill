# App Configuration

Kotaemon app configuration is split across `.env`, `flowsettings.py`, app database state, and UI-managed settings.

## Configuration layers

1. Environment and `.env` variables are read with `python-decouple` by `flowsettings.py` and app modules.
2. `flowsettings.py` defines developer/operator defaults: app data paths, default stores, feature flags, first setup, user management, initial model specs, GraphRAG index types, and user-facing settings schemas.
3. On first setup and through the Resources/Settings UI, Kotaemon persists models, users, and user settings in the app database under `ktem_app_data/user_data/`.
4. After the database exists, editing `.env` may not replace values already saved through the UI; inspect Resources and Settings when behavior does not match the file.

## `.env` keys to inspect

Use `.env.example` as the template for a local source deployment. Common deployment keys:

| Area | Keys | Notes |
| --- | --- | --- |
| OpenAI | `OPENAI_API_BASE`, `OPENAI_API_KEY`, `OPENAI_CHAT_MODEL`, `OPENAI_EMBEDDINGS_MODEL` | Placeholder key `<YOUR_OPENAI_KEY>` still creates non-usable OpenAI defaults. |
| Azure OpenAI | `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `OPENAI_API_VERSION`, `AZURE_OPENAI_CHAT_DEPLOYMENT`, `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT` | Both endpoint and key are needed before Azure models are seeded. |
| Cohere/rerank | `COHERE_API_KEY` | Default reranker config uses Cohere; missing/placeholder keys can affect reranking. |
| Local model | `LOCAL_MODEL`, `LOCAL_MODEL_EMBEDDINGS`, `KH_OLLAMA_URL` | `KH_OLLAMA_URL` defaults to `http://localhost:11434/v1/`; Docker deployments often need a non-localhost URL. |
| GraphRAG | `GRAPHRAG_API_KEY`, `GRAPHRAG_LLM_MODEL`, `GRAPHRAG_EMBEDDING_MODEL`, `USE_CUSTOMIZED_GRAPHRAG_SETTING`, `USE_NANO_GRAPHRAG`, `USE_LIGHTRAG`, `USE_MS_GRAPHRAG` | Detailed GraphRAG/provider tuning belongs in `../../model-providers/SKILL.md`. |
| PDF viewer | `PDFJS_VERSION_DIST`, `PDFJS_PREBUILT_DIR` | If `PDFJS_PREBUILT_DIR` is unset, the default package prebuilt path is used. |
| Auth | `AUTHENTICATION_METHOD`, `KEYCLOAK_SERVER_URL`, `KEYCLOAK_CLIENT_ID`, `KEYCLOAK_REALM`, `KEYCLOAK_CLIENT_SECRET` | Keycloak values matter only for Keycloak auth deployments. |
| App flags | `KH_GRADIO_SHARE`, `KH_FIRST_SETUP`, `KH_ENABLE_FIRST_SETUP`, `KH_DEMO_MODE` | `KH_FIRST_SETUP=true` forces first-setup behavior for recovery/testing. |

Run a read-only check:

```bash
python skills/kotaemon/sub-skills/app-deployment/scripts/check_app_config.py --env-file .env --repo-root .
```

The script warns on missing core keys, placeholder key-like values, questionable local-provider URLs in Docker contexts, missing PDF.js assets, and writable app-data hints.

## `flowsettings.py` operator defaults

Important values defined in `flowsettings.py`:

- `KH_APP_DATA_DIR`: defaults to `ktem_app_data` beside `flowsettings.py` and is created at import time.
- `KH_USER_DATA_DIR`: `KH_APP_DATA_DIR/user_data`; contains SQLite state, uploaded files, docstore, and vectorstore.
- `KH_DATABASE`: defaults to SQLite at `KH_USER_DATA_DIR/sql.db`.
- `KH_FILESTORAGE_PATH`: defaults to `KH_USER_DATA_DIR/files`.
- `KH_DOCSTORE`: defaults to `kotaemon.storages.LanceDBDocumentStore` under `user_data/docstore`.
- `KH_VECTORSTORE`: defaults to `kotaemon.storages.ChromaVectorStore` under `user_data/vectorstore`.
- `KH_REASONINGS`: registers built-in reasoning pipelines: full QA, decomposition, ReAct, and ReWOO.
- `KH_INDEX_TYPES` and `KH_INDICES`: register file and optional GraphRAG collection types.
- `KH_FEATURE_USER_MANAGEMENT`, `KH_FEATURE_USER_MANAGEMENT_ADMIN`, `KH_FEATURE_USER_MANAGEMENT_PASSWORD`: control built-in login/user management.
- `KH_ENABLE_FIRST_SETUP`: controls first-run setup page creation; `KH_FIRST_SETUP=true` can force the first-setup flow.

If a task asks for custom pipelines, custom index classes, or `flowsettings.py` extension code, route to `../../extensions/SKILL.md`.

## First setup and login

At startup, `ktem.main.App` decides whether to show the first setup page based on `KH_ENABLE_FIRST_SETUP`, `KH_DEMO_MODE`, and whether app data existed. `KH_FIRST_SETUP=true` forces the app to behave as if setup is needed.

The setup page supports Cohere, Google, OpenAI, and Ollama choices. It stores selected LLM, embedding, and reranking defaults through app managers, then tests LLM/embedding connectivity. Ollama setup may attempt model pulls from the Ollama API, which is a network/disk side effect.

Default user-management behavior:

- `KH_FEATURE_USER_MANAGEMENT` defaults true in `flowsettings.py`.
- The admin username/password default to `admin`/`admin` unless overridden.
- When user management is enabled, the initial visible tab is `Welcome`; after sign-in, tabs become visible.
- Admin users can see `Resources`; regular users see operational tabs but not the admin resource management tab.

If the user reports “only Welcome is visible” or “Resources is missing,” check login state, admin role, and `KH_FEATURE_USER_MANAGEMENT` before changing model configuration.

## Resources tab

The Resources tab is the operator/admin location for persistent app resources:

- LLM models.
- Embedding models.
- Reranking models.
- User management when enabled and the signed-in user is admin.

Use Resources to correct wrong API keys, wrong model names, or default-model choices after first setup. For provider-specific fields and local model URL semantics, route detailed work to `../../model-providers/SKILL.md`.

## Settings tab

Kotaemon renders user settings declared by registered indexes and reasoning pipelines. Typical settings include reasoning choice, output language, retrieval knobs, file loader, and index-specific options.

Settings are not the same as `.env`:

- `.env` seeds/developer config before or during startup.
- Settings are runtime user preferences saved in the app database.
- A bad file-loader selection can look like an ingestion failure even when deployment is healthy; route parser-specific diagnosis to `../../document-ingestion/SKILL.md`.

## Gradio/static paths

`app.py` launches Gradio with allowed paths for `libs/ktem/ktem/assets` and `GRADIO_TEMP_DIR`. `ktem.app.BaseApp` injects `PDFJS_PREBUILT_DIR` into the PDF viewer JavaScript and honors `GR_FILE_ROOT_PATH` as a static file root prefix.

Check these when browser-side previews fail but backend chat/indexing works:

- `PDFJS_PREBUILT_DIR` points to an existing PDF.js distribution.
- `GRADIO_TEMP_DIR` is writable by the app process.
- Reverse proxy/static root settings preserve Gradio file URLs.

## `settings.yaml.example`

`settings.yaml.example` is for customized MS GraphRAG settings when `USE_CUSTOMIZED_GRAPHRAG_SETTING=true`. It includes OpenAI-compatible API base examples, embedding settings, chunking, storage, cache, and reporting settings. Do not edit it for ordinary app startup unless the task is specifically about customized GraphRAG; route detailed GraphRAG work to `../../model-providers/SKILL.md`.
