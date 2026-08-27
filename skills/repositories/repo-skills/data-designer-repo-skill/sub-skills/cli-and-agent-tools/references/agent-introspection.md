# Agent Introspection Reference

The `data-designer agent ...` commands expose live Data Designer type catalogs, model alias state, persona dataset state, and command metadata. Use them instead of hardcoding built-in or plugin-added types.

## Command registry

| Command pattern | Registry return id | Meaning |
| --- | --- | --- |
| `data-designer agent context` | `agent_context` | Full bootstrap payload. |
| `data-designer agent types [family]` | `agent_types` | One or all type family catalogs. |
| `data-designer agent state model-aliases` | `agent_state_model_aliases` | Model aliases and usability. |
| `data-designer agent state persona-datasets` | `agent_state_persona_datasets` | Persona locales and install status. |

The same registry appears in the `Commands` section of `agent context` with `name`, `command_pattern`, `description`, and `returns` fields.

## `agent context`

`agent context` is the preferred first command for agents. The text output has these sections:

1. `Data Designer v...`
2. `Config Module`
3. `Types`
4. `Model Aliases`
5. `Persona Datasets`
6. `Commands`

Structured fields behind the formatter:

| Field | Meaning |
| --- | --- |
| `library_version` | Installed package version, or `unknown` when package metadata cannot be resolved. |
| `config_module_path` | Installed `data_designer.config` module directory. Use only as live inspection context; do not hardcode it. |
| `config_builder_file` | `DataDesignerConfigBuilder` source file shown relative to `{config_root}`. |
| `base_config_file` | Shared base config fields source file shown relative to `{config_root}`. |
| `families` | Family records with `family`, `count`, and `files`. |
| `types` | Mapping from family to type records with `type` and first-paragraph `description`. |
| `state.model_aliases` | Same content as `agent state model-aliases`. |
| `state.persona_datasets` | Same content as `agent state persona-datasets`. |
| `operations` | Agent command registry records. |

If no aliases are usable, the context formatter prints a clear message telling the user to configure models/providers. This can be true even in a fresh state with default-seeded aliases because API keys are still missing.

## `agent types [family]`

Accepted families and discriminators:

| Family | Discriminator |
| --- | --- |
| `columns` | `column_type` |
| `samplers` | `sampler_type` |
| `validators` | `validator_type` |
| `processors` | `processor_type` |
| `constraints` | `constraint_type` |

Notes:

- With no family argument, all families are printed.
- Singular names normalize to plural names (`validator` → `validators`).
- Type discovery walks the discriminated unions exported by `data_designer.config` and reads each model's `Literal[...]` discriminator.
- Source files are reported relative to `data_designer/` when possible. Plugin-defined types outside the package may report an absolute path from the installed environment.

One-family payload shape:

| Field | Meaning |
| --- | --- |
| `config_module_path` | Installed config module directory. |
| `family` | Normalized family name. |
| `files` | Source files that define family members. |
| `items` | Type records with `type` and `description`. |

## `agent state model-aliases`

Use this before model-backed validate/preview/create/check-models. Payload fields:

| Field | Meaning |
| --- | --- |
| `model_config_present` | Whether `model_configs.yaml` exists and loads. |
| `provider_config_present` | Whether `model_providers.yaml` exists and loads. |
| `items` | Sorted alias records. |

Each alias record has `model_alias`, `model`, `generation_type`, `provider`, `usable`, and `reason`.

Usability rules:

- `usable=True` only when the alias's provider exists and the provider is not missing its API key.
- Missing provider → `usable=False` with `Provider '...' is not configured.`
- Missing key → `usable=False` with `Provider '...' is missing an API key.`
- Default-seeded aliases are not automatically usable; the relevant API key environment variables still need values.

## `agent state persona-datasets`

Payload fields:

| Field | Meaning |
| --- | --- |
| `managed_assets_directory` | Directory used to check persona parquet files. |
| `items` | One row per built-in locale. |

Each locale record has `locale`, `dataset_name`, `size`, and `installed`. Installed state is per-locale: the command checks whether that locale's parquet file is present under managed assets.

## Error handling

Agent commands print `Error [<code>]: <message>` to stderr and exit `1` when a structured introspection error occurs.

| Code | Likely cause | Recovery |
| --- | --- | --- |
| `unknown_family` | Unsupported `agent types` family. | Re-run with a known family or no family. |
| `duplicate_discriminator_value` | Built-in or plugin type discriminator conflict. | Check recently installed plugins; route implementation debugging to `plugins-and-extensions`. |
| `invalid_discriminator_annotation` | A type does not use the expected `Literal[...]` discriminator. | Treat as a package/plugin bug; route config details to `config-authoring`. |
| `legacy_model_config` | Local model config cannot be loaded due to legacy format. | Back up and reconfigure through `config models` / `config providers`. |
| `invalid_registry` | A local registry file exists but cannot be parsed/validated. | Repair the YAML and re-run `agent state ...` or `config list`. |
| `internal_error` | Unexpected exception escaped the helper. | Capture stderr and verify the active installed package environment. |
