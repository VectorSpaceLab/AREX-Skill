# Forward Inference from a Checkpoint

## Purpose

Read this when the user wants to run Torch Points3D on unlabeled point clouds
using a checkpoint from a previous training run. This workflow is more
side-effectful than a model API smoke: it reads a checkpoint, instantiates a
forward dataset class, iterates dataloaders, and writes `.npy` prediction files.

## Required inputs

- A checkpoint run directory containing `<model_name>.pt`.
- A valid `model_name` and `weight_name`.
- An input data root compatible with the checkpoint's dataset family and its `FORWARD_CLASS`.
- An output directory for prediction `.npy` files.
- A Torch Points3D environment with all dependencies needed by the model and dataset.
- Optional data/config overrides for the checkpoint data config.

## Preflight first

```bash
python sub-skills/training-evaluation/scripts/forward_preflight.py \
  --checkpoint-dir /path/to/run \
  --model-name pointnet2_charlesssg \
  --weight-name latest \
  --input-path /path/to/unlabeled-points \
  --output-path /path/to/predictions
```

The preflight checks path existence, writable output, and checkpoint file
presence. It does not import Torch Points3D, instantiate the model, or write
predictions.

## Runtime behavior distilled from the repo workflow

The forward workflow:

1. Chooses device from CUDA availability and the config's CUDA setting.
2. Opens `ModelCheckpoint(checkpoint_dir, model_name, weight_name, strict=True)`.
3. Reads the checkpoint's `data_config` and changes its dataset class to the training dataset class's `FORWARD_CLASS`.
4. Sets the checkpoint data root to the user-provided input path.
5. Applies any dataset-specific or dataset-property overrides.
6. Creates the model from checkpoint weights.
7. Instantiates the forward dataset and dataloaders.
8. Runs `model.set_input(data, device)` and `model.forward()` over test loaders.
9. Calls `dataset.predict_original_samples(data, model.conv_type, model.get_output())` and saves each prediction dictionary entry as `<source>_pred.npy`.

## Command template

The exact Hydra command depends on the copied/available forward config in the
user's project. The important runtime fields are:

```bash
python forward.py \
  checkpoint_dir=/path/to/run \
  model_name=<checkpoint-basename> \
  weight_name=latest \
  input_path=/path/to/unlabeled-data \
  output_path=/path/to/predictions \
  batch_size=1 \
  num_workers=0 \
  cuda=false
```

If the user's forward script uses different field names, keep the same semantic
mapping: checkpoint directory, model name, weight name, input root, output root,
batch size, worker count, and CUDA toggle.

## Caveats

- The dataset class must expose `FORWARD_CLASS`; not every dataset wrapper does.
- Forward inference may still need dataset metadata, category mappings, original sample ids, or preprocessing caches.
- Sparse or registration checkpoints need their optional backends.
- Prediction filenames come from keys returned by `predict_original_samples`; validate the dataset method before promising exact names.
- The workflow writes `.npy` arrays; ensure the output path is intentional and has enough space.
