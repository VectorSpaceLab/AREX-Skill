# Troubleshooting

Use this page for config, registry, training, and CLI failures that are specific
to DeepPavlov’s pipeline machinery. For package-wide install/import/backend or
cache problems, use the root skill’s troubleshooting reference once it exists.

## Quick Triage

1. Run `scripts/inspect_config_requirements.py <config>` to see the resolved
   config path, nested configs, classes, requirements, and download references.
2. Check whether the error is about a missing config field, a missing registry
   entry, or a CLI misuse.
3. If the config nests another config, inspect the nested file before editing
   the outer one.

## Config Lookup and Aliases

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Config name is not found | The name is not an exact stem under `configs/`, or it is a deprecated alias. | Use the full file path or the current config stem; if a deprecation warning appears, switch to the new name. |
| Unexpected alias warning | The model name still maps through the alias table. | Update the config reference to the new target name. |

## Nested Configs and `overwrite`

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| An override does not change the nested field | The dot path is wrong or a list index is missing. | Use paths like `chainer.pipe.1.class_name`; numeric segments address list positions. |
| A nested config still uses its default paths | The `overwrite` block did not target the field you expected. | Inspect the nested config first and override only the exact field names you need. |
| A component reference seems to disappear when nesting configs | The nested config is being built in its own context. | Re-check whether the component should be inside the nested config or outside with a `ref`. |

## Registry and Custom Code

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Model <name> is not registered.` | The short name is not in the registry. | Add `metadata.imports`, register the class, or use `module.submodule:ClassName`. |
| `Expected class description in a module.submodules:ClassName form` | A `class_name` string is malformed. | Rewrite it as `module.submodule:ClassName`. |
| `Component config has no class_name nor ref fields` | The config item is incomplete. | Add `class_name`, `ref`, or `config_path`. |
| `Component with id "..." was referenced but not initialized` | A `ref` or `#id` refers to a component that has not been created yet. | Define the source component earlier in the pipe or rename the id. |
| A custom metric never appears by short name | The metric decorator or module import was missed. | Use `@register_metric`, add `metadata.imports`, and rebuild the registry if needed. |

## Training and Evaluation

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Training is skipped | The config has no `dataset_reader`. | Add `dataset_reader` and `dataset_iterator`, or accept that the config is inference-only. |
| `No dataset reader is provided in the JSON config.` | The reader block is missing or misnamed. | Add the reader section or fix the field name. |
| `Unsupported dataset type: ...` | The legacy `dataset` shortcut only supports classification. | Use explicit `dataset_reader` / `dataset_iterator` blocks for other tasks. |
| `val_every_n_epochs` is set but no validation data exists | The trainer expects a validation split. | Add `valid` data or remove the early-stopping schedule. |
| A trainable component does not reload after training | It lacks `save_path`, so `load_trained` cannot copy it to `load_path`. | Add a `save_path` / `load_path` pair or accept a non-reloadable component. |

## CLI Misuse

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `predict` fails on a terminal TTY | `predict` is stream mode, not interactive mode. | Use `interact` or pipe data from stdin / a file. |
| Batch output looks misaligned | Multi-input configs require the right number of interleaved lines. | Feed `batch_size × number_of_inputs` lines in the correct order. |
| `crossval` refuses to run | `--folds` is below 2. | Set `--folds 2` or higher. |
| `paramsearch` reports an unsupported search type | Only grid search is implemented in the shipped module. | Keep `--search_type grid`. |
| The best-config filename is not where the docs say | The code writes `*.cvbest.json` with `Path.with_suffix`. | Look for the `.cvbest.json` file next to the original config. |

## Environment and Settings

- `DP_SETTINGS_PATH` must point to a directory, not a file.
- `DP_SETTINGS_PATH` should not recursively sit inside the default settings tree.
- `DP_SKIP_NLTK_DOWNLOAD=TRUE` prevents automatic NLTK package downloads.
- `DP_ROOT_PATH`, `DP_CONFIGS_PATH`, and other `DP_<VARIABLE>` overrides can
  silently redirect file locations if they are set in the shell.

If you see an unexpected path, inspect the environment before editing the
config itself.

## When To Escalate

- If the failure is about missing CUDA, PyTorch, transformers, or another
  optional backend, use the root skill’s troubleshooting reference or the
  relevant model-family sub-skill.
- If the failure is about REST or socket request payloads, route to the serving
  sub-skill instead of staying here.
- If the failure is just a bad config shape, fix it in the config workflows
  above before trying package-level repairs.
