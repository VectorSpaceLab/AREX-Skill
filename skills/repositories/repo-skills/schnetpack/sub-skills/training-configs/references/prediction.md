# Prediction with `spkpredict`

Use `spkpredict` after a SchNetPack model has been trained and exported into a model directory. It loads data from an ASE database, loads `best_model` from the model directory, and writes prediction batches through SchNetPack's `PredictionWriter`.

## Required fields

The packaged prediction config marks these values as required:

| Field | Meaning |
| --- | --- |
| `datapath` | ASEAtomsData database to run prediction on |
| `modeldir` | Directory containing the exported `best_model` file and, optionally, checkpoints |
| `outputdir` | Directory for prediction outputs |
| `cutoff` | Neighbor-list cutoff used by prediction transforms |

Minimal template:

```bash
spkpredict \
  datapath=/path/to/input.db \
  modeldir=/path/to/trained/run \
  outputdir=/path/to/predictions \
  cutoff=5.0
```

Run `spkpredict --help` to confirm the resolved config without launching prediction.

## Model directory behavior

Hydra sets the prediction run directory to `${modeldir}`. The prediction code then loads `best_model` from the current directory. This means `modeldir` should normally be the training run directory that contains the exported `best_model` file, not the parent `runs/` directory and not the checkpoint directory.

Expected training outputs in a standard run directory:

```text
/path/to/runs/<run.id>/
  config.yaml
  best_model
  best_model.task
  checkpoints/
    last.ckpt
    <epoch>.ckpt
```

If training used `globals.model_path=my_best_model`, the default `spkpredict` loader still expects `best_model`. Either provide/copy the expected model file in the prediction model directory or use a custom prediction config/code path that loads the alternate basename.

## Checkpoint selection

`spkpredict` uses the exported model file and can pass `ckpt_path` into Lightning `trainer.predict`. Defaults:

```text
ckpt_path: null
batch_size: 100
write_interval: epoch
enable_grad: false
write_idx_m: false
```

Common overrides:

```bash
spkpredict datapath=/path/to/input.db modeldir=/path/to/run outputdir=/path/to/preds cutoff=5.0 \
  batch_size=256 \
  trainer.accelerator=cpu trainer.devices=1
```

If a user asks for a checkpoint-specific prediction, verify whether they mean the exported `best_model` file or a Lightning checkpoint under `checkpoints/`. In the packaged prediction code, the model is loaded from `best_model`, while `ckpt_path` affects Lightning prediction state handling.

## Data transforms during prediction

The default prediction data config instantiates `schnetpack.data.ASEAtomsData` with transforms:

1. `SubtractCenterOfMass`
2. `MatScipyNeighborList` using `cutoff`
3. `CastTo32`

Prediction does not infer dataset units or training-time preprocessing from the training config. The input ASE DB must contain structures and properties in a schema compatible with the trained model. Route database creation, property keys, and unit conversion questions to `../data-pipelines/SKILL.md`.

## Output handling

Prediction outputs are written to `outputdir` at the configured `write_interval`, defaulting to `epoch`. Use a new or clearly named output directory for each run to avoid mixing batches from different models or datasets:

```bash
spkpredict datapath=/path/to/eval.db \
  modeldir=/path/to/runs/qm9-painn \
  outputdir=/path/to/preds/qm9-painn-eval \
  cutoff=5.0 \
  batch_size=100 \
  write_idx_m=true
```

Set `write_idx_m=true` when downstream analysis needs mapping back to molecule indices.

## Sanity checklist

Before giving a prediction command, confirm:

- `modeldir/best_model` exists or the user knows how their exported model is named.
- `datapath` is an ASEAtomsData database readable by SchNetPack.
- `cutoff` matches the training cutoff closely enough for the model and neighbor list.
- `outputdir` is intentionally chosen and writable.
- Device choices are explicit for portable commands, e.g. `trainer.accelerator=cpu trainer.devices=1`.

Do not run predictions over large databases, GPU workloads, or generated output directories unless the user explicitly asks for execution.
