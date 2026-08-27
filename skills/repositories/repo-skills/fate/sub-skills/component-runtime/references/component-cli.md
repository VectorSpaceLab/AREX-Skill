# Component CLI Surface

The installed FATE package exposes `python -m fate.components` with two top-level groups: `component` and `test`. This sub-skill focuses on `component`.

## Verified command matrix

| Command | Purpose | Output / side effect | Notes |
| --- | --- | --- | --- |
| `python -m fate.components --help` | Show top-level groups. | Help text. | The installed package advertises `component` and `test`. |
| `python -m fate.components component --help` | Show component subcommands. | Help text. | The live help includes `artifact-type`, `cleanup`, `desc`, `execute`, `list`, and `task-schema`. |
| `python -m fate.components component list [--save <json>]` | List built-in and third-party components. | JSON dict. | Safe and cheap. Use this before `desc` or `artifact-type`. |
| `python -m fate.components component desc --name <component> [--save <yaml>]` | Emit a component descriptor. | YAML descriptor. | The component name must match the exact registered id. |
| `python -m fate.components component task-schema [--save <json>]` | Emit the `TaskConfigSpec` JSON schema. | JSON schema. | The command name is hyphenated: `task-schema`, not `task_schema`. |
| `python -m fate.components component artifact-type --name <component> --role <role> --stage <stage> [--output-path <yaml>]` | Emit the stage- and role-filtered runtime I/O view. | YAML. | Use this when you want the active input/output artifacts for a specific role and stage. |
| `python -m fate.components component execute ...` | Execute a live component configuration. | Runtime meta file and logs. | Reference-only for this sub-skill; it needs a live config, valid runtime backends, and artifact wiring. |
| `python -m fate.components component cleanup ...` | Destroy a live runtime context. | Cleanup side effects. | Reference-only unless a live runtime is available. |

## Saved-file formats

- `list --save` writes JSON with two keys: `buildin` and `thirdparty`.
- `desc --save` writes a YAML component descriptor with `component`, `schema_version: v1`, roles, parameters, and artifact definitions.
- `task-schema --save` writes the pydantic JSON schema for `TaskConfigSpec`.
- `artifact-type --output-path` writes YAML that only includes the artifacts active for the requested role and stage.

## Practical use order

1. Run `component --help` if you want to confirm the installed CLI shape.
2. Run `component list --save` to discover exact component names.
3. Run `component desc --name <component> --save` to inspect the full merged descriptor.
4. Run `component artifact-type --name <component> --role <role> --stage <stage>` to inspect the runtime I/O view.
5. Run `component task-schema --save` to validate task-config fields before debugging a config error.

## Exact spelling reminders

- `task-schema` is hyphenated in the CLI.
- `artifact-type` is the CLI spelling shown by `component --help`.
- The CLI accepts component names exactly as registered by the runtime loader; do not infer names from filenames.
