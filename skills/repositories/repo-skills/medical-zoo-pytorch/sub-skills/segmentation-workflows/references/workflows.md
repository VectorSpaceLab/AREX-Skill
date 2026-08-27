# Workflows

This page describes the standard 3D segmentation flow: model selection, trainer wiring, checkpointing, TensorBoard logging, and patch-based inference.

## 1. Model selection flow

The factory call is the main routing step:

```python
model, optimizer = medzoo.create_model(args)
```

The factory reads the following fields from `args`:

- `model`: uppercase factory id such as `UNET3D`, `VNET`, or `RESNETMED3D`
- `inChannels`: number of input modalities/channels
- `classes`: number of segmentation classes
- `dim`: spatial crop used by models that need it
- `lr`: learning rate
- `opt`: optimizer name

The factory returns the model and a ready-to-use optimizer.

## 2. Training launcher pattern

Most bundled launchers follow the same shape:

1. Parse arguments.
2. Call reproducibility helpers.
3. Create output directories.
4. Build loaders for the selected dataset.
5. Build the model and optimizer with `create_model`.
6. Create the segmentation criterion.
7. Move the model to CUDA when requested.
8. Construct the trainer and start training.

A minimal pattern looks like this:

```python
from lib.utils.general import reproducibility, make_dirs
from lib.losses3D import DiceLoss
import lib.medzoo as medzoo
import lib.train as train

reproducibility(args, seed)
make_dirs(args.save)
model, optimizer = medzoo.create_model(args)
criterion = DiceLoss(classes=args.classes)
trainer = train.Trainer(
    args,
    model,
    criterion,
    optimizer,
    train_data_loader=train_loader,
    valid_data_loader=val_loader,
)
trainer.training()
```

### Notes on the two trainer classes

- `BaseTrainer` is the generic scaffold. It handles device selection, logger setup, monitoring, early stopping, and TensorBoard writer construction.
- `Trainer` is the concrete 3D segmentation loop used by the launchers. It prepares inputs, calls the model, expects the loss to return `(loss, per_channel_score)`, and writes checkpoints.

If you are building a custom loop, keep the same `loss, per_channel_score` contract so logging stays compatible.

## 3. Checkpointing and resume

`BaseModel` owns the checkpoint helpers:

- `save_checkpoint(directory, epoch, loss, optimizer=None, name=None)`
  - Treat `directory` as a directory, not a file path.
  - The default names come from the directory basename.
  - The method writes the main checkpoint and a `_BEST` copy when the tracked loss improves.
- `restore_checkpoint(path, optimizer=None)`
  - Restores model weights.
  - Restores optimizer state when provided.
  - Returns the checkpoint epoch.

### Practical checkpoint recipe

1. Create a dedicated checkpoint directory per experiment.
2. Call `save_checkpoint` from the trainer with the current validation loss.
3. Load the model with `restore_checkpoint` before switching to evaluation or inference.
4. If the checkpoint came from another device, load it with the same model structure and then move the model to the target device.

### Resume pattern

```python
epoch = model.restore_checkpoint(ckpt_path, optimizer=optimizer)
model.to(device)
```

## 4. TensorBoard writer usage

`lib.visual3D_temp.TensorboardWriter` expects the same argument namespace used by the training launchers.

Required fields:

- `log_dir`
- `save`
- `model`
- `dataset_name`
- `classes`

Main methods:

- `update_scores(iter, loss, channel_score, mode, writer_step)`
- `display_terminal(iter, epoch, mode='train', summary=False)`
- `write_end_of_epoch(epoch)`
- `reset(mode)`

The writer tracks train and validation loss, overall DSC, and per-class DSC.

### Writer contract

- `channel_score` must be indexable and must match the dataset label count.
- `args.dataset_name` must map to one of the known 3D segmentation label sets.
- `args.save` is used for the CSV files.
- `args.log_dir` is used for the SummaryWriter path.

## 5. Inference and visualization

There are two families of helpers:

### Model-level inference

`BaseModel.inference(input_tensor)`:

- switches the model to eval mode
- runs a no-grad forward pass
- unwraps tuple outputs to the first tensor
- returns a CPU tensor

Use it when you need a quick inference step and do not want to manage device transfers manually.

### Volume reconstruction and visualization

`lib.visual3D_temp.viz` provides the non-overlap inference path:

- `visualize_3D_no_overlap_new(args, full_volume, affine, model, epoch, dim)`
- `create_3d_subvol(full_volume, dim)`
- `save_3d_vol(predictions, affine, save_path)`
- `non_overlap_padding(args, full_volume, model, criterion, kernel_dim=(32, 32, 32))`

Important behavior:

- `visualize_3D_no_overlap_new` expects a stacked volume tensor and saves both a 2D view and a NIfTI prediction.
- `non_overlap_padding` expects the input/target stack to end with the target channel and currently forces `.cuda()` in the loss call.
- `find_crop_dims` only behaves cleanly when the volume dimensions tile exactly; pad or crop to compatible sizes first.
- `save_3d_vol` writes `.nii.gz` output with the affine that was passed in.

Treat the legacy inference demo as reference-only because it assumes both a checkpoint and a GPU-style path through the helper.

## 6. Example launcher pattern

The bundled launchers differ mostly by dataset name, crop size, channel count, class count, and whether augmentation is enabled.

Typical knobs:

- `batchSz`
- `dataset_name`
- `dim`
- `nEpochs`
- `classes`
- `samples_train`
- `samples_val`
- `inChannels`
- `inModalities`
- `split`
- `lr`
- `cuda`
- `model`
- `opt`
- `log_dir`
- `augmentation`
- `normalization`

Use the same launcher structure for a new dataset: build `args`, reproduce the seed, create the directories, call the loader factory, build the model, and hand control to `Trainer`.
