# Training and fine-tuning workflows

This runbook keeps expensive actions behind explicit user intent. The default
workflow ends at a parser/config preflight. It never treats `--help`, import
probes, or a resolved config as evidence that a model trained.

## 1. Common gate

1. Confirm the operation: base training, CSP training, or fine-tuning.
2. Confirm the dataset name and cache root. `mp_20` and `alex_mp_20` are
   separate config groups with different documented epoch schedules and
   property lists.
3. Confirm the target backend. The inspected environment proved public imports
   and an available CUDA tensor smoke on an A100; it did not prove every
   trainer/backend combination.
4. Confirm a writable, dedicated output location. Use `OUTPUT_DIR` or a Hydra
   output override rather than reusing a valuable run accidentally.
5. Assemble the command and run
   `<mattergen-skill-root>/sub-skills/training-finetuning/scripts/validate_hydra_overrides.py --config-root <mattergen-config-root> ...`.
6. Review errors and warnings, especially effective batch size, property files,
   logger state, and adapter source selection.
7. Only after an explicit launch decision run the command. Record the resolved
   config and checkpoint paths outside this runtime skill.

## 2. Base training

Base training instantiates `DiffusionLightningModule` from the default
lightning-module, diffusion-module, model, corruption, trainer, and data-module
configs. It starts with the model's default optimizer/scheduler configuration;
it does not load a pre-trained adapter.

Recommended documented entry points:

```bash
mattergen-train data_module=mp_20 ~trainer.logger
mattergen-train data_module=alex_mp_20 ~trainer.logger trainer.accumulate_grad_batches=4
```

The default base config has `auto_resume: True`. `mattergen.diffusion.run.main`
adds a checkpoint callback below the trainer's run root and chooses the latest
checkpoint there when resuming. Do not combine a manually supplied
`checkpoint_path` with `auto_resume: true`: the source raises an ambiguity
error. A fresh output directory is the safest way to force a fresh run.

The README reports a documented MP-20 reference (`loss_val` about 0.4 after 360
epochs/about 80k steps), but no full training run was performed during skill
construction. Do not use that number as a local acceptance result.

## 3. CSP training

CSP uses `--config-name=csp`, which selects the CSP diffusion module and
corruption. It keeps positions and cells in the loss while setting
`include_atomic_numbers: False`; it is intended to support later conditioning
on a specific composition. Use the matching sampling route after training; do
not load a CSP checkpoint with an unconditional sampling config without
checking the model/config compatibility.

```bash
mattergen-train --config-name=csp data_module=mp_20 ~trainer.logger
```

CSP also enables `auto_resume: true`. Apply the same output/checkpoint
ambiguity rule as base training.

## 4. Fine-tuning from a published checkpoint

Fine-tuning composes `finetune.yaml`, creates the data module and trainer, then
`mattergen.scripts.finetune` loads a checkpoint through `MatterGenCheckpointInfo`
and copies the source denoiser configuration into a `GemNetTAdapter`. New
properties are installed in `adapter.adapter.property_embeddings_adapt` and
are marked in the adapter's `condition_on_adapt` list. The script adds config
callbacks to the trainer and calls `trainer.fit` with no resume checkpoint.

A safe order is:

1. Choose a published `adapter.pretrained_name`, such as `mattergen_base`, or
   choose `adapter.model_path`, not both.
2. Confirm the chosen data module contains the property cache file in every
   split needed by the datamodule.
3. Add one property-embedding group under the adapter and the same property to
   `data_module.properties`.
4. Disable W&B for a local trial with `~trainer.logger`.
5. Increase accumulation before reducing model capacity when VRAM is the
   problem.
6. Preflight and only then launch `mattergen-finetune`.

`full_finetuning: true` is the adapter default. With `full_finetuning: false`,
the adapter script freezes parameters whose names were present in the source
checkpoint; state this choice explicitly because it changes the optimization
problem.

## 5. Multi-property fine-tuning

Treat the property list and adapter mapping as a pair. For properties `p1` and
`p2`, both of these must be present:

```text
+lightning_module/diffusion_module/model/property_embeddings@adapter.adapter.property_embeddings_adapt.p1=p1
+lightning_module/diffusion_module/model/property_embeddings@adapter.adapter.property_embeddings_adapt.p2=p2
data_module.properties=["p1","p2"]
```

Use the exact same spelling, including underscores, in all three places. The
adapter rejects a new condition that is already in the base model's
`property_embeddings`; remove the duplicate adapter entry rather than trying
to override it. For joint conditioning, sparse labels matter: the default
`SetEmbeddingType(dropout_fields_iid=false)` only uses the conditional state
when all conditional fields are present in a sample.

## 6. Custom-property workflow

Follow [custom-properties.md](custom-properties.md). A new CSV column alone is
not sufficient: the current dataset builder only persists columns registered
in its property-source allow-list, and a training config needs a matching
embedding YAML. Existing source ids and embedding configs are the config-only
path. A truly new source id or embedding type requires the source-level change
described there; do not claim that a package-internal code change was avoided
when it was not.

## 7. Failure/recovery loop

- If preflight fails, do not launch; correct the override or config root.
- If Hydra rejects an override, preserve the exact command and compare its
  prefix (`+`, `~`) and list quoting with [configuration.md](configuration.md).
- If data loading fails, inspect cache files and property JSONs before changing
  model settings.
- If a trainer fails after creating output, inspect the saved `config.yaml` and
  checkpoint directory. Resume only when the run is known to be the intended
  run and auto-resume semantics are unambiguous.
- If a source checkpoint fails to load, verify model path layout, `load_epoch`,
  and code/checkpoint compatibility. Do not delete the source checkpoint.
- If W&B blocks startup and logging is not required, rerun a deliberate local
  command with `~trainer.logger`; do not edit package code to bypass logging.
