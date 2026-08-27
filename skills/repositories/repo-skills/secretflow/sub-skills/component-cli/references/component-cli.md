# Component CLI reference

This reference covers the component registry, the `secretflow component`
command family, payload-driven component evaluation, and export-to-serving
workflows.

## CLI commands

| Command | Purpose | Common use |
| --- | --- | --- |
| `secretflow component ls` | List registered components | Quick registry health check |
| `secretflow component inspect <comp_id>` | Show one component definition | Inspect a single component before building a payload |
| `secretflow component inspect --all` | Show the full public component list | Browse the available component catalog |
| `secretflow component translate` | Produce or update translation metadata | Plugin / localization workflow |
| `secretflow component get_translation` | Print the translation map | Debug component labels and descriptions |
| `secretflow component run` | Execute a component payload | Payload-driven component evaluation |

## Core component APIs

| API | Purpose | Notes |
| --- | --- | --- |
| `Registry` | Live component registry | Used to look up component definitions |
| `comp_eval(...)` | Execute a component evaluation | The main programmatic entry point behind `component run` |
| `get_comp_list_def()` | Get the public component list definition | Useful for smoke checks and catalog generation |
| `load_plugins()` | Load registered plugins | Needed when component definitions come from plugins |
| `ModelExport` | Export a component pipeline to a serving package | Bridges SecretFlow components and serving bundles |

## Payload flow

The `component run` command and the `comp_eval` API expect three objects to stay
in sync:

1. `NodeEvalParam` — the component payload and attributes.
2. `StorageConfig` — where the component reads and writes files.
3. `SFClusterConfig` — the party and device wiring for the runtime.

The most common errors in this path come from one of these issues:
- wrong component id or version,
- inputs or outputs in the wrong order,
- or a payload that references a party/data id that does not exist in the
  cluster config.

## Export and serving workflow

`ModelExport` is the bundled bridge from SecretFlow component pipelines to a
serving package.

High-level flow:
1. Train or score a model with components that implement the serving export
   interface.
2. Collect the `NodeEvalParam` objects in the same order the components ran.
3. Feed the matching input and output `DistData` objects to the export step.
4. Package the serving graph and the preprocessing trace into the exported
   tarball.

## Plugin workflow

A plugin entry point should import the plugin's component modules and then
invoke the component loader for the plugin package.
A minimal entry skeleton usually does three things:
- import the component class so it is registered,
- expose a `main()` function,
- and keep the package path resolution simple.

The bundled template file under `scripts/` is a safe starting point for this
shape.

## Troubleshooting

### `Component with id [...] is not found`
- Check the registry first with `component ls` or `get_comp_list_def()`.
- Verify that the plugin was loaded before you looked up the component.

### `You must provide comp_id or use --all/-a`
- `component inspect` requires either a component id or the `--all` flag.

### Payload execution fails with ordering or metadata errors
- Re-check the `NodeEvalParam`, `StorageConfig`, and `SFClusterConfig` order.
- Make sure the input and output `DistData` lists correspond to the component
  sequence.

### Export complains about unsupported components
- Only components that implement the serving export interface can participate
  in the export pipeline.
- If the component is part of a preprocessing chain, make sure the trace can be
  rebuilt from the recorded nodes.

### Plugin import does not register anything
- Confirm the entry module imports the component class.
- Make sure the package path is correct and that plugin loading was enabled.

## Cross-links

- Root troubleshooting: `../../references/troubleshooting.md`
- Smoke helper: `../scripts/component_registry_smoke.py`
- Plugin skeleton: `../scripts/plugin_entry_template.py`
