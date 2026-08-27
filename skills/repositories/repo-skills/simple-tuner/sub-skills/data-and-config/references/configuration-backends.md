# Configuration backends and `data_backend_config`

SimpleTuner separates the **training configuration** from the **dataloader configuration**:

- The training config is loaded from `config.json`, `config.toml`, `config.env`, command-line args, or a WebUI/service environment.
- The dataloader config is the JSON file pointed to by `data_backend_config` / `--data_backend_config` / `DATALOADER_CONFIG`.
- If no dataloader path is provided, SimpleTuner falls back to `multidatabackend.json` under the active config path.

Do not start training from this sub-skill. Use this file to resolve what config a training workflow would use, then route launch/distributed/runtime work to `training-workflows`.

## Backend selection precedence

SimpleTuner's loader uses these environment variables and fallbacks:

1. Environment name:
   - `SIMPLETUNER_ENVIRONMENT`
   - then `SIMPLETUNER_ENV`
   - then `ENV`
   - then `default`
2. Config backend:
   - `SIMPLETUNER_CONFIG_BACKEND`
   - then `CONFIG_BACKEND`
   - then `CONFIG_TYPE`
   - then auto-detection
3. Auto-detection checks, in order, for:
   - `config.json`
   - `config.toml`
   - `config.env`

For the default environment, the auto-detection base is `config/`. For a named environment, it is `config/<environment>/`.

Supported backend values are:

| Backend | Loader input | Main path behavior |
|---|---|---|
| `json` | JSON object mapping config keys to CLI-style args. | Default `config/config.json`; env-specific `config/<ENV>/config.json`; JSON additionally honors `CONFIG_PATH`. |
| `toml` | TOML mapping of config keys to CLI-style args. | Default `config/config.toml`; env-specific `config/<ENV>/config.toml`. |
| `env` | Environment variables mapped to CLI-style args. | Searches `config.env`, `config/config.env`, and `config/<ENV>/config.env`; `DATALOADER_CONFIG` maps to `--data_backend_config`. |
| `cmd` | Direct command-line parser input. | Used when invoking lower-level commands manually; route launch details to `training-workflows`. |

## JSON backend path details

The JSON loader checks `CONFIG_PATH` first:

- If `CONFIG_PATH` points to a directory, it tries `CONFIG_PATH/config.json`.
- If `CONFIG_PATH` points to a file or stem, it tries that file and a `.json` suffixed form.
- With an environment name, it also tries direct env paths, `config/<ENV>/config.json`, and packaged example-style locations.

This makes JSON the most flexible backend when a caller needs an explicit config path override.

## TOML and env backend caveat

In the inspected SimpleTuner version, TOML and env loading primarily follow `config/<ENV>/config.toml` and `config/<ENV>/config.env` patterns. If a non-JSON `CONFIG_PATH` override does not behave as expected, use one of these safer routes:

- Place the file under `config/<ENV>/config.toml` or `config/<ENV>/config.env` and run with the matching environment name.
- Convert the training config to JSON and set `CONFIG_BACKEND=json` with `CONFIG_PATH`.
- Use the WebUI/config service to create an environment folder containing `config.json` and `multidatabackend.json` together.

## Training config key spelling

Config files may use either dash-prefixed CLI keys or normalized keys, depending on the path that created the config. SimpleTuner normalizes mappings to CLI-style args.

Examples:

```json
{
  "data_backend_config": "config/my-env/multidatabackend.json",
  "model_family": "flux",
  "output_dir": "output/my-run"
}
```

```json
{
  "--data_backend_config": "config/my-env/multidatabackend.json",
  "--model_family": "flux",
  "--output_dir": "output/my-run"
}
```

For env files, use the mapped variable name:

```bash
ENV=my-env
CONFIG_BACKEND=json
DATALOADER_CONFIG=config/my-env/multidatabackend.json
```

## Placeholder expansion

String values loaded from `config.json` and `config.toml` support environment placeholders:

```json
{
  "data_backend_config": "config/{env:DATASET_CONFIG_NAME}.json"
}
```

String values inside the referenced dataloader JSON also support:

- `{env:VAR_NAME}` from the process environment.
- `{model_family}` from the active training config.
- `{output_dir}` from the active training config, falling back to a local output directory if missing.
- `{id}` from the current dataset entry.

Example dataloader path template:

```json
{
  "id": "portraits",
  "type": "local",
  "dataset_type": "image",
  "instance_data_dir": "{env:DATA_ROOT}/{model_family}/{id}",
  "cache_dir_vae": "{output_dir}/cache/vae/{id}"
}
```

Do not place credentials or secrets into generated runtime docs. For S3/HF credentials, prefer environment variables or the user's credential manager and only record the required variable names in task notes.

## How to resolve a user's active dataloader

1. Determine whether the user is using `simpletuner train env=<name>`, an example, WebUI-created environment, or direct config files.
2. Resolve config backend from explicit CLI/env values before auto-detection.
3. Load or inspect the selected training config file without starting training.
4. Read `data_backend_config` / `--data_backend_config` / `DATALOADER_CONFIG`.
5. If absent, assume `multidatabackend.json` under the active config directory.
6. Validate the resolved JSON dataloader with the bundled validator.

## WebUI environment and maintainer note

The WebUI/config service stores environments as folders containing `config.json` plus dataloader files such as `multidatabackend.json`, and it rewrites paths so the environment folder is self-contained.

When **changing SimpleTuner source code** to add or rename a dataloader option, do not stop at backend parsing. Route to `repo-development` and require updates to the WebUI dataset blueprint/template surface (`simpletuner/simpletuner_sdk/server/data/dataset_blueprints.py`) plus docs/translations as appropriate. This sub-skill can describe the runtime schema, but maintainer test/doc policy belongs to `repo-development`.

## Source evidence distilled

This reference is based on `simpletuner/helpers/configuration/loader.py`, `json_file.py`, `toml_file.py`, `env_file.py`, `template_vars.py`, `simpletuner/cli/common.py`, `simpletuner/cli/train.py`, `simpletuner/helpers/configuration/cmd_args.py`, `tests/test_config_templates.py`, `tests/test_config_management.py`, `tests/test_configs_service_environment.py`, and the public `documentation/INSTALL.md` / `documentation/OPTIONS.md` config sections.
