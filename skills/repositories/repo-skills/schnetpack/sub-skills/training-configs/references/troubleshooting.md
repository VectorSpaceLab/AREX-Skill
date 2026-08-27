# Training and Prediction Troubleshooting

Use `--help` first whenever possible. It composes the Hydra config and catches many override mistakes without training, downloading datasets, or running prediction.

## `run.data_dir` missing or incomplete config

Symptoms:

- `Config incomplete! You need to specify the data directory data_dir.`
- `Config incomplete! You have to specify at least data and model!`
- Hydra reports missing mandatory values such as `???`.

Likely causes:

- Running bare `spktrain` without an experiment or explicit `model`, `data`, and task outputs.
- Starting from `data=custom` without required fields such as `data.datapath`, `data.num_train`, or `data.num_val`.
- Forgetting `run.data_dir` when using benchmark experiments that expect `${run.data_dir}`.

Fix patterns:

```bash
spktrain experiment=qm9_atomwise run.data_dir=/path/to/data --help
```

```bash
spktrain data=custom model=nnp model/representation=painn \
  data.datapath=/path/to/data.db data.num_train=900 data.num_val=100 \
  run.data_dir=/path/to/data --help
```

Prefer packaged experiments for QM9, MD17, and rMD17 because they fill model, data, transforms, and task outputs together.

## Dot versus slash override mistakes

Symptoms:

- Hydra cannot find a key such as `model/representation.n_interactions`.
- An override silently edits a scalar but does not switch the intended config template.
- Hydra reports no match in config group or no such key.

Fix:

- Use `/` to choose a config group option: `model/representation=schnet`.
- Use `.` to edit fields after the option is selected: `model.representation.n_interactions=6`.

Correct combined pattern:

```bash
spktrain experiment=qm9_atomwise \
  model/representation=schnet \
  model.representation.n_interactions=6 \
  globals.cutoff=5.0 \
  --help
```

## Adding missing keys or optional groups

Hydra requires `+` when adding a key that is not already in the composed config. SchNetPack docs mention this for optional PyTorch matrix multiplication precision:

```bash
spktrain experiment=qm9_atomwise +matmul_precision=high --help
```

For config groups, first inspect the composed defaults with `--help`. If the group is already present, override it normally, e.g. `logger=csv` or `trainer=ddp_trainer`. If the entry is absent or nullable in your custom config, use Hydra's add syntax, e.g. `+logger=csv` or `+callbacks/ema=ema`, depending on how the defaults are structured.

## Existing `config.yaml` and resume behavior

When the run directory already contains `config.yaml`, SchNetPack assumes continuation:

- It saves the old config as `config.old.N.yaml`.
- If `run.ckpt_path` is null and `checkpoints/last.ckpt` exists, it resumes from `checkpoints/last.ckpt`.
- Relative checkpoint paths are resolved after Hydra changes into `${run.path}/${run.id}`.

If continuation is intended:

```bash
spktrain experiment=md17 data.molecule=uracil \
  run.path=/path/to/runs run.id=md17-uracil \
  run.ckpt_path=checkpoints/last.ckpt
```

If a fresh run is intended, change `run.id` or cleanly archive the old run directory before launching. Do not reuse a run id casually because logs, configs, checkpoints, and best-model files can be mixed.

## Dataset downloads and unsafe smoke tests

Benchmark experiments may download datasets into `run.data_dir` if expected files are missing. Do not use a real training command as a syntax smoke test. Safer options:

```bash
spktrain experiment=qm9_atomwise run.data_dir=/path/to/data --help
spkpredict --help
```

If the user explicitly asks for a bounded execution check on existing local data:

```bash
spktrain experiment=qm9_atomwise \
  run.data_dir=/path/to/existing/data \
  run.path=/tmp/spk-runs run.id=fast-dev \
  trainer.fast_dev_run=true \
  data.num_workers=0 data.num_val_workers=0 data.num_test_workers=0
```

This may still instantiate the dataset and access files; confirm that the data already exists and that the side effects are acceptable.

## Logger and optional dependency failures

Symptoms:

- Import errors for `aim`, `wandb`, or TensorBoard packages.
- Authentication or service errors from experiment trackers.

Fix patterns:

- Use the low-dependency CSV logger: `logger=csv`.
- Use TensorBoard only when installed: `logger=tensorboard`.
- Treat `logger=aim` and `logger=wandb` as opt-in because they may require extra packages, credentials, or external services.

## Callback or checkpoint monitor failures

Symptoms:

- Checkpoint or early-stopping callbacks complain that `val_loss` or another monitor is missing.
- No `best_model` is exported after training.

Likely causes:

- Custom `task.outputs` does not log validation metrics with the monitored name.
- Validation split is missing or too small.
- Callback monitor was changed without matching logged metrics.

Fix patterns:

```bash
spktrain experiment=qm9_atomwise \
  callbacks.model_checkpoint.monitor=val_loss \
  callbacks.early_stopping.monitor=val_loss \
  data.num_val=1000 --help
```

For custom outputs, ensure task outputs and validation data produce the metric being monitored. Route output-module and task-output design to `../models-atomistic/SKILL.md` when the fix requires changing model semantics.

## Prediction required fields

Symptoms:

- Hydra reports missing `datapath`, `modeldir`, `outputdir`, or `cutoff`.
- Prediction fails to load `best_model`.
- Prediction writes into an unexpected directory.

Fix pattern:

```bash
spkpredict \
  datapath=/path/to/input.db \
  modeldir=/path/to/runs/run-id \
  outputdir=/path/to/predictions/run-id \
  cutoff=5.0 \
  trainer.accelerator=cpu trainer.devices=1 \
  --help
```

Remember that prediction changes into `modeldir` and loads `best_model` there. `modeldir` should be the run directory containing `best_model`, not the parent runs directory or the `checkpoints/` directory.

## Custom config not found

Symptoms:

- Hydra cannot find `experiment=my_experiment`.
- `--config-dir` appears ignored.

Fix:

- Put custom experiments under `experiment/my_experiment.yaml` or `configs/experiment/my_experiment.yaml` relative to the working directory.
- If using `--config-dir`, point it to the base directory that contains `experiment/`, not to the experiment directory itself.

```bash
spktrain --config-dir=/path/to/configs experiment=my_experiment --help
```

## When to redirect the task

Redirect to sibling sub-skills instead of stretching training-configs when:

- The issue is ASE DB creation, property names, units, transforms, or splits: `../data-pipelines/SKILL.md`.
- The issue is representation internals, custom output modules, forces/stress modules, or task-output semantics: `../models-atomistic/SKILL.md`.
- The issue starts after a trained model exists and concerns ASE calculators, MD, deployment, or LAMMPS: `../interfaces-md/SKILL.md`.
