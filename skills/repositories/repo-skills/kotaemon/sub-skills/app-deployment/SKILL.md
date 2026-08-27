---
name: app-deployment
description: "Install, launch, configure, and troubleshoot the Kotaemon Gradio
  app for document QA users and operators."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Kotaemon App Deployment

Use this sub-skill when the task is to get the Kotaemon Gradio application running, diagnose its runtime configuration, prepare a safe update or data migration, or explain the operator-facing UI for document QA.

## Route here for

- Docker vs local installation decisions, including `uv`, conda, editable installs, and release-style launch scripts.
- `.env`, `flowsettings.py`, `settings.yaml.example`, Gradio, first setup, login, app-data, PDF.js, and Resources/Settings tab behavior.
- Safe diagnostics before launch, update, or Chroma migration; use the bundled scripts instead of running app/update/migration scripts blindly.
- Operator troubleshooting for missing credentials, placeholder model defaults, local-provider URLs, data permissions, optional parsers/providers, PDF viewer assets, and broad dependency installs.

## Do not use this for

- Custom component, plugin, page, or flow authoring; use `../extensions/SKILL.md`.
- Low-level `kotaemon` RAG APIs, indexes, retrieval, document objects, or QA pipelines; use `../rag-core/SKILL.md`.
- Provider-specific model tuning, GraphRAG details, local model server tuning, or credential semantics beyond app deployment checks; use `../model-providers/SKILL.md`.

## Fast workflow

1. Pick the deployment mode using `references/deployment.md`: Docker for isolated operator use, local `uv`/conda for source/developer installs, Hugging Face duplicate Space for online installs.
2. Check runtime configuration with `references/configuration.md` and run `python scripts/check_app_config.py --env-file .env --repo-root .` from a Kotaemon checkout or copied deployment directory.
3. For first-run issues, login/resource visibility, PDF viewer problems, data directory permissions, updates, or migrations, follow `references/troubleshooting.md`.
4. Before any Chroma metadata migration, run `python scripts/inspect_chroma_migration_inputs.py --chroma-dir <vectorstore-dir> --sqlite-uri sqlite:///<sql.db>` and back up `ktem_app_data` before mutating anything with external migration code.

## Safety rules

- Do not start `python app.py`, run Docker, execute release scripts, download PDF.js, update packages, pull local models, or mutate Chroma/SQLite data unless the user explicitly approves side effects.
- Treat `.env` as a first-run seeding mechanism for models/credentials; after the app database exists, Resources and Settings UI entries may override what the file originally seeded.
- Never print secrets. The bundled config script reports whether key-like values are missing or placeholders, not the values themselves.
- Back up `ktem_app_data/` before update or migration work; it contains user uploads, SQLite state, vector/doc stores, caches, and model cache directories.

## Bundled references

- `references/deployment.md` - install modes, launch choices, data directory, PDF.js, Docker/local/HF notes.
- `references/configuration.md` - `.env`, `flowsettings.py`, app settings/resources tabs, first setup/login, Gradio settings.
- `references/troubleshooting.md` - diagnostic decision tree, safe update/migration cautions, common failure modes.

## Bundled scripts

- `scripts/check_app_config.py` - read-only `.env` and PDF.js/app-data diagnostic; never starts Kotaemon.
- `scripts/inspect_chroma_migration_inputs.py` - read-only Chroma/SQLite migration preflight; never updates collections or SQL rows.
