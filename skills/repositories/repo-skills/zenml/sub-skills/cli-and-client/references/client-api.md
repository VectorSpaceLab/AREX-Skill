# ZenML Client API Reference

## Import And Instance Pattern

Use the public Client abstraction for programmatic resource management:

```python
from zenml.client import Client

client = Client()
```

Do not import server routers, server deployment internals, SQL schemas, or Zen store schemas from CLI/client code. Use `Client` methods and shared domain models. If a task needs FastAPI routes, store methods, SQLModel schemas, migrations, or RBAC, route to `../server-and-stores/SKILL.md`.

## Session And Repository Methods

- `Client.initialize(root=...)` creates a ZenML repository at a filesystem root.
- `Client.find_repository()` detects a ZenML repository from the current location.
- `Client.activate_root(root=...)` changes the active repository root.
- `Client.root`, `Client.active_user`, `Client.active_project`, and `Client.active_stack` expose current context.
- `Client.set_active_project(...)` and `Client.activate_stack(...)` update active selections.

CLI equivalents are `zenml init`, `zenml project set`, and `zenml stack set`. Authentication and server selection are configured by the login/connect layer and global configuration, not by passing credentials directly into `Client()` for normal CLI usage.

## Common Resource Method Families

Most resource families have explicit `create_*`, `get_*`, `list_*`, `update_*`, and `delete_*` methods. Method signatures are explicit; do not pass arbitrary filter kwargs unless the method signature accepts them.

| Resource | Key Client methods | Notes |
| --- | --- | --- |
| Users/projects | `list_users`, `get_user`, `list_projects`, `get_project`, `create_project`, `set_active_project`, `delete_project` | Project commands can show or update active/default project. |
| Stacks/components/flavors | `list_stacks`, `get_stack`, `create_stack`, `update_stack`, `activate_stack`, `list_stack_components`, `create_stack_component`, `list_flavors` | Component implementation belongs to `../stacks-and-integrations/SKILL.md`. |
| Pipelines/runs/snapshots/builds | `list_pipelines`, `get_pipeline`, `list_pipeline_runs`, `get_pipeline_run`, `list_snapshots`, `get_snapshot`, `list_builds`, `get_build` | `list_pipeline_runs` has many explicit filters, including trigger and parent/root run filters. |
| Legacy schedules | `list_schedules`, `get_schedule`, `update_schedule`, `delete_schedule` | Backed by legacy schedule records under `zenml pipeline schedule`. |
| Native triggers | `create_schedule_trigger`, `list_schedule_triggers`, `get_schedule_trigger`, `create_platform_event_trigger`, `list_platform_event_triggers`, `get_platform_event_trigger`, `delete_trigger` | Backed by trigger architecture under `zenml trigger ...`. |
| Resource pools | `create_resource_pool`, `get_resource_pool`, `list_resource_pools`, `update_resource_pool`, `delete_resource_pool`, `create_resource_pool_subject_policy`, `list_resource_pool_subject_policies` | Backend scheduling/store behavior belongs to `../server-and-stores/SKILL.md`. |
| Resource requests | Store-facing request inspection is available through the Client's store in current CLI code | Treat direct `client.zen_store` use as internal and prefer public Client methods when available. |
| Secrets | `create_secret`, `list_secrets`, `get_secret`, `update_secret`, `delete_secret`, `list_secrets_by_private_status` | `list_secrets` omits secret values; `get_secret` can return values. |
| Tags | `create_tag`, `list_tags`, `get_tag`, `update_tag`, `delete_tag` | Tags organize artifacts, models, and model versions. |
| Models/model versions | `create_model`, `list_models`, `get_model`, `update_model`, `delete_model`, `create_model_version`, `list_model_versions`, `get_model_version`, `update_model_version`, `delete_model_version` | These are ZenML model namespaces/control-plane records. |
| Service accounts/API keys | `create_service_account`, `list_service_accounts`, `get_service_account`, `create_api_key`, `list_api_keys`, `get_api_key`, `update_api_key`, `delete_api_key` | API key creation/rotation may display one-time secrets. |

## Filtering Contract

ZenML list filters use typed Pydantic filter models, but public Client methods expose explicit keyword parameters. A CLI list command normally receives generated kwargs from `@list_options(FilterModel)` and calls a matching Client list method.

When adding a new filter field, keep these layers synchronized:

1. Add the field to the appropriate filter model, with description and type-specific filter behavior.
2. If the field should be usable from the CLI, leave it out of `CLI_EXCLUDE_FIELDS`; if it is internal-only, add it to `CLI_EXCLUDE_FIELDS`.
3. Add the same parameter to the corresponding `Client.list_*` method signature.
4. Pass that parameter into the filter model instance inside the Client method body.
5. If the field references another entity, update store query/join logic and server schema behavior as needed.
6. Add or update CLI tests for the generated option and Client tests for the filter behavior.

A runtime `TypeError: list_pipeline_runs() got an unexpected keyword argument 'new_field'` means the CLI generated an option from the filter model but the Client method signature did not accept it.

## High-Value Filter Examples

### Pipeline Runs

`Client().list_pipeline_runs(...)` supports filters for identity/time (`id`, `created`, `updated`, `name`, `index`), project/pipeline/stack (`project`, `pipeline`, `pipeline_id`, `pipeline_name`, `stack`, `stack_id`, `stack_component`), run state (`status`, `in_progress`, `templatable`, `start_time`, `end_time`), lineage (`schedule_id`, `build_id`, `snapshot_id`, `source_snapshot_id`, `template_id`, `code_repository`, `code_repository_id`, `model`, `model_version_id`, `linked_to_model_version_id`, `run_metadata`, `tags`, `triggered_by_step_run_id`, `triggered_by_deployment_id`, `trigger_id`, `parent_run_id`, `root_runs_only`), pagination/sorting (`sort_by`, `page`, `size`, `logical_operator`), and hydration (`hydrate`, `include_full_metadata`).

Use `hydrate=False` for broad audits. Use `include_full_metadata=True` only when step metadata is specifically needed and output size is acceptable.

### Secrets

`Client().list_secrets(...)` returns a page of secret metadata without values. `Client().get_secret(...)` can return secret values. For safe audits, use list methods and summarize only names/IDs/private status unless the user explicitly requests values.

### Triggers

Use native trigger methods for `zenml trigger schedule ...` and `zenml trigger platform-event ...`. Use legacy schedule methods only for `zenml pipeline schedule ...`. If a user says “schedule” ambiguously, identify which command family or model family is involved before editing.

### Resource Pools

Resource pool Client methods operate on pool records and subject policies. Resource request inspection in current CLI code may still call through `Client().zen_store`. Prefer public methods if available; if changing store/backend behavior, route to `../server-and-stores/SKILL.md`.

## Safe Programmatic Audit Template

```python
from zenml.client import Client

client = Client()
summary = {
    "project": client.active_project.name,
    "stacks": [stack.name for stack in client.list_stacks(size=50).items],
    "pipelines": [pipeline.name for pipeline in client.list_pipelines(size=50).items],
    "runs": [run.name for run in client.list_pipeline_runs(size=50).items],
    "secrets": [secret.name for secret in client.list_secrets(size=50).items],
    "resource_pools": [pool.name for pool in client.list_resource_pools(size=50).items],
    "schedule_triggers": [trigger.name for trigger in client.list_schedule_triggers(size=50).items],
    "platform_event_triggers": [trigger.name for trigger in client.list_platform_event_triggers(size=50).items],
}
```

Do not print `client.get_secret(...).values`, API keys, tokens, or credentials in audit output. If an entity list can be large, use pagination and bounded `size` values.

## CLI/Client Change Checklist

For CLI-facing Client changes:

- Confirm whether the task is usage, CLI behavior, or server/store behavior.
- Check the command module, filter model, Client method, and tests together.
- Keep command functions thin: parse CLI inputs, instantiate `Client()`, call a public Client method, and format output.
- Do not import optional integration SDKs at module import time.
- Do not import `zen_server` or SQL schema modules into CLI/client code.
- For destructive operations, keep confirmation prompts unless an established `--yes` flag exists.
- For sensitive resources, keep list output metadata-only and value output opt-in.
