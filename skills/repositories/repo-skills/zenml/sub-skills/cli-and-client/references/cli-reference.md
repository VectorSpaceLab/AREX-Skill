# ZenML CLI Reference

## Entry Point And Registration

The package exposes the console script `zenml = zenml_cli:cli`. Importing `zenml_cli` reroutes logging to stderr so JSON, YAML, CSV, and TSV command output can stay pipeable on stdout. The root Click object is `zenml.cli.cli.cli`; command modules are registered by importing the `zenml.cli` package, which loads the command modules.

For help-only inspection, use `zenml --help`, `zenml <group> --help`, or the bundled `scripts/zenml_cli_help_snapshot.py`. Help rendering should not require server login, but it still imports ZenML base dependencies. If import fails before help is shown, check the missing dependency or optional import guidance in `troubleshooting.md`.

## Core Session Commands

- `zenml init [--path PATH]` initializes a ZenML repository by creating local ZenML configuration at the chosen root. Template initialization uses the `templates` extra and may prompt or copy files.
- `zenml login [SERVER]` connects and authenticates to a server. With no arguments it can offer local, Pro, or custom server flows depending on current state.
- `zenml login --local` starts/connects to a local server; `--docker`, `--port`, `--ip-address`, `--restart`, and `--blocking` affect local server startup and may require local/server extras, Docker, or a long-running process.
- `zenml login <url> --api-key` prompts for an API key and connects non-interactively after the key is supplied.
- `zenml connect <url>` is a compatibility command for connecting a client to a server URL; prefer `zenml login` for current authentication flows when credentials are involved.
- `zenml logout [SERVER] [--clear] [--local] [--pro]` disconnects and can clear credentials or stop a local server.
- Environment variables `ZENML_STORE_URL` and `ZENML_STORE_API_KEY` authenticate automation directly; do not run `zenml login`/`logout` while `ZENML_STORE_URL`, `ZENML_STORE_API_KEY`, `ZENML_STORE_USERNAME`, or `ZENML_STORE_PASSWORD` are set.

## List Commands And Output

Most list commands use generated filter options plus shared output flags:

- `--output table|json|yaml|tsv|csv` controls render format.
- `--columns id,name,...` selects columns; `--columns all` asks for all known columns.
- `--sort_by "desc:created"` or `--sort_by "asc:name"` controls sorting when supported.
- Text/UUID filters support operators such as `contains`, `notcontains`, `startswith`, `endswith`, `oneof`, and `notoneof`.
- Nullable filters support `isnull:` and `isnotnull:`.
- Datetime filters use `%Y-%m-%d %H:%M:%S` with operators such as `gt`, `gte`, `lt`, and `lte`.
- Boolean filters use true/false strings accepted by the filter model.

For scriptable audits, prefer JSON or YAML and narrow columns. Avoid `describe` or `get` commands that hydrate and print sensitive values unless values are intentionally needed.

## Command Families

### Projects

Use `zenml project list`, `register`, `set`, `describe`, and `delete` to manage projects. `project list` highlights the active project when no explicit sort/filter is used. `project register --set` activates the new project; `project set --default` also updates the user default project.

Python Client equivalents include `Client().list_projects(...)`, `Client().get_project(...)`, `Client().create_project(...)`, `Client().set_active_project(...)`, `Client().update_project(...)`, and `Client().delete_project(...)`.

### Pipelines, Runs, Snapshots, And Legacy Schedules

Use `zenml pipeline list` for pipeline records and `zenml pipeline runs list` for run records. `pipeline runs list` supports filters such as pipeline, stack, status, tags, model, trigger, parent/root run fields, and time fields when the Client signature and filter model are aligned.

`zenml pipeline schedule ...` is the legacy schedule command family backed by schedule records. Do not confuse it with native trigger commands under `zenml trigger schedule ...`.

Pipeline snapshots live under `zenml pipeline snapshot ...`; run templates and older commands may be deprecated in favor of snapshots.

Python Client equivalents include `Client().list_pipelines(...)`, `get_pipeline(...)`, `delete_pipeline(...)`, `list_pipeline_runs(...)`, `get_pipeline_run(...)`, `delete_pipeline_run(...)`, `list_snapshots(...)`, `get_snapshot(...)`, and legacy `list_schedules(...)`/`update_schedule(...)`/`delete_schedule(...)`.

### Secrets

Use `zenml secret create`, `list`, `get`, `update`, `rename`, `export`, and `delete` carefully:

- `secret list` returns secret metadata and does not include secret values.
- `secret create` and `secret update` preview values with redaction by default.
- `secret get` prints secret keys and values. Do not use it during broad audits unless the user explicitly needs secret values.
- `--private` narrows operations to private or public secrets where supported.
- Centralized secrets can be unavailable on a deployment; the CLI reports that as a centralized secret management error.

Python Client equivalents include `Client().create_secret(...)`, `list_secrets(...)`, `get_secret(...)`, `update_secret(...)`, `delete_secret(...)`, `get_secret_by_name_and_private_status(...)`, and `list_secrets_by_private_status(...)`.

### Stacks And Components

Use `zenml stack list`, `get`, `set`, `register`, `update`, `delete`, `copy`, `describe`, `export`, `import`, and related commands to inspect and manage stacks. Stack registration can use explicit component names or provider/service connector shortcuts; provider/connector registration requires a remote ZenML deployment reachable by the cloud provider.

Use stack component command groups for component records and flavors. Implementation details, flavor classes, optional SDK imports, and component runtime behavior belong in `../stacks-and-integrations/SKILL.md`.

Python Client equivalents include `Client().list_stacks(...)`, `get_stack(...)`, `create_stack(...)`, `update_stack(...)`, `activate_stack(...)`, `delete_stack(...)`, `list_stack_components(...)`, `get_stack_component(...)`, `create_stack_component(...)`, `update_stack_component(...)`, and `delete_stack_component(...)`.

### Native Triggers

Use `zenml trigger schedule ...` for native schedule triggers and `zenml trigger platform-event ...` for platform event triggers. Both support create/update/list and share generated delete/attach/detach/clear-error commands by trigger type.

Native trigger changes often span CLI, Client methods, trigger models, server endpoints, stores, schemas, docs, and tests. Route deep implementation to `../server-and-stores/SKILL.md`, but keep CLI option and Client signature updates here.

Python Client equivalents include `Client().create_schedule_trigger(...)`, `update_schedule_trigger(...)`, `get_schedule_trigger(...)`, `list_schedule_triggers(...)`, `create_platform_event_trigger(...)`, `update_platform_event_trigger(...)`, `get_platform_event_trigger(...)`, `list_platform_event_triggers(...)`, and `delete_trigger(...)`.

### Resource Pools And Requests

Use `zenml resource-pool create|update|describe|list|delete` for pool records. Capacity, reserved resources, and limits are JSON/YAML dictionaries whose values must parse to integers.

Use `zenml resource-pool attach-policy|update-policy|detach-policy|list-policies` for component subject policies. Policies target orchestrators or step operators and include priority, reserved resources, and limits.

Use `zenml resource-request list|describe|delete` for queue/request inspection. These commands use resource request models and may call the store through the Client, so backend behavior belongs in `../server-and-stores/SKILL.md`.

Python Client equivalents include `Client().create_resource_pool(...)`, `get_resource_pool(...)`, `list_resource_pools(...)`, `update_resource_pool(...)`, `delete_resource_pool(...)`, `create_resource_pool_subject_policy(...)`, `list_resource_pool_subject_policies(...)`, `update_resource_pool_subject_policy(...)`, and `delete_resource_pool_subject_policy(...)`.

### Tags And Models

Use `zenml tag list|register|update|delete` for tags. Tags are used on artifacts, models, and model versions.

Use `zenml model list|register|update|delete` and `zenml model version ...` for model namespace and version records. These are ZenML control-plane models, not necessarily ML model artifacts. Artifact/model-version link commands belong to the model command group but may touch artifact/deployment concepts.

Python Client equivalents include `Client().list_tags(...)`, `create_tag(...)`, `update_tag(...)`, `delete_tag(...)`, `list_models(...)`, `get_model(...)`, `create_model(...)`, `update_model(...)`, `delete_model(...)`, `list_model_versions(...)`, `get_model_version(...)`, `create_model_version(...)`, `update_model_version(...)`, and `delete_model_version(...)`.

## CLI Development Coupling

List commands usually follow this pattern:

```python
@entity.command("list")
@list_options(EntityFilter)
def list_entities(columns: str, output_format: OutputFormat, **kwargs: Any) -> None:
    page = Client().list_entities(**kwargs)
    print_page(page, columns, output_format)
```

The `list_options` decorator turns filter model fields into Click options unless the field is listed in the model's `CLI_EXCLUDE_FIELDS`. If a field is generated as a CLI option, the receiving Client method must accept the same keyword and pass it into the filter model instance in the method body.

When adding or renaming filters, update the filter model, Client signature, Client filter-model instantiation, CLI exclusions if needed, and functional CLI tests together. Relationship-backed fields can also require store-layer join logic; route that part to `../server-and-stores/SKILL.md`.

## Safe Audit Pattern

For an audit that should avoid secret leaks:

1. Confirm target connection using `zenml server list`, `zenml project describe`, or `Client().active_project` without printing tokens.
2. Use `list` commands with `--output=json` and narrow columns for projects, stacks, pipelines, pipeline runs, tags, models, triggers, resource pools, and resource requests.
3. Use `secret list --columns=id,name,private --output=json`, not `secret get`, unless the user explicitly asks to retrieve values.
4. Prefer Client methods that return metadata-only pages (`list_secrets`) instead of hydrated value retrieval (`get_secret`).
5. Redact server URLs, API keys, tokens, and secret values in summaries.
