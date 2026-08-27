# App architecture and state model

This reference explains the H2O LLM Studio Wave app surfaces needed for runtime reasoning and troubleshooting.

## Entry point and request flow

The GUI entry point is the Wave app module `llm_studio.app` with the route `/`.

At import time the module sets `MKL_THREADING_LAYER=GNU`, imports H2O Wave primitives, and wires the route handler. On startup, it initializes logging and records that H2O LLM Studio is starting.

For each Wave request, the route handler follows this sequence:

1. If a chat response is still streaming and another button was clicked, return early so the streaming update can finish.
2. Call `initialize_app(q)` to prepare process-wide `q.app` state once.
3. Copy submitted Wave arguments into `q.client` with `copy_expando(q.args, q.client)`.
4. Call `initialize_client(q)` to prepare per-client state once.
5. Dispatch the request through the central handler.
6. Render the common interface unless the current submission is a chat streaming update.
7. Apply Heap redaction if Heap analytics is enabled.
8. Save the Wave page.

## Process-wide app initialization

`initialize_app(q)` runs once per Wave app process. It:

- Uploads the app icon from the runtime root's static assets.
- Bundles Bokeh inline JavaScript resources into one temporary file and uploads it through Wave so visualization scripts load in order.
- Stores the uploaded script URLs in `q.app["script_sources"]`.
- Marks `q.app["initialized"] = True`.
- Stores the application version, display name, and Heap mode from the default config.

If the first request fails before the UI appears, check the runtime root assets first: missing static icon files, missing package assets, or launching from the wrong current working directory can break this phase.

## Per-client initialization

`initialize_client(q)` runs once per Wave client session. It:

1. Initializes `q.client.delete_cards` and removes the startup card.
2. Creates the derived data, database, output, and download directories if missing.
3. Opens the SQLite database at `<workdir>/data/dbs/user.db` and creates `datasets` and `experiments` tables if they do not exist.
4. Logs the Wave-authenticated user name.
5. Marks the client initialized and enters full-layout mode.
6. Loads user settings and secrets.
7. Renders the common interface.
8. Imports default datasets when dataset id `1` is absent.
9. Sets the first displayed page to `home`.

A failure here usually means the workdir is not writable, the SQLite database is locked or incompatible, settings/secret loading failed, or first-run default dataset preparation hit a dependency/network issue.

## Navigation and request dispatch

The common UI creates a header and navigation groups:

- `Home`
- `Settings`
- `Import dataset`
- `View datasets`
- `Create experiment`
- `Create grid search`
- `View experiments`

The request handler maps Wave submission names to section functions. Relevant app-owned routes include:

- `home`
- `settings`
- `save_settings`
- `load_settings`
- `restore_default_settings`
- dataset import/list/delete/edit/merge navigation
- experiment create/list/compare/display/stop/delete/download actions
- chat tab and chat streaming actions
- `report_error`

When an unknown exception reaches the handler, the app logs the stack trace and displays an error page with `Restart` and `Report` actions. The report card redacts keys and tokens from Wave state before displaying debug details.

## Database model

The app uses a SQLite database file named `user.db` under the `data/dbs` directory. SQLAlchemy creates two tables:

- `datasets`: id, unique dataset name, dataset path, config file path, train row count, optional validation row count.
- `experiments`: id, experiment name, mode, linked dataset name, config file, output path, seed, process id, and GPU list.

The app does not store dataset files or experiment artifacts in the database. It stores filesystem paths that point into `data/user` and `output/user`.

## Settings and secrets

Default settings are defined in the app config and then seeded from environment variables where supported. Important settings categories include connector credentials, default experiment limits, W&B defaults, Hugging Face token and transfer toggle, OpenAI/Azure OpenAI defaults, GPT evaluation sample cap, chart point cap, delete-dialog behavior, and default GPU choices for model download/chat.

Secret keys are identified by setting names containing `api`, `secret`, or `key`. They are not stored in the normal YAML settings file. Non-secret settings are stored in:

```text
<workdir>/data/dbs/<wave-user>.yaml
```

Credential storage choices are:

- `Do not save credentials permanently`: no-op saver; secrets are not loaded back after restart.
- `.env File`: writes a YAML-formatted secret map to `<workdir>/data/dbs/<wave-user>.env`.
- `Keyring`: available only if the host keyring responds during the app's short keyring probe.

The default credential saver is `.env File`. The Settings page warns that Keyring or no persistent credential storage is preferred; `.env File` should be used only when the machine is access-restricted. When a user saves settings, the app clears the same secret keys from non-selected credential stores. Restore-default settings clears secrets from all stores.

Older pickle settings named `<wave-user>.settings` are migrated to YAML settings plus the selected credential saver when detected. If migration fails, the app logs a message asking the user to delete the old settings file and re-enter credentials.

## Workdir and directory helpers

Directory helpers resolve paths as follows:

| Helper behavior | Resolved path |
|---|---|
| User dataset directory | `<workdir>/data/user` |
| Database directory | `<workdir>/data/dbs` |
| Experiment output directory | `<workdir>/output/user` |
| Download staging directory | `<workdir>/output/download` |
| SQLite database file | `<workdir>/data/dbs/user.db` |
| User settings file | `<workdir>/data/dbs/<wave-user>.yaml` |

`<workdir>` is `H2O_LLM_STUDIO_WORKDIR` when set, otherwise the process current working directory at app startup.

## Download links

Download actions create a symlink under `output/download` that points to the requested artifact under `output/user`, then return a relative URL path. This relative URL behavior is intentional so downloads work behind reverse proxies and public cloud IPs. In cloud mode, when `H2O_CLOUD_ENVIRONMENT` is present, the app prepends `H2O_WAVE_BASE_URL` to the generated URL path.

If a download button opens a missing or untrusted path, verify all three pieces together:

1. The experiment artifact exists under `output/user`.
2. The app can create symlinks under `output/download`.
3. `H2O_WAVE_PRIVATE_DIR` maps `/download` to the same `output/download` directory.

## Default datasets

On first client initialization, the app checks whether dataset id `1` exists. If not, it attempts to prepare four default datasets:

- OASST-style causal language modeling data.
- DPO preference data.
- IMDB classification data.
- HelpSteer-style regression data.

When `H2O_LLM_STUDIO_DEMO_DATASETS` is set, these are read from local parquet files. Otherwise, the app uses the `datasets` package to load public datasets. Any exception is caught, the database session is rolled back, and a warning is logged; users can still import their own dataset.

## UI integration-test shape

The optional browser tests use Playwright-style page objects and BDD scenarios. They assume a running app URL and either local login or remote login credentials. Local testing sets `LOCAL_LOGIN=True` and `PYTEST_BASE_URL=localhost:10101`. The scenarios exercise home page loading, local filesystem dataset import/delete, experiment creation with a tiny unit-test backbone, experiment completion polling, and experiment deletion.
