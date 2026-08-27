# App Troubleshooting

Use this decision tree for deployment, startup, PDF viewer, login, update, and migration issues. Prefer read-only checks before running side-effectful launch/update/migration scripts.

## Start with safe diagnostics

From a Kotaemon checkout or copied deployment directory:

```bash
python skills/kotaemon/sub-skills/app-deployment/scripts/check_app_config.py --env-file .env --repo-root .
```

For a proposed Chroma migration:

```bash
python skills/kotaemon/sub-skills/app-deployment/scripts/inspect_chroma_migration_inputs.py \
  --chroma-dir ktem_app_data/user_data/vectorstore \
  --sqlite-uri sqlite:///ktem_app_data/user_data/sql.db
```

These scripts do not start servers, download files, import heavy provider packages, or modify user data.

## App will not launch

Check in order:

1. Python version is 3.10+ and the active environment is the intended one.
2. Required packages are installed for the selected install mode (`uv sync`, Docker image, or editable `libs/kotaemon` plus `libs/ktem`).
3. The app process can write `ktem_app_data/`, especially `user_data/`, cache directories, and `gradio_tmp/`.
4. `GRADIO_SERVER_PORT` is free and the bind address is reachable (`0.0.0.0` for containers/remote access, loopback for local-only use).
5. Optional parser/provider errors correspond to optional workflows, not base app startup.

If broad dependency installation is slow, avoid repeatedly reinstalling all extras. Confirm the user’s actual workflow first, then install only the optional parser/provider packages it needs.

## Missing or placeholder API keys

Symptoms:

- First setup connection tests fail.
- Chat fails even though the UI loads.
- Reranking or embeddings fail after upload/indexing.
- `.env` contains values such as `<YOUR_OPENAI_KEY>`, `<COHERE_API_KEY>`, `your-key`, or blank Azure fields.

Recovery:

1. Use `check_app_config.py` to identify placeholder or blank key-like variables without printing secrets.
2. If this is the first launch, fix `.env` and restart.
3. If app data already exists, update the saved model entries in `Resources -> LLMs`, `Resources -> Embedding Models`, and `Resources -> Reranking Models`.
4. For provider-specific base URLs, deployment names, model names, or GraphRAG keys, route to `../../model-providers/SKILL.md`.

## Wrong Docker host URL for local providers

Symptoms:

- Ollama or OpenAI-compatible local server works on the host but not from Docker.
- `KH_OLLAMA_URL` or a model base URL uses `http://localhost:11434/v1/` inside a container.

Recovery:

- Explain that `localhost` inside a container points to the container itself.
- Use a Docker-reachable host address such as a host gateway name on supported platforms or the host LAN IP.
- Update the saved model configuration in Resources if the database already exists; changing only `.env` may not update saved resources.

## PDF viewer is missing or blank

Symptoms:

- Chat answers and citations appear, but PDF preview/highlight does not render.
- Browser console or app logs mention PDF.js or missing static viewer files.

Recovery:

1. Run `check_app_config.py --repo-root .` and inspect the PDF.js section.
2. Confirm `PDFJS_PREBUILT_DIR` or the default package prebuilt directory exists.
3. Confirm the directory resembles a PDF.js distribution, commonly with `web/` and `build/` content.
4. If assets are absent, ask before running any download helper because it performs a network download and writes into the install tree.
5. For reverse proxy deployments, verify Gradio static file URLs and `GR_FILE_ROOT_PATH` behavior.

## First setup or login confusion

Symptoms:

- The app opens to a Welcome page instead of Chat.
- Resources is not visible.
- Default `admin`/`admin` credentials do not work after a previous setup.

Recovery:

- `KH_ENABLE_FIRST_SETUP` enables the first setup wrapper; `KH_FIRST_SETUP=true` forces setup mode.
- User management defaults enabled; login gates the main tabs.
- Admin credentials are configured by `KH_FEATURE_USER_MANAGEMENT_ADMIN` and `KH_FEATURE_USER_MANAGEMENT_PASSWORD` only for initial/admin setup, not necessarily after user changes in the database.
- Resources is shown to admin users; a regular signed-in user may not see it.
- If state is corrupted, back up `ktem_app_data/` before considering resets or database edits.

## Data directory permissions or corruption

Symptoms:

- SQLite cannot open the database.
- Uploads fail or files disappear.
- Chroma/docstore errors after moving an install.
- Gradio temp files fail to write.

Recovery:

1. Identify `KH_APP_DATA_DIR`; default is `ktem_app_data` beside `flowsettings.py`.
2. Check ownership and write permissions for `user_data/`, `files/`, `vectorstore/`, `docstore/`, caches, and `gradio_tmp/`.
3. If moving across machines, copy the entire `ktem_app_data/` tree, not just the SQLite file.
4. Before any cleanup, zip or snapshot the app-data directory.

## Update scripts mutate environment

The release update scripts activate the installer-managed conda environment and reinstall Kotaemon packages from Git sources. In source checkouts, they tell the user to perform `git pull` manually. Windows update also writes a `VERSION` file after update.

Before update:

- Back up `ktem_app_data/`.
- Record current package versions and whether this is a source checkout or release-style install.
- Check whether optional parser/provider packages were manually installed.
- Warn that update scripts can change packages and environment state; ask for explicit approval.

If update fails, do not delete app data. Repair or recreate the environment separately, then point the app back at the preserved data directory.

## Chroma migration risk

The source Chroma migration code opens a Chroma persistent client and SQLite database, reads file index rows, then updates Chroma metadatas with `file_id`. That is a real mutation of vectorstore contents.

Safe preflight:

```bash
python skills/kotaemon/sub-skills/app-deployment/scripts/inspect_chroma_migration_inputs.py \
  --chroma-dir <path-to-vectorstore> \
  --sqlite-uri sqlite:///<path-to-sql.db> \
  --index-id 1
```

Proceed with any mutating migration only after:

- A full `ktem_app_data/` backup exists.
- The source Chroma directory and SQLite database are clearly the same app instance.
- The expected `index__<id>__source` and `index__<id>__index` tables exist, or the top-level app `index` table confirms the available index IDs.
- The user accepts the risk of updating Chroma metadata.

## Optional parser/provider packages missing

Kotaemon supports many optional integrations. A base app can load while specific features fail due to missing dependencies:

- Extra document types may need `unstructured`, Docling, PaddleOCR, Azure Document Intelligence, Adobe PDF Extract, or other parser packages.
- Vector/doc stores beyond defaults may need Chroma, LanceDB, Milvus, Qdrant, Elasticsearch, or compatible services.
- Provider entries may need SDK packages and credentials.
- GraphRAG variants may add dependency conflicts; NanoGraphRAG/LightRAG/MS GraphRAG should be handled deliberately.

Route parser-specific tasks to `../../document-ingestion/SKILL.md` and provider/GraphRAG-specific tasks to `../../model-providers/SKILL.md`.

## Hard usability cases for verification

- Recover a local source install where `.env` still contains placeholder OpenAI/Cohere keys, `LOCAL_MODEL` is set, `KH_OLLAMA_URL` is wrong for Docker, and PDF.js assets are missing; expected outcome is a safe diagnostic report and a launch plan that does not expose secrets or start services.
- Preflight a Chroma migration where SQLite exists but one `index__<id>__source` table is missing; expected outcome is a non-mutating report that identifies the missing table and requires backup/user approval before migration.
