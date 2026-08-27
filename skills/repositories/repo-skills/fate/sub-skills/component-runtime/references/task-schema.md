# Task Schema

`python -m fate.components component task-schema` prints the JSON schema for `TaskConfigSpec`.

## Top-level fields

The installed schema exposes these fields:

| Field | Required | Meaning |
| --- | --- | --- |
| `task_id` | yes | Global task id. |
| `party_task_id` | yes | Party-scoped task id. |
| `task_name` | yes | Human-readable task name. |
| `component` | yes | Registered component id. |
| `role` | yes | Runtime role string such as `guest`, `host`, `arbiter`, or `local`. |
| `party_id` | yes | Local party id. |
| `stage` | no | Execution stage; default is `default`. Supported values are `default`, `train`, `predict`, and `cross_validation`. |
| `parameters` | no | Component parameter payload. |
| `input_artifacts` | no | Map of component input names to artifact apply specs. |
| `output_artifacts` | no | Map of component output names to artifact apply specs. |
| `conf` | yes | Runtime backend, federation, and logging configuration. |

## `conf` sub-model

`conf` is a `TaskConfSpec` object with these nested pieces:

| Field | Allowed types | Notes |
| --- | --- | --- |
| `device` | `CPU` or `GPU` | Choose the runtime device class. |
| `computing` | `standalone`, `eggroll`, or `spark` | Select the computing backend. |
| `federation` | `standalone`, `rollsite`, `rabbitmq`, `pulsar`, or `osx` | Select the federation backend and metadata shape. |
| `logger` | `LoggerConfig` | Logging configuration; the runtime installs this before execution. |
| `task_final_meta_path` | file path | Final execution meta output path. The model definition seeds it from the current working directory path. |

## Artifact apply specs

### Inputs

`input_artifacts` values use `ArtifactInputApplySpec`:

- `uri` is required.
- `metadata` is required.
- `type_name` is optional.
- A single input key may accept either one apply spec or a list of apply specs when the component declares a multi-input artifact.

### Outputs

`output_artifacts` values use `ArtifactOutputApplySpec`:

- `uri` is required.
- `type_name` is optional.
- Multi-output artifacts require a template URI that contains `{index}`.
- Singleton outputs reject template URIs.

## How to use the schema

1. Run `component task-schema --save` to verify the runtime field names and defaults.
2. Compare the schema with `component desc --name <component>` so the task config uses the exact component id and the right input/output names.
3. Compare the schema with `component artifact-type --name <component> --role <role> --stage <stage>` to make sure the artifact names and stage selection line up.
4. Use the schema output when debugging validation errors from config loading before attempting execution.

## Debugging tips

- If validation fails on `stage`, check that you used the CLI spelling and one of the four supported values.
- If validation fails on `conf.device`, `conf.computing`, or `conf.federation`, inspect the nested backend metadata rather than the top-level task fields.
- If an artifact URI error mentions templates, check whether the output is multi-valued and whether `{index}` is required.
- `TaskCleanupConfigSpec` is a separate model used by `cleanup`; it only carries `computing` and `federation`.
