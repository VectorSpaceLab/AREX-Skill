# Inference and interpolation workflow

## Normal generation

Use a trained checkpoint to transfer one target style to a source object file:

```sh
python infer.py \
  --model_dir=checkpoint/experiment_0_batch_16 \
  --batch_size=16 \
  --source_obj=experiment/data/val.obj \
  --embedding_ids=0 \
  --save_dir=inferred
```

If `embedding_ids` has one integer, every batch uses that style. If it has
multiple integers, the script samples randomly from the list for each batch.

## Interpolation

To generate a sequence between style IDs, pass `--interpolate=1` and at least
two embedding IDs:

```sh
python infer.py \
  --model_dir=checkpoint/experiment_0_batch_16 \
  --batch_size=10 \
  --source_obj=experiment/data/val.obj \
  --embedding_ids=0,1 \
  --save_dir=frames \
  --interpolate=1 \
  --steps=10 \
  --output_gif=transition.gif \
  --uroboros=1
```

`steps` controls the number of interpolation segments between each pair. With
`uroboros=1`, the final style connects back to the first style.

## Exporting generator weights

When you want to preserve only the generator portion of a trained checkpoint:

```sh
python export.py \
  --model_dir=checkpoint/experiment_0_batch_16 \
  --batch_size=16 \
  --save_dir=exported-generator
```

This saves generator-only variables under the requested output directory.

## Path and batch planning

- `source_obj` should be a zi2zi `.obj` file produced by the data-preparation
  stage.
- `model_dir` should be the concrete checkpoint directory that contains TensorFlow
  checkpoint state, not just the parent experiment folder.
- `batch_size` should usually match the training batch size unless the model and
  checkpoint were explicitly designed to restore under a different batch.
- `save_dir` should exist or be creatable before a long inference run.

## Safe checks before running

- Confirm `infer.py --help` and `export.py --help` work in the target legacy
  environment.
- Inspect the checkpoint directory for checkpoint state files.
- Confirm the source object file contains at least one record and the labels you
  want to render.
- For interpolation, confirm you really want the embeddings to be traversed in
  a chain or loop before writing many frame PNGs.

## Using the planner helper

The bundled planner prints validated commands without running TensorFlow:

```sh
python sub-skills/inference-and-export/scripts/plan_zi2zi_inference.py \
  infer \
  --model-dir checkpoint/experiment_0_batch_16 \
  --source-obj experiment/data/val.obj \
  --embedding-ids 0,1,2 \
  --save-dir inferred
```
