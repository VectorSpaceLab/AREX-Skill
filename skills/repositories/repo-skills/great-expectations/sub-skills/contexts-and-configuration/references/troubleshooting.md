# Troubleshooting Contexts and Configuration

Use this reference for context creation, file project loading, config variables, stores, Data Docs settings, analytics, and import sanity checks.

## Wrong Context Type

Symptoms:

- `gx.get_context()` returns `EphemeralDataContext` when a persistent project was expected.
- Object definitions disappear after a new Python process starts.
- `context.mode` is `ephemeral` but the workflow needs persisted suites, validation definitions, or checkpoints.

Likely causes and fixes:

1. The process is not running under a directory that contains a file-backed GX project. Pass `mode="file"` and `project_root_dir="./your-project-root"`.
2. The provided path points at the wrong level. Use `project_root_dir` for the project root and `context_root_dir` for the context directory that contains `great_expectations.yml`.
3. The script omitted `mode`, so fallback rules selected ephemeral after no file context was found. Use explicit `mode="file"` in persistent automation.
4. The project was intentionally built in memory. Create or load a file context, or call `context.convert_to_file_context()` only when writing a new file-backed project in the current working directory is intended.

## Missing Project Root or Config

Symptoms:

- File mode scaffolds a new context when the user expected an existing one.
- `ConfigNotFoundError` appears in lower-level APIs.
- A custom root contains data files but no GX config.

Fixes:

- Confirm whether the caller intended `project_root_dir` or `context_root_dir`; do not pass both for file mode.
- Check for a `great_expectations.yml` in the context directory.
- Use a disposable root when testing scaffolding because file mode may create config directories.
- If the user only needs an in-memory check, switch to `mode="ephemeral"` to avoid filesystem writes.

## Config Variable Substitution Failure

Symptoms:

- Error text mentions an unresolved config substitution variable.
- A string containing `$NAME` or `${NAME}` does not resolve.
- Passwords containing `$` lose characters or trigger substitution.

Fixes:

1. Define the variable in the environment, the file context's `config_variables.yml`, or `runtime_environment` passed to `gx.get_context(...)`.
2. Confirm `config_variables_file_path` is configured for file contexts before saving variables.
3. Use `$NAME` or `${NAME}` consistently and check case sensitivity.
4. Escape literal dollar signs as `\$` before saving secret values such as `pa\$\$word`.
5. Read raw placeholders from `context.variables.config` and resolved values from `context.variables`; do not confuse the two surfaces.
6. Avoid printing resolved connection strings or tokens while debugging.

## Accidental Cloud Mode

Symptoms:

- `gx.get_context()` raises a Great Expectations error saying GX Cloud has been shut down.
- The error appears even though the task is local.

Likely causes:

- `mode="cloud"` or `cloud_mode=True` was passed.
- A complete set of `cloud_*` keyword arguments was supplied.
- Complete `GX_CLOUD_*` environment configuration is present.

Fixes:

- For local work, pass `mode="file"` or `mode="ephemeral"` explicitly.
- If omitting `mode`, pass `cloud_mode=False` to suppress Cloud auto-detection.
- Remove or isolate `GX_CLOUD_*` variables from the process environment for local scripts.
- Do not recommend Cloud context creation in this GX Core line; it raises by design and is removed in the next major version.

## Analytics Toggle Confusion

Symptoms:

- Analytics remain enabled or disabled after changing a variable.
- Ephemeral context changes do not persist.

Fixes:

- Set `GX_ANALYTICS_ENABLED=False` before context creation for environment-wide or ephemeral control.
- For a file context, set `context.variables.analytics_enabled = False`, call `context.variables.save()`, and re-initialize the context.
- Remember that either `GX_ANALYTICS_ENABLED` or `analytics_enabled` set to false disables analytics.

## Store Path Issues

Symptoms:

- Suites, validation results, validation definitions, or checkpoints save in an unexpected location.
- A store path change does not take effect.
- File permissions fail while saving config or metadata.

Fixes:

1. Inspect `context.variables.config.stores` for raw store settings and `context.variables.stores` for substituted settings.
2. Update the relevant `store_backend.base_directory`, then call `context.variables.save()`.
3. Recreate the file context because stores are instantiated during context initialization.
4. Prefer project-relative paths; use absolute paths only when the deployment intentionally shares metadata outside the project.
5. Verify the process can create and write the selected directories.

## Data Docs Path Issues

Symptoms:

- `build_data_docs` succeeds but files are not where expected.
- Data Docs do not update after validation.
- A site name is missing from `get_docs_sites_urls()`.

Fixes:

- Inspect `context.variables.config.data_docs_sites` for site names and `store_backend.base_directory` values.
- Add sites with unique names through `context.add_data_docs_site(site_name=..., site_config=...)`.
- Run `context.build_data_docs(site_names=[...])` for manual builds.
- Use `UpdateDataDocsAction` in checkpoints for automated builds; route action setup to `../checkpoints-actions-and-data-docs/SKILL.md`.
- Reload file contexts after editing Data Docs site config directly.

## Import or Version Mismatch

Symptoms:

- `import great_expectations as gx` fails.
- `gx.get_context` is missing.
- Public signatures differ from expected examples.

Fixes:

- Verify the installed distribution imports as `great_expectations`.
- Print `gx.__version__` for diagnostics, but do not encode local install paths in reusable docs.
- Run `python scripts/inspect_context.py` from this sub-skill for a safe import/context summary.
- If APIs differ, inspect the installed package's `gx.get_context` signature and context manager attributes before generating code.

## Quick Diagnostic Script

Use the bundled helper first for a low-risk diagnosis:

```bash
python scripts/inspect_context.py --mode ephemeral
python scripts/inspect_context.py --mode file --project-root-dir ./gx-project
```

The helper intentionally avoids printing absolute root paths, credentials, config-variable values, or Data Docs URLs.
