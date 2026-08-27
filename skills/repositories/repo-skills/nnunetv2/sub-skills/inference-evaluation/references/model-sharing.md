# Model Sharing, Import, Export, and Downloads

## Export a Trained Model

Export a trained model to a portable zip:

```bash
nnUNetv2_export_model_to_zip \
  -d DATASET001_Example \
  -o model.zip \
  -c 3d_fullres \
  -tr nnUNetTrainer \
  -p nnUNetPlans \
  -f 0 1 2 3 4 \
  -chk checkpoint_final.pth
```

Useful options:

- `-c`: one or more configurations to export. Defaults include the common nnU-Net configurations.
- `-tr`: trainer class name; default `nnUNetTrainer`.
- `-p`: plans identifier; default `nnUNetPlans`.
- `-f`: folds to export; default `0 1 2 3 4`.
- `-chk`: one or more checkpoint names; default `checkpoint_final.pth`.
- `--not_strict`: allow missing folds and/or configurations.
- `--exp_cv_preds`: export cross-validation predictions as well.

Prefer strict export for reproducible model sharing. Use `--not_strict` only when intentionally packaging a partial model, and document which folds/configurations are present.

## Install an Exported Model

Install a model zip into the active nnU-Net environment:

```bash
nnUNetv2_install_pretrained_model_from_zip model.zip
```

After installation, predict through the normal results-layout route if the model lands under `nnUNet_results`, or use `nnUNetv2_predict_from_modelfolder` if you keep a copied model folder separate.

## Download by URL

Download and install from a URL:

```bash
nnUNetv2_download_pretrained_model_by_url URL
```

The downloader warns that model weights are subject to the dataset license used for training. Confirm license compatibility before commercial or redistributed use.

## Version Compatibility

nnU-Net v1 pretrained weights are not compatible with nnU-Net v2. Do not attempt to install v1 model weights into v2; retrain in v2 or run inference with the old v1 stack.

## Custom Trainer Models

A checkpoint records `checkpoint["trainer_name"]`. At inference time, nnU-Net must import a class with that name to rebuild the architecture. Resolution order:

1. Built-in trainers under `nnunetv2.training.nnUNetTrainer`.
2. External trainer directories listed in `nnUNet_extTrainer`, if set.

If the trainer class cannot be found, prediction and continued training fail even if the checkpoint file exists.

### Option 1: Rename to a Built-In Trainer

Rewrite the checkpoint trainer name to a built-in trainer only when all of these are true:

- The custom trainer did not change `build_network_architecture` or any behavior that affects the network structure.
- You manually verified that predictions match the original custom trainer.
- You accept that provenance is less transparent because the checkpoint no longer points to the original class.

This is the lowest-friction distribution path when it is valid, but it is unsafe for architecture-changing trainers.

### Option 2: Ship Trainer Code and Use `nnUNet_extTrainer`

Distribute trainer files separately and tell users to expose the parent directory:

```bash
export nnUNet_extTrainer="/path/to/custom_trainers"
```

Multiple directories use the OS path separator, for example `:` on Linux/macOS or `;` on Windows. The directory should be a parent from which the trainer module and its imports are resolvable.

This is the recommended transparent option when the trainer changes architecture or training behavior.

### Option 3: Editable Source Copy

Users can install nnU-Net in editable mode and copy trainer files under `nnunetv2/training/nnUNetTrainer/`, but this is brittle across reinstalls and versions. Prefer `nnUNet_extTrainer` unless the user intentionally needs a development checkout.

### Option 4: Distribute a Fork

A fork can bundle the trainer permanently and pin compatibility with the checkpoint. Use this when users must train or modify models in the same custom environment, or when release requirements mandate source distribution.

## Sharing Checklist

Include the following with every shared model:

- nnU-Net v2 version or install instructions.
- Dataset id/name and modality/channel order expected by `dataset.json`.
- Configurations, folds, checkpoints, trainer, and plans identifier exported.
- Whether prediction should use `nnUNetv2_predict` or `nnUNetv2_predict_from_modelfolder`.
- Whether the recipient must set `nnUNet_extTrainer` or install a fork.
- License and usage restrictions for training data and weights.
- Recommended postprocessing file and inference commands when available.
