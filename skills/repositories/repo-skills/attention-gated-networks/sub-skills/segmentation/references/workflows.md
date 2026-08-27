# Segmentation Workflows

## Purpose

Read this for Attention-Gated Networks medical image segmentation training,
validation, and attention/feature-map export.

## Install and smoke check

After installing the repository with a CUDA-enabled PyTorch stack, run:

```bash
python ../../scripts/check_env.py --repo-root /path/to/Attention-Gated-Networks --mode segmentation
```

The expected signal is a 3D model construction and an output line like:

```text
segmentation-output=(1, 4, 16, 16, 16)
check-env-ok
```

Synthetic smoke checks do not validate a real dataset or checkpoint, but they
catch missing CUDA, torchsample, model registry, and transform dependencies.

## Train a 3D segmentation model

1. Arrange paired image/label NIfTI files as described in
   [data-layout.md](data-layout.md).
2. Copy a config matching the intended network:
   - `config_unet_ct_dsv.json` for `unet_ct_dsv`;
   - `config_unet_ct_multi_att_dsv.json` for `unet_ct_multi_att_dsv`.
3. Replace `data_path.acdc_sax` with the current dataset root.
4. Confirm `augmentation.acdc_sax.scale_size` and `patch_size` fit the real
   data and GPU memory.
5. Keep `model.type='seg'`, `tensor_dim='3D'`, `input_nc=1`, and `gpu_ids=[0]`
   for the unmodified source path.
6. Run the bundled replacement script:

```bash
python scripts/run_segmentation.py \
  --repo-root /path/to/Attention-Gated-Networks \
  --config path/to/config.json
```

The training loop builds `train`, `validation`, and `test` datasets, optimizes
one model step per batch, writes visualizations/logs through `Visualiser`, saves
checkpoints at `training.save_epoch_freq`, and updates the learning rate.

## Validate a checkpoint and write NIfTI outputs

The source validation behavior builds the model, loads the dataset, predicts a
segmentation map, computes dice/precision/recall/distance metrics, writes
`*_img.nii.gz`, `*_lbl.nii.gz`, `*_pred.nii.gz`, and writes a `stats.csv` file.
Use the bundled helper for validation-style checks and parameterized outputs:

```bash
python scripts/validate_and_export_maps.py \
  --repo-root /path/to/Attention-Gated-Networks \
  --config configs/config_unet_ct_dsv.json \
  --output-dir /tmp/ag-net-segmentation \
  --mode validate
```

The helper writes synthetic input, label, prediction, and `metrics.json` under
the requested output directory.

## Export feature or attention maps

The source `visualise_att_maps_epoch.py` and `visualise_fmaps.py` hard-code
private config paths, subject IDs, epochs, and output folders. Use the generated
helper instead:

```bash
python scripts/validate_and_export_maps.py \
  --repo-root /path/to/Attention-Gated-Networks \
  --config configs/config_unet_ct_multi_att_dsv.json \
  --output-dir /tmp/ag-net-maps \
  --mode maps \
  --layers attentionblock2 attentionblock3 attentionblock4 center
```

For a real input volume, save one 3D volume as a NumPy array and pass
`--input-npy volume.npy`. To inspect a trained model, also pass
`--checkpoint path/to/checkpoint.pth`. The helper writes NIfTI volumes and
middle-slice preview PNGs.

## Model selection notes

| Goal | Config/model fields |
| --- | --- |
| Baseline 2D or 3D U-Net | `model_type='unet'`, choose `tensor_dim` |
| Non-local U-Net | `model_type='unet_nonlocal'`, set `nonlocal_mode` |
| CT deep-supervision U-Net | `model_type='unet_ct_dsv'`, `tensor_dim='3D'`, `criterion='dice_loss'` |
| CT multi-attention U-Net | `model_type='unet_ct_multi_att_dsv'`, set `nonlocal_mode` and `attention_dsample` |

Deep-supervision CT models concatenate four upsampled prediction maps before the
final convolution. Keep input dimensions divisible by the downsampling stack to
avoid interpolation or size-mismatch surprises.

## Pre-run checklist

- `python scripts/run_segmentation.py --help` and `python scripts/validate_and_export_maps.py --help` work.
- The root segmentation smoke succeeds on CUDA.
- NIfTI image and label folder counts match by split.
- The config's `visualisation.display_id` is `0` or a Visdom server is running.
- The checkpoint directory is writable and has enough disk space.
- GPU memory is adequate for `batchSize`, `patch_size`, and `feature_scale`.
