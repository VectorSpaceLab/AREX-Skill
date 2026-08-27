# Config Reference

Torchtune recipes receive a single OmegaConf `DictConfig`. Built-in recipes normally decorate `main(cfg)` with `torchtune.config.parse`, then instantiate selected fields with `torchtune.config.instantiate`.

## Public Config APIs

| API | Signature | Use |
| --- | --- | --- |
| `torchtune.config.parse` | `parse(recipe_main)` | Decorates a recipe main function, requires `--config`, loads YAML defaults, collects CLI overrides, and passes a merged `DictConfig` to the recipe. |
| `torchtune.config.instantiate` | `instantiate(config, *args, caller_globals=None, **kwargs)` | Recursively creates an object from a dict/`DictConfig` containing `_component_`; explicit kwargs override config fields. |
| `torchtune.config.validate` | `validate(cfg)` | Checks top-level `_component_` nodes can be resolved and keyword arguments bind to component signatures. |

## YAML Shape

A config is a YAML mapping of recipe parameters:

```yaml
seed: 123
output_dir: ./runs/example
device: cuda
dtype: bf16
optimizer:
  _component_: torch.optim.AdamW
  lr: 2e-5
  fused: true
```

Guidelines:

- Keep configs airtight: include fields the recipe actually reads or instantiates.
- Prefer public dotpaths without private underscore modules, such as `torchtune.datasets.alpaca_dataset` rather than an internal file path.
- Use `null` for optional values that should become Python `None` after OmegaConf resolution.
- Treat paths, tokens, and machine-specific cache locations as run-local choices, not reusable public skill content.

## `_component_` Dotpaths

A node with `_component_` is instantiated by resolving the dotpath and passing sibling keys as keyword arguments:

```yaml
tokenizer:
  _component_: torchtune.models.llama2.llama2_tokenizer
  path: ./models/llama2/tokenizer.model

dataset:
  _component_: torchtune.datasets.alpaca_dataset
  train_on_input: false
```

Recipe setup commonly looks like:

```python
tokenizer = config.instantiate(cfg.tokenizer)
dataset = config.instantiate(cfg.dataset, tokenizer)
```

`instantiate` details that matter for agents:

- It accepts a dict or OmegaConf `DictConfig`; `None` returns `None`.
- The target config must include `_component_`, otherwise `InstantiationError` is raised.
- Nested dict/list values are recursively instantiated when they contain `_component_`.
- Interpolations are resolved before object creation.
- Positional args apply to the top-level component; kwargs merge into and override config keys.
- `caller_globals` can resolve simple local names, but reusable configs should prefer importable public dotpaths.

## OmegaConf Interpolation

Use `${field}` when multiple config fields should share a value:

```yaml
output_dir: ./runs/alpaca
metric_logger:
  _component_: torchtune.training.metric_logging.DiskLogger
  log_dir: ${output_dir}
```

Torchtune intentionally keeps config interpolation unresolved during initial CLI parse, then resolves values during `instantiate` and logging. This preserves editability while allowing consistent runtime values.

## CLI Overrides

Recipe overrides after `--config` are parsed as a dotlist and merged over the YAML:

```bash
tune run lora_finetune_single_device \
  --config llama2/7B_lora_single_device \
  output_dir=./runs/lora epochs=1 model.lora_rank=16
```

Override rules:

- Use `key=value`; unknown `--flags` after `--config` are rejected.
- Dot notation updates nested keys, such as `optimizer.lr=1e-5`.
- Values are interpreted by OmegaConf, so booleans, numbers, lists, and `null`-like values should be written carefully.
- Torchtune maps CLI value `None` to OmegaConf null.
- Keys containing `max_filename` are forced to string to preserve leading zeroes.

## Overriding Components

If a YAML key currently points to a component node, assigning to the parent key changes its `_component_` field:

```bash
tune run lora_finetune_single_device \
  --config llama2/7B_lora_single_device \
  dataset=torchtune.datasets.slimorca_dataset dataset.train_on_input=True
```

This is equivalent to changing `dataset._component_` while preserving compatible nested fields. Remove incompatible nested fields when switching components.

## Removing Fields With `~`

Use `~field.path` to remove a key from the YAML before applying other overrides:

```bash
tune run --nproc_per_node=4 full_finetune_distributed \
  --config llama2/7B_full \
  optimizer=bitsandbytes.optim.PagedAdamW8bit \
  ~optimizer.fused
```

Removal rules:

- Removal only works for keys that exist in the YAML-derived config.
- Removing `_component_` itself is not supported.
- Removing a nested key can also remove empty parent containers.
- Use removals when changing a component to one that rejects old keyword arguments.

## Safe Preflight Without Training

Use the bundled helper to inspect config shape and override effects:

```bash
python scripts/validate_config_shape.py llama2/7B_full \
  --from-registry \
  optimizer=bitsandbytes.optim.PagedAdamW8bit \
  ~optimizer.fused
```

The helper can resolve registry config names, apply torchtune-style override/removal semantics, report `_component_` nodes, and optionally import component paths with `--resolve-components`. It does not instantiate models, datasets, optimizers, tokenizers, or launch a recipe.
