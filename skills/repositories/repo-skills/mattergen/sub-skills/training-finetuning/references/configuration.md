# Hydra configuration and resource controls

MatterGen 1.0.3 uses Hydra 1.3.1. The training entry point composes files
under the package `conf` directory, prints the resolved config, and passes a
read-only merged config to the diffusion runner. Fine-tuning uses the same
config root with `finetune.yaml` as its default config name.

## Root configs

| Selection | Main effect | Important defaults |
|---|---|---|
| `default` | base diffusion training | `data_module=mp_20`, default trainer/lightning/diffusion/model/corruption, `auto_resume: True` |
| `csp` | CSP training | `data_module=mp_20`, CSP diffusion module/corruption, `auto_resume: true` |
| `finetune` | adapter fine-tuning | `data_module=mp_20`, adapter default, `max_epochs: 200`, learning rate `5e-6`, W&B logger job type `train_finetune` |

Use `--config-name=csp` only for the CSP root config. Do not use it as a
substitution for `sampling-config-name` during generation.

The normal default output expression is equivalent to:

```text
OUTPUT_DIR or outputs/singlerun/<date>/<time>
```

Hydra's `now` interpolation makes the concrete path unique by timestamp. The
training scripts save a resolved config; base training's `auto_resume` adds a
checkpoint search directory below the trainer root. The finetune script saves
its effective, source-derived config through Lightning callbacks.

## Data modules and cache expectations

`data_module=mp_20` selects `data_module/mp_20.yaml`; `data_module=alex_mp_20`
selects `data_module/alex_mp_20.yaml`. Both instantiate
`mattergen.common.data.datamodule.CrystDataModule` with train/validation
`CrystalDataset.from_cache_path` objects. The config's default root is based on
`${oc.env:PROJECT_ROOT}/../datasets/cache/<dataset-name>`; resolve this before
launch and override `data_module.root_dir` only when the cache layout differs.

The dataset configs expose:

- `properties: []` by default;
- transforms that symmetrize lattices and set a chemical-system string;
- a dataset transform that filters sparse properties;
- batch expressions based on a nominal total training batch of 512;
- `num_workers` zero in the supplied configs;
- `max_epochs` of 900 for MP-20 and 2200 for Alex-MP-20.

Use an override, not a package edit, to select a prepared cache:

```text
data_module=alex_mp_20
data_module.root_dir=/path/to/datasets/cache/alex_mp_20
data_module.properties=["dft_band_gap"]
```

The absolute example is a placeholder only; keep real machine paths out of
shared skill files and supply them at runtime. A requested property must have a
`<property>.json` cache file in each consumed split. The builder rejects source
ids outside its registered property allow-list.

## Trainer, device, and memory

The supplied trainer config contains these material controls:

- `accelerator: gpu`, `devices: 1`, `num_nodes: 1`, `precision: 32`;
- `accumulate_grad_batches: 1`;
- gradient clipping by value (`0.5`);
- validation every five epochs;
- default DDP strategy with `find_unused_parameters: true`;
- W&B logger plus learning-rate, checkpoint, progress, and property-scaler
  callbacks.

Useful overrides are:

```text
trainer.accelerator=cpu
trainer.devices=1
trainer.precision=32
trainer.accumulate_grad_batches=4
trainer.max_epochs=1
trainer.limit_val_batches=1
~trainer.logger
```

The last three are appropriate only for an explicitly approved smoke run; they
are not a silent replacement for the documented schedule. On Apple Silicon,
use both `~trainer.strategy` and `trainer.accelerator=mps`, as in the README.
The inspected private environment proved CUDA tensor operation on an A100, but
runtime files must remain backend-neutral.

The training batch expression is roughly
`512 // accumulate // (devices * nodes)`. If the computed integer becomes too
small or zero, correct the control values rather than assuming Lightning will
repair it. If a single GPU OOMs on Alex-MP-20, raise accumulation and preflight
again; this reduces per-step batch memory while retaining the nominal total
batch, though it does not make the model or data inexpensive.

## Diffusion and model tree

The default diffusion module includes position, cell, and atomic-number loss;
CSP disables atomic-number loss. The `mattergen` model uses hidden dimension
512, GemNetT, four blocks, and a latent dimension expression that includes one
time encoding plus each base-model property embedding. The default corruption
uses continuous position/cell SDEs and a masked discrete atomic-number
corruption; CSP uses only the continuous parts.

The default lightning module uses Adam with learning rate `1e-4` and a
ReduceLROnPlateau schedule (factor `0.6`, patience `100`, minimum `1e-6`).
Fine-tuning overrides the partial optimizer learning rate to `5e-6` in
`finetune.yaml`. These are source defaults, not a claim about a successful
run.

## Hydra override grammar used here

- `key=value` changes an existing scalar or mapping value.
- `+group/path@destination=name` adds a config-group node; this is why property
  embeddings use a leading `+` in the README fine-tune command.
- `~trainer.logger` deletes the default W&B logger.
- `++key=value` forces an add-or-change operation when appropriate.
- Lists such as `data_module.properties=["p1","p2"]` must be quoted as a
  shell argument when the shell treats brackets specially.
- Environment variables such as `$PROPERTY` are expanded by the shell before
  Hydra sees the token; use braces or quoting when composing longer values.

Use the bundled preflight for syntax and file existence. It intentionally does
not implement all Hydra grammar and does not attempt interpolation or
instantiation. A preflight pass cannot prove that YAML interpolation resolves,
that a dataset has the requested JSON, or that a backend can execute the
model.

## Adapter and checkpoint controls

The adapter config starts with:

```text
pretrained_name: mattergen_base
model_path: null
load_epoch: last
full_finetuning: true
adapter.property_embeddings_adapt: {}
```

`adapter.model_path` takes precedence if both source selectors are set, but
supplying both is an avoidable ambiguity. `load_epoch` accepts `last`, `best`,
or an integer when matching checkpoint files exist. `full_finetuning=false`
freezes source-matching parameters; it is not the same as training a new base
model.

During fine-tuning, the script copies the source diffusion/denoiser config and
replaces the denoiser target with `GemNetTCtrl`. New condition names become the
adapter's `condition_on_adapt` fields. A new adapter condition must not duplicate
a property already in the source model's base `property_embeddings`.
