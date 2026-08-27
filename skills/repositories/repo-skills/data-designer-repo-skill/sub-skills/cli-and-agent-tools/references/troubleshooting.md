# CLI and Agent Tool Troubleshooting

Use this when a `data-designer` command fails, emits surprising local state, or needs a safe recovery path.

## Command availability

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `data-designer: command not found` | Console script is not on `PATH` or the package is not installed in the active environment. | Activate the intended environment, reinstall the package, or try `python -m data_designer.cli.main --help`. |
| `No module named data_designer` with `python -m ...` | Current Python cannot import the package. | Use the installed package environment. |
| CLI crashes during help/import | Incomplete runtime dependencies. | Repair the package environment before debugging config files. |

## API keys and usable aliases

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `agent context` says `No usable model aliases` | Defaults may exist, but providers/API keys are not configured. | Run `data-designer config providers` and `data-designer config models`, set required key env vars, then re-run `agent state model-aliases`. |
| Alias reason says provider is missing an API key | Provider exists but its key reference is unresolved. | Set `NVIDIA_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, or the provider's custom key variable/value. |
| Alias reason says provider is not configured | Model alias references an absent provider. | Add/rename the provider through `config providers`; confirm with `config list`. |
| `check-models` fails after aliases look usable | External provider or MCP tool probe failed. | Check endpoint/network/key/tool config. `validate` is internal readiness; `check-models` is external readiness. |

## Config source and Python script args

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Config source not found` or `not a file` | Wrong path or directory passed as `CONFIG_SOURCE`. | Pass an existing local file or supported remote YAML/JSON URL. |
| `Unsupported file extension` | Source is not `.yaml`, `.yml`, `.json`, or local `.py`. | Use a supported extension. Remote `.py` modules are rejected. |
| `Script arguments are only supported for local Python config modules` | Args were supplied to YAML/JSON/remote config or placed before `--`. | Use a local `.py` config and put args after `--`: `data-designer validate workflow.py -- --seed-path seeds.parquet`. |
| Missing `load_config_builder()` | Local Python module lacks the required function. | Define `load_config_builder()` returning `DataDesignerConfigBuilder`; route object fields to `config-authoring`. |
| Script args rejected by function signature | Function has zero args while args were supplied, or an unsupported signature. | Accept exactly one `DataDesignerScriptParams` parameter or remove forwarded args. |

## `create --run-config`

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `CONFIG_SOURCE` reported missing | `--run-config` does not replace the dataset config argument. | Use `data-designer create CONFIG_SOURCE --run-config run-config.yaml`. |
| Run config URL or JSON rejected | Run configs must be local `.yaml` or `.yml`. | Use a local YAML file. |
| Extra/invalid field errors | YAML root is not a direct `RunConfig` mapping or contains invalid values. | Remove any `run_config:` wrapper; keep only valid `RunConfig` fields. Partial YAML is valid. |
| Nested settings do not behave as expected | Nested mappings are validated as `RunConfig` fields and omitted nested fields use model defaults. | Make nested sections explicit and route runtime behavior to `generation-runtime`. |

## Preview in non-TTY sessions

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Preview prints all records instead of browsing | stdin/stdout is not a TTY, only one record exists, or `--non-interactive` is set. | Use a real TTY for browsing, or intentionally pass `--non-interactive`. |
| Navigation keys fail | Terminal cannot deliver interactive keypresses. | Use `--non-interactive` or `--save-results`. |
| Piped preview is awkward | Interactive browsing is not appropriate for pipes. | Use `data-designer preview CONFIG --non-interactive` or save HTML artifacts. |

## Reset/delete caution

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `config reset` did not remove MCP/tool/plugin/persona state | Reset only targets provider and model config files. | Delete other state deliberately: plugin catalogs through `plugin catalog remove`; managed assets manually. |
| Only one reset prompt appears | Only one targeted config file exists. | Confirm or skip that file; there is no hidden full-state reset. |

## Persona downloads

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `NGC CLI not found` | `ngc` is not installed or not on `PATH`. | Install NGC CLI and retry. |
| Missing `~/.ngc/config` | NGC CLI has not been configured. | Run `ngc config set`, then rerun `download personas`. |
| Invalid locale | Requested locale is not in the built-in registry. | Run `download personas --list` or `agent state persona-datasets` and choose a listed locale. |
| Download fails or stalls | Network/auth/storage problem. | Use `--dry-run` to confirm planned locales, verify NGC access, and ensure disk space under managed assets. |
| One locale installed, another missing | Install state is per-locale. | Download the missing locale explicitly, e.g. `data-designer download personas -l ja_JP`. |

## Plugin catalog/install issues

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `--catalog` seems ignored by `plugin installed` or `plugin catalog ...` | Those commands do not read a selected catalog. | Only use `--catalog` with `list`, `search`, `info`, `install`, and `uninstall`. |
| Package not found but runtime plugin exists | Package commands take package names or package aliases. | Run `plugin search QUERY`; use the owning package suggested by the CLI. |
| List/search appears empty | Incompatible packages are hidden by default. | Add `--include-incompatible`. |
| Install blocked by compatibility | Package declares unsupported Python/Data Designer constraints. | Inspect with `plugin info PACKAGE` and `plugin install PACKAGE --dry-run`. |
| Manager fails | `uv`/`pip` is missing, too old, or unusable in the active environment. | Try `--manager pip` or `--manager uv` explicitly, or repair the environment. |

## Agent introspection errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Error [unknown_family]` | Bad `agent types` family. | Use `columns`, `samplers`, `validators`, `processors`, or `constraints`. |
| `Error [legacy_model_config]` or `Error [invalid_registry]` | Local YAML registry exists but cannot be read. | Back up, repair YAML/schema, and re-run `agent state ...` or `config list`. |
| `Error [duplicate_discriminator_value]` | Built-in or plugin type registration conflict. | Check newly installed plugins and route implementation work to `plugins-and-extensions`. |

For repeatable diagnosis, run `scripts/capture_agent_context.py`; it captures root/group help and agent outputs using a temporary `DATA_DESIGNER_HOME` unless `--home` is provided.
