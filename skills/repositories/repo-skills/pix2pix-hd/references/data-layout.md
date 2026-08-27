# pix2pixHD Data Layout

## Purpose

Read this when you need the folder conventions that drive training, inference, and feature workflows.

## Dataset roots

### Cityscapes-style paired data
The bundled sample fixture lives under `datasets/cityscapes/` and follows the standard phase-based layout:

- `train_label/`, `train_inst/`, `train_img/`
- `test_label/`, `test_inst/`
- optional `train_feat/` and `test_feat/` when `--load_features` is used

The loader expects matching basenames across the paired folders. The setup sub-skill's layout checker validates that alignment.

### Label-free translation
When `label_nc=0`, `AlignedDataset` switches to the paired `phase_A` and `phase_B` naming convention instead of the Cityscapes-style label / instance / image folders.

## Common outputs

| Output | Default location | Used by |
| --- | --- | --- |
| Checkpoints | `checkpoints/<name>/` | Training, inference preflight, feature workflows |
| Generator checkpoint | `checkpoints/<name>/<epoch>_net_G.pth` | Inference |
| Encoder checkpoint | `checkpoints/<name>/<epoch>_net_E.pth` | Feature workflows and encoded-image inference |
| Feature cache | `checkpoints/<name>/features.npy` and `checkpoints/<name>/features_clustered_*.npy` | Instance-feature workflows |
| HTML results | `results/<name>/<phase>_<epoch>/index.html` | Inference |
| Rendered images | `results/<name>/<phase>_<epoch>/images/` | Inference |
| Training HTML | `checkpoints/<name>/web/index.html` | Training |
| Training logs | `checkpoints/<name>/loss_log.txt` and `checkpoints/<name>/logs/` | Training |

## Folder rules that matter

- Keep the dataset root on the parent of the phase folders, not on a leaf folder.
- Keep paired files aligned by sorted basename.
- Keep feature caches in the same experiment directory as the checkpoints that generated them.
- Keep `cluster_path` relative to `checkpoints/<name>/`, because the inference helpers resolve it there.

## Feature-folder reminder

- `load_features` means the dataset uses `phase_feat/` folders created by `precompute_feature_maps.py`.
- `instance_feat` / `label_feat` means the model uses feature conditioning; it does not by itself create `phase_feat/`.

## Quick sanity checks

- `train_label` should pair with `train_inst` and `train_img`.
- `test_label` should pair with `test_inst` for the bundled inference smoke; `test_img` is only needed when encoded-image inference is requested.
- `batchSize=1` is the safest choice for the bundled sample fixture because `AlignedDataset.__len__` floors to a batch multiple.
