# CLI And Config Troubleshooting

## Symptoms And Fixes

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `import recipes` raises immediately | The recipes package is intentionally not an importable public API | Use `tune run`, `tune cp`, `tune cat`, registry names, or CLI/runpy behavior. |
| `The '--config' argument is required` | `tune run` did not receive `--config <config>` in recipe args | Add `--config` after the recipe name, before overrides. |
| `Additional flag arguments not supported` | A `--flag` was passed after `--config` as a recipe override | Convert to `key=value` or use a real torchrun flag before the recipe. |
| Distributed run does not use requested workers | Torchrun flags were placed after the recipe name | Move `--nproc_per_node`, `--nnodes`, rendezvous flags, and related options before `<recipe>`. |
| Single-device recipe rejects distributed args | Registry marks the recipe `supports_distributed=False` | Choose a distributed recipe or remove torchrun options. |
| `Invalid file name` from `tune cp` | Name is not a registry recipe/config | Run `tune ls` or `inspect_tune_registry.py` and copy the exact name. |
| `is a recipe, not a config` from `tune cat` | A recipe name was passed where a config name is required | Pass one of the recipe's config names or a local YAML path. |
| `Invalid config format` from `tune cat` | Local config path does not end in `.yaml` or `.yml` | Rename the file or pass a registry config name. |
| `Could not find key ... to remove` | `~field` points to a key absent from the YAML-derived config | Inspect with `tune cat` or the bundled shape checker and remove the exact existing key. |
| `Removing components from CLI is not supported` | Override tries to remove `_component_` | Override the parent component or edit the YAML directly. |
| Config validation fails after switching components | Old keyword fields do not match the new component signature | Remove incompatible fields with `~field` or edit the YAML. |
| Gated Hugging Face download fails | Missing access approval or token | Accept model terms and use `--hf-token`, `HF_TOKEN`, or `huggingface-cli login`; do not embed tokens. |
| Kaggle download ignores output dir | CLI path uses `kagglehub.model_download`, which ignores `--output-dir` | Move/copy files after download if needed; do not rely on `--output-dir` for Kaggle. |
| `tune validate` fails on imports | Selected component requires optional dependencies | Install the relevant optional package or use `validate_config_shape.py` without `--resolve-components` for structural checks. |

## Command Ordering Checklist

For distributed execution, check the command in this order:

```bash
tune run --nproc_per_node=4 --nnodes=1 <distributed-recipe> --config <config> key=value ~field
```

- Everything before `<recipe>` is parsed as a torchrun/tune-run launch option.
- `<recipe>` is either a registry recipe name or local recipe path.
- `--config <config>` is required and is part of recipe args.
- Everything after the config value must be a torchtune recipe override token, not a new `--flag`.

## Component Switch Checklist

When changing a config component through overrides:

1. Inspect the current node with `tune cat <config>`.
2. Read the target component's public signature if available.
3. Override the parent key to the new dotpath.
4. Remove incompatible nested fields with `~field`.
5. Run `python scripts/validate_config_shape.py <config> [overrides...] --from-registry` for built-ins.
6. Run `tune validate <local-yaml>` only when all optional dependencies needed by component imports are installed.

Example:

```bash
python scripts/validate_config_shape.py llama2/7B_full --from-registry \
  optimizer=bitsandbytes.optim.PagedAdamW8bit \
  ~optimizer.fused
```

## Synthetic Hard Cases For Review

- Copy a LoRA config, switch `optimizer` from `torch.optim.AdamW` to `bitsandbytes.optim.PagedAdamW8bit`, and remove incompatible optimizer fields such as `~optimizer.fused` without editing unrelated dataset/model sections.
- Construct a distributed command where `--nproc_per_node` and `--nnodes` appear before `full_finetune_distributed`, while recipe overrides such as `epochs=1` and `output_dir=...` appear after `--config <config>`.
