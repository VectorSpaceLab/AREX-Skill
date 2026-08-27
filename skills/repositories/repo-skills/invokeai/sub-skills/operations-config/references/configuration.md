# InvokeAI Operations and Configuration

## Package and Entry Points

- Distribution name: `InvokeAI`.
- Evidence package version: `6.13.0.post1`.
- Supported Python range from package metadata: `>=3.11,<3.13`.
- Console scripts:
  - `invokeai-web` -> `invokeai.app.run_app:run_app`
  - `invoke-useradd` -> `invokeai.app.util.user_management:useradd`
  - `invoke-userdel` -> `invokeai.app.util.user_management:userdel`
  - `invoke-userlist` -> `invokeai.app.util.user_management:userlist`
  - `invoke-usermod` -> `invokeai.app.util.user_management:usermod`
- Full server startup requires the application dependency set, including FastAPI, uvicorn, Torch, pydantic-settings, python-socketio, passlib/bcrypt, python-jose, and model/backend dependencies. Do not claim an inspection-only environment can start the server unless these dependencies are actually installed.

## `invokeai-web` CLI

`invokeai-web` parses CLI args before importing most of the app so command-line settings can override file/env settings. Supported public flags are:

- `--root PATH`: runtime root directory.
- `--config PATH`: path to `invokeai.yaml`; if relative, it is resolved under the runtime root.
- `--version`: print the package version and exit.

Use `scripts/inspect_cli_help.py --command invokeai-web` to inspect help safely. This helper imports only the lightweight parser when possible and never starts uvicorn.

## Root and Config Resolution

When the full entry point parses args, `get_config()` resolves the runtime root and config as follows:

1. CLI `--root` sets the root when provided.
2. Otherwise `INVOKEAI_ROOT` is used.
3. Otherwise the active virtual environment parent is used when `VIRTUAL_ENV` is set.
4. Otherwise the default is `~/invokeai`.

The config file path is `--config` when provided, otherwise `invokeai.yaml` under the resolved root. Path-like settings such as `models_dir`, `db_dir`, `outputs_dir`, `custom_nodes_dir`, `style_presets_dir`, `workflow_thumbnails_dir`, `profiles_dir`, cache directories, and legacy config directories resolve relative to the runtime root unless they are absolute.

## Settings Precedence

The config implementation uses pydantic-settings with `INVOKEAI_` env vars, YAML migration/loading, and CLI-private root/config fields. Operational precedence is:

1. CLI `--root` and `--config` determine where root/config files are read from during full startup.
2. Environment variables with prefix `INVOKEAI_` populate config fields, for example `INVOKEAI_HOST`, `INVOKEAI_PORT`, `INVOKEAI_MULTIUSER`, and `INVOKEAI_EXTERNAL_OPENAI_API_KEY`.
3. Existing `invokeai.yaml` values are merged without clobbering fields already supplied by env vars.
4. `api_keys.yaml` values for external provider keys/base URLs are merged after `invokeai.yaml`, but still do not override env vars.
5. Built-in defaults fill any remaining unset fields.

A full app startup writes `invokeai.example.yaml` and creates `invokeai.yaml` if missing. Tests assert that env/default values are not written into `invokeai.yaml` unless they were explicitly set in the file update path.

## Runtime Root Layout

Common runtime files/directories under the root are:

- `invokeai.yaml`: primary user-editable config, with `schema_version` metadata.
- `api_keys.yaml`: external provider API keys and base URLs; preferred persistence location for sensitive external provider config.
- `databases/invokeai.db`: default SQLite database path.
- `models/`: installed model records and model files.
- `models/.download_cache`: download cache.
- `models/.convert_cache`: legacy converted model cache retained for migration compatibility.
- `outputs/`: generated outputs.
- `nodes/`: custom nodes directory; route authoring/import issues to `../workflow-nodes/SKILL.md`.
- `style_presets/`, `workflow_thumbnails/`, `profiles/`, and `configs/`: operational support directories.

## Key Operational Settings

Use `scripts/summarize_settings.py` for the full bundled settings catalog. High-value categories for server operations:

- Web: `host`, `port`, `allow_origins`, `allow_credentials`, `allow_methods`, `allow_headers`, `ssl_certfile`, `ssl_keyfile`.
- Logging: `log_handlers`, `log_format`, `log_level`, `log_sql`, `log_level_network`.
- Paths: `models_dir`, `db_dir`, `outputs_dir`, `custom_nodes_dir`, `style_presets_dir`, `workflow_thumbnails_dir`, cache directories.
- Queue/session retention: `max_queue_size`, `clear_queue_on_startup`, `max_queue_history`.
- Auth: `multiuser`, `strict_password_checking`.
- Node controls: `allow_nodes`, `deny_nodes`, `node_cache_size`.
- Backend memory/device: `pytorch_cuda_alloc_conf`, `device`, `precision`, `attention_type`, cache memory limits. Route deep model/cache interpretation to `../model-management/SKILL.md`.
- External providers: `external_alibabacloud_*`, `external_gemini_*`, `external_openai_*`, `external_seedream_*`; API keys are separated into `api_keys.yaml` by runtime config update endpoints.

## Server Startup Ordering

`invokeai-web` startup has ordering constraints that matter for troubleshooting:

1. Parse CLI args immediately.
2. Import uvicorn and load config with `get_config()`.
3. Create the InvokeAI logger.
4. If `pytorch_cuda_alloc_conf` is set, configure the Torch CUDA allocator before importing modules that import Torch.
5. Import invocation registry, custom node loader, and device helpers after allocator configuration.
6. Detect Torch device and run startup utilities.
7. If the requested port is occupied, find the first open port and update the in-memory config, logging a warning.
8. Initialize the FastAPI app/event loop and API dependencies.
9. Load custom nodes after core invocation classes are imported to detect clobbering of core node types.
10. Optionally enable development reload.
11. Start uvicorn with configured host, port, network log level, and SSL cert/key files.
12. On keyboard interrupt, shut down services, cancel pending asyncio tasks, shut down the default thread executor, close the loop, and log remaining non-daemon threads.

Because allocator setup must happen before Torch import, avoid diagnostic snippets that import `torch` before checking `pytorch_cuda_alloc_conf` when investigating CUDA allocator behavior.

## Source Script Decisions

- The original web wrapper only changed cwd to the repository root before calling `run_app()`. The bundled replacement is `scripts/inspect_cli_help.py`, which safely inspects CLI help without starting the server.
- The original OpenAPI generator changed cwd and imported the full FastAPI app. The bundled replacement is `scripts/inspect_openapi_routes.py`, which works from arbitrary cwd, supports safe fallback route-family output, and reports missing dependencies clearly.
- The generated settings JSON is bundled as `references/settings-catalog.json` and summarized by `scripts/summarize_settings.py`.
- Gallery maintenance is intentionally reference-only/excluded: it removes orphan image files, removes orphan DB rows, and regenerates thumbnails, so it is mutating operational maintenance rather than safe inspection.
