# MONAI Bundle Config Syntax

MONAI Bundle configs are JSON or YAML dictionaries that `monai.bundle.ConfigParser` turns into Python objects, expressions, and workflow steps. Use config files to keep networks, transforms, engines, handlers, paths, metadata, and run expressions outside ordinary Python code.

## Core Parser APIs

| API | Use |
| --- | --- |
| `ConfigParser(config=None, excludes=None, globals=None)` | Create a parser from a dict or later-loaded files. Default globals include `monai`, `torch`, `np`, and `numpy`; add optional packages explicitly only when installed. |
| `parser.read_config(file_or_files_or_dict)` | Load JSON/YAML config content and preserve existing `_meta_` metadata. A sequence or comma-separated string merges files in order. |
| `parser.read_meta(file_or_files_or_dict)` | Load metadata under `_meta_`, so metadata fields can be referenced as `_meta_#...`. |
| `parser[id]` / `parser.get(id)` | Read raw config content by nested id before or after parsing. `#` and `::` both step into dict/list structures. |
| `parser[id] = value` / `parser.update({...})` | Apply overrides before `parse()` or `get_parsed_content()` so cached resolved content does not hide changes. |
| `parser.parse(reset=True)` | Resolve macros and relative ids, then register every config item. |
| `parser.get_parsed_content(id, instantiate=True, eval_expr=True, lazy=True)` | Resolve a single id as an object, evaluated expression, or raw config item depending on flags. |
| `ConfigParser.load_config_file(s)` | Load and merge JSON/YAML without instantiating objects. |
| `ConfigParser.export_config_file(config, filepath, fmt="json")` | Write JSON/YAML config files from Python dictionaries. |

## `_target_` Objects

A dict with `_target_` describes a Python callable or class and keyword arguments for instantiation.

```json
{
  "network_def": {
    "_target_": "monai.networks.nets.UNet",
    "spatial_dims": 2,
    "in_channels": 1,
    "out_channels": 2,
    "channels": [4, 8],
    "strides": [2]
  }
}
```

Useful companion keys:

| Key | Meaning |
| --- | --- |
| `_target_` | Dotted callable/class name or a resolvable callable. Required for object instantiation. |
| `_requires_` | Reference or expression to evaluate before instantiating the target, useful for side-effect dependencies. |
| `_disabled_` | Skip instantiation when set truthy. |
| `_desc_` | Human-readable description; useful in shared bundles. |
| `_mode_` | `default` calls the target, `callable` returns the callable or partial, and `debug` runs with `pdb.runcall`. |

Keep `_target_` values importable in the target runtime. If a config imports optional packages with `$import`, document those dependencies in the bundle README or metadata.

## References With `@`

`@` resolves another config item and passes the resulting object/value into the current item.

| Form | Example | Meaning |
| --- | --- | --- |
| Absolute nested id | `@network_def#channels` | Read nested key `channels` under `network_def`. |
| `::` separator | `@network_def::channels` | Equivalent to `#`; often easier to read in prose. |
| List index | `@transforms#0` | Read list element at zero-based index. |
| Same-level relative | `@#keys` | Read sibling `keys` from the same nested structure. |
| Parent relative | `@##image_key` | Read `image_key` one level above. |
| Parsed alias | `"alias": "$@target"` | Evaluate and return the object/value referenced by `target`. |

Use `@` for dependencies between Bundle components, such as a trainer referencing `@network_def`, `@optimizer`, and `@train_loader`.

## External/Macro Replacement With `%`

`%` is a textual macro replacement performed before object instantiation and expression evaluation.

```json
{
  "network_def": "%defaults.json#network_def",
  "inference_net": "%network_def"
}
```

Rules and cautions:

- `%other.json#id` copies the raw config subtree from another JSON/YAML file.
- `%id` copies from the current merged config.
- Relative macros such as `%#value` and `%##value` are resolved relative to the current nested location.
- Macro replacement is not recursively expanded forever; keep macros shallow and obvious.
- Treat macros as config templating, not runtime references; use `@` when you want a parsed object/value.

## Expressions With `$`

`$` marks a Python expression evaluated by `ConfigParser`.

```json
{
  "imports": ["$import torch"],
  "device": "$torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')",
  "scaled_lr": "$@base_lr * @world_size",
  "run": ["$print('ready')"]
}
```

Guidelines:

- `$import package` and `$from package import name` make names available to later expressions.
- Expressions can contain `@id` references; the parser resolves them into expression globals.
- Expressions can mutate referenced objects, so avoid hidden side effects unless you are building explicit workflow steps.
- Quote `$`, `#`, and `::` carefully in shells because they may be interpreted before Python Fire sees them.

## Multiple Files And Merging

`ConfigParser.load_config_files([...])`, `read_config([...])`, `ConfigWorkflow(config_file=[...])`, and CLI `--config_file` can merge multiple config files in order.

- Later files override earlier keys by default.
- Prefix a key with `+` to merge dicts with `update()` or concatenate lists with `extend()`.
- `+` merging requires both old and new values to be the same mergeable type: dict with dict or list with list.
- Keys containing `#` or `::` can override nested ids directly, such as `network_def#in_channels`.

Example override file:

```json
{
  "network_def#in_channels": 3,
  "+imports": ["$import torch"],
  "+preprocessing#transforms": ["$@extra_transform"]
}
```

## CLI Overrides

Bundle CLI commands accept keyword overrides after command arguments. The override key becomes a config id.

```bash
python -m monai.bundle run \
  --config_file configs/inference.json \
  --meta_file configs/metadata.json \
  --network_def#in_channels 3 \
  --device "\$torch.device('cpu')"
```

Practical rules:

- Install Python Fire for CLI access.
- Use `python -m monai.bundle <command> -- --help` for command-specific help.
- Quote ids containing `#` and values containing `$`, spaces, brackets, or commas in shell scripts.
- Prefer an `args_file` for complex overrides so shell quoting does not change config semantics.
- Apply programmatic `parser.update()` before calling `parse()` or `get_parsed_content()`.

## ConfigWorkflow And BundleWorkflow

`BundleWorkflow` defines `initialize`, `run`, `finalize`, property access, `workflow_type`, and metadata handling. `ConfigWorkflow` implements those stages from config ids.

| Field | Default | Purpose |
| --- | --- | --- |
| `config_file` | required for `ConfigWorkflow` | JSON/YAML file or files to load and merge. |
| `meta_file` | `configs/metadata.json` next to the config root | Metadata loaded under `_meta_`. |
| `logging_file` | `configs/logging.conf` if present | Python logging configuration; `False` skips logging setup. |
| `init_id` | `initialize` | Expression or expression list evaluated before run; optional. |
| `run_id` | `run` | Expression or expression list evaluated by `run`; required for `ConfigWorkflow.run()`. |
| `final_id` | `finalize` | Expression or expression list evaluated after run; optional. |
| `workflow_type` | `train` | `train`/`training` or `infer`/`inference`/`eval`/`evaluation`; controls property checks. |
| `tracking` | `None` | Optional experiment tracking settings, often requiring optional tracking packages. |

`create_workflow(workflow_name=None, config_file=None, args_file=None, **kwargs)` locates `ConfigWorkflow` by default, calls `initialize()`, and returns the workflow. `run_workflow(...)` creates the workflow, runs it, and finalizes it.

## Metadata And Bundle Layout

A package-style Bundle typically contains:

```text
<bundle_name>/
  LICENSE
  configs/metadata.json
  configs/inference.json
  configs/train.json
  models/model.pt
  docs/README.md
```

Required metadata fields include version information, package versions, task/description/authors/copyright, `required_packages_version`, and `network_data_format`. `network_data_format` describes model inputs and outputs; `verify_net_in_out` uses it to create fake tensors and check output channel/dtype behavior.

## Authoring Checklist

- Keep ids stable: `network_def`, `preprocessing`, `postprocessing`, `inferer`, `trainer`, `evaluator`, `initialize`, `run`, and `finalize` are easier for agents to recognize.
- Prefer JSON/YAML primitives and `@` references; use `$` only for necessary runtime expressions.
- Put optional package imports in an `imports` list near the top of config files.
- Keep metadata and config separate: metadata describes the bundle and I/O, config defines executable components.
- Make overrides explicit and reversible; avoid editing source config when a CLI or `args_file` override is enough.
- For generated bundles, route Auto3DSeg generation logic to `apps-auto3dseg`; this sub-skill owns the resulting Bundle config and CLI behavior.
