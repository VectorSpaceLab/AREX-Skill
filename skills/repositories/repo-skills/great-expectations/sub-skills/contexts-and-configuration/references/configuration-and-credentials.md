# Configuration and Credentials

GX Core configuration lives on the Data Context. Use file-backed contexts when configuration must survive across Python sessions, and use ephemeral contexts when a script can rebuild all configuration at runtime.

## `DataContextConfig` Surfaces

`great_expectations.data_context.types.base.DataContextConfig` accepts these context-level fields most often used by agents:

| Field | Purpose |
| --- | --- |
| `config_version` | GX project config version. Existing file contexts load it from `great_expectations.yml`. |
| `fluent_datasources` | Fluent datasource definitions. Prefer `context.data_sources` APIs for normal creation/update. |
| `expectations_store_name` | Store name used for expectation suites. |
| `validation_results_store_name` | Store name used for validation results. |
| `checkpoint_store_name` | Store name used for checkpoints. |
| `stores` | Store definitions and `store_backend` settings. |
| `data_docs_sites` | Data Docs site definitions. |
| `config_variables_file_path` | File path for non-committed config variables, commonly `uncommitted/config_variables.yml`. |
| `analytics_enabled` | Context-level analytics toggle. |
| `plugins_directory` | Optional project plugins directory. |
| `store_backend_defaults` | Convenience defaults such as filesystem or in-memory store backends. |

Use `DataContextConfig(...)` directly for ephemeral contexts or test fixtures. For a file context, prefer loading the context, editing `context.variables.config`, calling `context.variables.save()`, and reloading.

## Config Variable Resolution

GX substitutes variables in strings using `$NAME` and `${NAME}` syntax. Resolution can draw from runtime values, environment variables, config-variable files, and supported secret-manager references. When the same setting can come from multiple places, `runtime_environment` is useful for short-lived overrides because it is passed into `gx.get_context(...)` and does not need to be written to disk.

Safe credential patterns:

```python
context = gx.get_context(
    mode="ephemeral",
    runtime_environment={"POSTGRES_CONNECTION_STRING": "postgresql+psycopg2://..."},
)
```

```python
connection_string = "${POSTGRES_CONNECTION_STRING}"
```

```yaml
# uncommitted/config_variables.yml
POSTGRES_CONNECTION_STRING: postgresql+psycopg2://<user>:<password>@<host>:<port>/<database>
```

Important details:

- Do not commit secrets; file contexts scaffold an `uncommitted/` area for config variables.
- `$NAME` and `${NAME}` are both substitution forms.
- Escape literal dollar signs in secrets with a backslash, for example `pa\$\$word`.
- If a variable is missing, GX raises a missing-config-variable error rather than silently preserving the placeholder.
- `context.variables.config` shows raw values before substitution; `context.variables` getters substitute values through the context config provider.
- `context.escape_all_config_variables(...)` can escape dollar signs before saving values that should remain literal.

## Metadata Store Paths

For a file context, raw store configuration is available at `context.variables.config.stores`:

```python
context = gx.get_context(mode="file", project_root_dir="./gx-project")
context.variables.config.stores["expectations_store"]["store_backend"]["base_directory"] = "my_expectations_store/"
context.variables.save()
context = gx.get_context(mode="file", project_root_dir="./gx-project")
```

Use this pattern for expectation, validation result, validation definition, and checkpoint stores. Store configuration is loaded during context initialization, so reloading is not optional after changing store paths. Keep relative paths rooted in the project unless the user explicitly wants a shared absolute path.

## Data Docs Sites

Data Docs site settings live under `data_docs_sites` and can be added with `context.add_data_docs_site(...)`:

```python
site_config = {
    "class_name": "SiteBuilder",
    "site_index_builder": {"class_name": "DefaultSiteIndexBuilder"},
    "store_backend": {
        "class_name": "TupleFilesystemStoreBackend",
        "base_directory": "uncommitted/data_docs/local_site/",
    },
}
context.add_data_docs_site(site_name="local_site", site_config=site_config)
```

`context.build_data_docs(site_names=[...])` or `context.build_data_docs(site_names="local_site")` builds sites manually. Checkpoint actions can automate Data Docs updates; route checkpoint-action details to `../checkpoints-actions-and-data-docs/SKILL.md`.

## Analytics Toggles

GX checks both:

- `GX_ANALYTICS_ENABLED` environment variable.
- `context.variables.analytics_enabled` in the Data Context.

If either is set to false, analytics are disabled. Analytics settings are checked when a context initializes. For file contexts, set `context.variables.analytics_enabled`, call `context.variables.save()`, then reload the context. For ephemeral contexts, use `GX_ANALYTICS_ENABLED=False` before creating the context.

```python
context = gx.get_context(mode="file", project_root_dir="./gx-project")
context.variables.analytics_enabled = False
context.variables.save()
context = gx.get_context(mode="file", project_root_dir="./gx-project")
```

## Secret Managers

GX substitution supports credential references for AWS Secrets Manager, AWS Systems Manager Parameter Store, Google Cloud Secret Manager, and Azure Key Vault when the relevant optional SDKs and host credentials are available. Use those references as config-variable values, not as hardcoded secrets in skill text. If optional SDKs or cloud credentials are missing, keep the failure contained to the user environment and offer an environment-variable or `config_variables.yml` fallback.

## Safety Checklist

- Use explicit non-cloud `mode` values in scripts unless the user intentionally tests Cloud shutdown behavior.
- Do not print secret-bearing strings, substituted connection strings, tokens, or config-variable values.
- Prefer `context.variables.config` for editing raw config and `context.variables` properties for reading substituted values.
- Save and reload file contexts after editing stores, Data Docs sites, analytics, or config-variable paths.
- Route datasource connection-string usage to `../datasources-and-assets/SKILL.md`; this reference only covers how credentials should be stored and substituted.
