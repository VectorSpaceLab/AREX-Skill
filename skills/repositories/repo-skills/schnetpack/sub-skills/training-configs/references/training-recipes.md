# Training Recipes

Start `spktrain` commands from a packaged experiment whenever possible, then override only the fields that matter for the user's run. Always make side effects explicit with `run.data_dir`, `run.path`, and `run.id`.

## QM9 atomwise property

Default template:

```bash
spktrain experiment=qm9_atomwise \
  run.data_dir=/path/to/data \
  run.path=/path/to/runs \
  run.id=qm9-energy-u0
```

Useful overrides:

```bash
spktrain experiment=qm9_atomwise \
  run.data_dir=/path/to/data \
  run.path=/path/to/runs \
  run.id=qm9-painn-energy \
  globals.property=energy_U0 \
  globals.cutoff=5.0 \
  globals.lr=5e-4 \
  data.batch_size=100
```

The experiment sets `data=qm9`, `model=nnp`, default representation `painn`, an atomwise output module, offset transforms, and one task output for `globals.property`. To switch representation groups, use slash syntax:

```bash
spktrain experiment=qm9_atomwise \
  model/representation=schnet \
  model.representation.n_interactions=6 \
  globals.cutoff=5.0
```

Use dot syntax for fields under the selected representation, such as `model.representation.n_atom_basis=128`.

## QM9 dipole moment

Use `qm9_dipole` when the target is a molecular dipole magnitude instead of an extensive atomwise scalar:

```bash
spktrain experiment=qm9_dipole \
  run.data_dir=/path/to/data \
  run.path=/path/to/runs \
  run.id=qm9-dipole \
  globals.property=dipole_moment
```

This template uses `schnetpack.atomistic.DipoleMoment` rather than `Atomwise`. Route requests to change output module internals to `../models-atomistic/SKILL.md`.

## MD17 and rMD17 energy-force training

MD17/rMD17 templates train energy and forces with force-heavy loss weights and molecule-specific ASE DB paths:

```bash
spktrain experiment=md17 \
  data.molecule=uracil \
  run.data_dir=/path/to/md17-data \
  run.path=/path/to/runs \
  run.id=md17-uracil-painn
```

```bash
spktrain experiment=rmd17 \
  data.molecule=aspirin \
  data.split_id=1 \
  run.data_dir=/path/to/rmd17-data \
  run.path=/path/to/runs \
  run.id=rmd17-aspirin-split1
```

Common energy-force overrides:

```bash
spktrain experiment=md17 data.molecule=uracil \
  globals.cutoff=5.0 \
  globals.lr=1e-3 \
  data.batch_size=10 \
  task.outputs.0.loss_weight=0.01 \
  task.outputs.1.loss_weight=0.99
```

The MD17/rMD17 experiments set `globals.energy_key=energy`, `globals.forces_key=forces`, units `kcal/mol` and `kcal/mol/Ang`, an `Atomwise` energy output, a `Forces` output, and matching task outputs. Route force/stress module design changes to `../models-atomistic/SKILL.md`.

## Custom ASE database training

Use `data=custom` or a custom experiment when the dataset is an ASEAtomsData database prepared elsewhere:

```bash
spktrain data=custom model=nnp model/representation=painn \
  data.datapath=/path/to/custom.db \
  data.num_train=900 data.num_val=100 data.batch_size=32 \
  run.data_dir=/path/to/data \
  run.path=/path/to/runs \
  run.id=custom-energy \
  globals.cutoff=5.0 globals.lr=5e-4 \
  model.output_modules='[{_target_: schnetpack.atomistic.Atomwise, output_key: energy, n_in: ${model.representation.n_atom_basis}, aggregation_mode: sum}]' \
  task.outputs='[{_target_: schnetpack.task.ModelOutput, name: energy, loss_fn: {_target_: torch.nn.MSELoss}, loss_weight: 1.0}]'
```

For maintainability, prefer a project-local `experiment/my_custom.yaml` once outputs, transforms, units, and splits become complex. Use data-pipelines to prepare the database, choose `property_units`, set `distance_unit`, and verify property keys before building the training command.

## Trainer controls

Common PyTorch Lightning trainer overrides:

| Goal | Overrides |
| --- | --- |
| Short debug run | `trainer.fast_dev_run=true` |
| Limit epochs | `trainer.max_epochs=20` |
| Use CPU explicitly | `trainer.accelerator=cpu trainer.devices=1` |
| Use one CUDA device if available | `trainer.accelerator=gpu trainer.devices=1` |
| Reduce workers for notebooks/CI | `data.num_workers=0 data.num_val_workers=0 data.num_test_workers=0` |
| Use mixed precision where supported | `trainer.precision=16-mixed` or Lightning-supported precision string |
| Improve reproducibility | `seed=123 trainer.deterministic=true` |

`trainer=debug_trainer` selects a packaged short debug trainer, but still inspect with `--help` because the config contains Lightning-version-sensitive fields.

## Logger choices

Default logging is TensorBoard:

```bash
spktrain experiment=qm9_atomwise logger=tensorboard
```

Other packaged logger groups include:

```bash
spktrain experiment=md17 logger=csv
spktrain experiment=md17 logger=aim run.experiment=md17_uracil
spktrain experiment=md17 logger=wandb
```

Use `logger=csv` for low-dependency local runs. `aim` and `wandb` may require optional packages, services, credentials, or user-specific setup; do not assume they are safe in a generic environment.

## Callback and checkpoint controls

Default callbacks include model checkpointing, early stopping, LR monitoring, and EMA in the base train config. Useful overrides:

```bash
spktrain experiment=qm9_atomwise \
  callbacks.model_checkpoint.monitor=val_loss \
  callbacks.model_checkpoint.save_top_k=1 \
  callbacks.model_checkpoint.save_last=true \
  callbacks.model_checkpoint.dirpath=checkpoints/ \
  callbacks.early_stopping.patience=200 \
  callbacks.ema.decay=0.995
```

SchNetPack's checkpoint callback also saves a deployed model at `${globals.model_path}`, which defaults to `best_model`, and training writes `${globals.model_path}.task` for the Lightning task. Change the exported model basename with:

```bash
spktrain experiment=qm9_atomwise globals.model_path=my_best_model
```

Downstream tools often expect `best_model`; changing this name means prediction/deployment commands must load the chosen basename or run from a directory where the expected model exists.

## Resume and storage behavior

When `spktrain` starts in a run directory that already contains `config.yaml`, it treats the run as a continuation, saves the previous config as `config.old.N.yaml`, and uses `checkpoints/last.ckpt` if `run.ckpt_path` is not set and that file exists.

Explicit resume command:

```bash
spktrain experiment=md17 data.molecule=uracil \
  run.path=/path/to/runs \
  run.id=md17-uracil-painn \
  run.ckpt_path=checkpoints/last.ckpt
```

Because Hydra changes into `${run.path}/${run.id}`, relative `run.ckpt_path=checkpoints/last.ckpt` resolves inside the run directory. Use an absolute checkpoint path when resuming from a different run.

## Side-effect checklist before launch

Before giving a final training command, confirm:

- `run.data_dir` points to an intended data/cache location; benchmark experiments may download datasets if files are absent.
- `run.path` and `run.id` point to the intended output directory and will not overwrite an unrelated run.
- `experiment=...` or explicit `model`, `data`, and `task.outputs` are present.
- Data property names and units match the database; route preparation and schema checks to data-pipelines.
- GPU, logger services, and long training are user-approved.
