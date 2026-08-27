# MineContext cross-cutting troubleshooting

## Purpose

Read this first when an issue could be caused by installation, imports,
configuration, credentials, local data paths, or mixed backend/frontend build
state. Then follow the workflow-specific troubleshooting linked from the owning
sub-skill.

## Installation and import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: opencontext` | The `MineContext` distribution was not installed in the active Python environment. | Install the backend package, then run `python -c "import opencontext; print(opencontext.__version__)"`. Use the bundled `scripts/check_runtime.py` for a broader smoke check. |
| `opencontext: command not found` | Console entry point was not installed or the wrong environment is active. | Run `python -m pip show MineContext` in the intended environment, reinstall with `python -m pip install -e .`, and use `python -m opencontext.cli --help` as a fallback check. |
| `pip check` reports dependency conflicts | Mixed user/global packages or a stale environment. | Use a fresh environment with Python 3.10-3.12, install the package once, and avoid mixing frontend/node dependencies into the Python env. |
| Import fails inside storage, web-link, or document modules | Optional runtime dependency missing or incompatible. | Install the package from its runtime metadata. Do not install only a subset if the task needs storage, document processing, or web-link capture. |

## Configuration and secret handling

- `config/config.yaml` uses environment interpolation. Empty values can appear
  when variables such as `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`,
  `EMBEDDING_BASE_URL`, `EMBEDDING_API_KEY`, or `EMBEDDING_MODEL` are missing.
- `${CONTEXT_PATH:.}` controls local data, log, screenshot, ChromaDB, and SQLite
  paths. If data appears in an unexpected place, inspect the effective config
  rather than assuming a fixed application directory.
- User settings are merged from `user_setting_path`; API/UI settings updates may
  override base YAML without modifying the base file.
- Prompt language is controlled by the `prompts.language` config key and loads a
  matching prompt YAML file. Missing prompt files can break generation and
  completion routes.
- Never paste API keys, signing credentials, local `CONTEXT_PATH`, private model
  endpoints, or absolute data paths into public notes.

## Model-service failures

MineContext can import without working model credentials, but many workflows
need a model endpoint at runtime.

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `API key, base URL, and model must be provided` | LLM or embedding config was empty after env interpolation. | Set the model settings in YAML, user settings, or the model-settings API. Confirm both chat/VLM and embedding values. |
| Provider validation fails | Wrong endpoint, provider, model id, output dimension, or credential. | Use the model-settings validation route before running capture/generation. For Doubao, ensure both visual-language and embedding models are enabled in the provider console. |
| Screenshot, report, todo, or tip generation hangs or errors | External service unavailable, no local OpenAI-compatible server, or network policy blocks calls. | Stop native generation checks until a model endpoint is explicitly available. Use offline smoke scripts for package/runtime validation. |

## Local storage failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| ChromaDB initialization fails | Bad local path, permissions, or incompatible installed ChromaDB version. | Check the effective `storage.backends` entry and ensure the local persistence directory is writable. |
| Qdrant search/upsert fails | Config switched to Qdrant but server/path/vector size is wrong. | Confirm `vector_size` matches `embedding_model.output_dim`; verify local/server Qdrant connectivity before blaming retrieval logic. |
| SQLite table errors | Old database schema, deleted local data, or unwritable path. | Use a new `CONTEXT_PATH` for isolation or back up/reset the SQLite file. Avoid destructive resets without user approval. |

## Runtime vs packaging issues

- If `opencontext --help` works but the desktop app cannot start, switch to
  [desktop-packaging troubleshooting](../sub-skills/desktop-packaging/references/troubleshooting.md).
- If the desktop app opens but API routes, generation, or capture fail, switch
  to [runtime-service troubleshooting](../sub-skills/runtime-service/references/troubleshooting.md).
- If a build script deletes `dist/` or `frontend/backend/`, treat it as a
  mutating packaging operation and ask before rerunning on a user workspace.

## Safe diagnostic order

1. Run `python scripts/check_runtime.py` from the skill directory or import the
   package with the environment's Python.
2. Run `opencontext --help` and inspect CLI startup options.
3. Inspect effective configuration and environment variables without printing
   secrets.
4. For runtime workflows, use bundled deterministic smokes before model/network
   examples.
5. For packaging workflows, run the packaging preflight before build commands.
