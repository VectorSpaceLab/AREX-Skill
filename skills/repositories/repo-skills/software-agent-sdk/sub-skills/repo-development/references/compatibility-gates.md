# Compatibility Gates

## SDK public API

- `openhands.sdk.__all__` is the public surface.
- Public removals require deprecation metadata with a removal target at least 5 minor releases later.
- Breaking public API changes require at least a MINOR version bump.

## Agent-server REST API

- `/api/**` is a public REST surface.
- Incompatible REST changes need a deprecation notice and a 5-minor-release runway.
- OpenAPI `deprecated=True` must match documented deprecation text.

## Persisted settings

- Persisted SDK settings use `schema_version` and direct model-dump shapes.
- Incompatible shape changes need a schema version bump, migration, and a fixture under `tests/sdk/persisted_settings_baselines/`.

## Tool registration and import layering

- SDK must not import from tools, workspace, or agent-server.
- Tools can import SDK but not workspace or agent-server.
- Workspace can import SDK/tools but not agent-server.
- Agent-server can import SDK/tools but not workspace implementations.

## Examples and tool names

- Tool names are wire contracts; avoid renaming without a compatibility plan.
- The default tool names are `terminal`, `file_editor`, and `task_tracker`.
