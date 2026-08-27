# Segmentation API Reference

## Purpose

Read this when a task needs exact model names, wrapper behavior, dataset
classes, metric functions, or feature-map hooks for Attention-Gated Networks
segmentation workflows.

## Entry points

| Object | Signature or command | Use |
| --- | --- | --- |
| `models.get_model(json_opts)` | `(json_opts)` | Builds a `FeedForwardSegmentation` wrapper when `json_opts.type='seg'`. |
| `dataio.loader.get_dataset(name)` | `(name)` | Returns dataset classes for `ukbb_sax`, `acdc_sax`, `rvsc_sax`, `hms_sax`, `test_sax`, and `us`. Use `acdc_sax` or `ukbb_sax` for 3D segmentation. |
| `dataio.transformation.get_dataset_transformation(name, opts=None)` | `(name, opts=None)` | Builds transform dictionaries. `acdc_sax` and `ukbb_sax` return `train` and `valid`; `test_sax` returns `test`. |
| `scripts/run_segmentation.py` | `--config CONFIG [--repo-root PATH] [--disable-visdom]` | Skill-owned replacement; relative configs require `--repo-root` and config-relative data paths use the config parent. |
| `scripts/validate_and_export_maps.py` | `--config CONFIG --output-dir DIR --mode validate|maps|both [--checkpoint PATH]` | Skill-owned validation and feature/attention map export helper. |
| Source root entry points | `train_segmentation.py -c CONFIG`; `validation.py -c CONFIG` | Evidence for behavior; use bundled replacements unless deliberately working inside a maintainer checkout. |

## Segmentation wrapper

`FeedForwardSegmentation` is defined in `models/feedforward_seg_model.py`.

- `initialize(self, opts, **kwargs)` builds the selected network with
  `get_network`, moves it to CUDA when `self.use_cuda` is true, optionally loads
  a checkpoint, and creates the loss/optimizer when `opts.isTrain` is true.
- `set_input(self, *inputs)` expects image tensors first and label tensors
  second. If `tensor_dim='2D'` and a 5D tensor is supplied, it folds the slice
  dimension into the batch. For segmentation, input and target tensor sizes must
  match.
- `forward(self, split)` returns raw class logits during training and sets
  `pred_seg` during test/validation by applying softmax then argmax.
- `optimize_parameters(self)` runs one forward/backward/optimizer step.
- `validate(self)` runs the inference path and computes the configured loss.
- `get_segmentation_stats(self)` reports overall accuracy, mean IoU, and a dice
  score for each class.
- `get_feature_maps(self, layer_name, upscale)` uses a hook-based extractor on
  `model.net` and is the safest API to reuse for attention-map exports.

## Network names

The registry in `models/networks/__init__.py` maps `model_type` and `tensor_dim`
to concrete networks:

| `model_type` | `tensor_dim` | Class/function | Notes |
| --- | --- | --- | --- |
| `unet` | `2D`, `3D` | `unet_2D`, `unet_3D` | Baseline U-Net variants. |
| `unet_nonlocal` | `2D`, `3D` | `unet_nonlocal_2D`, `unet_nonlocal_3D` | U-Net with non-local blocks. |
| `unet_grid_gating` | `3D` | `unet_grid_attention_3D` | 3D grid-attention U-Net. |
| `unet_ct_dsv` | `3D` | `unet_CT_dsv_3D` | CT-oriented 3D U-Net with deep supervision outputs. |
| `unet_ct_single_att_dsv` | `3D` | `unet_CT_single_att_dsv_3D` | Single attention block plus deep supervision. |
| `unet_ct_multi_att_dsv` | `3D` | `unet_CT_multi_att_dsv_3D` | Multiple attention gates plus deep supervision. |

Verified signatures include:

```text
unet_CT_dsv_3D(feature_scale=4, n_classes=21, is_deconv=True, in_channels=3, is_batchnorm=True)
unet_CT_multi_att_dsv_3D(feature_scale=4, n_classes=21, is_deconv=True, in_channels=3, nonlocal_mode='concatenation', attention_dsample=(2, 2, 2), is_batchnorm=True)
GridAttentionBlock3D_TORR(in_channels, gating_channels, inter_channels=None, mode='concatenation', sub_sample_factor=(1, 1, 1), bn_layer=True)
NONLocalBlock3D(in_channels, inter_channels=None, mode='embedded_gaussian', sub_sample_factor=2, bn_layer=True)
```

## Dataset and NIfTI APIs

| Class/function | Signature | Notes |
| --- | --- | --- |
| `CMR3DDataset` | `(root_dir, split, transform=None, preload_data=False)` | Reads `root_dir/<split>/image/*.nii.gz` and `root_dir/<split>/label/*.nii.gz`. |
| `UKBBDataset` | `(root_dir, split, transform=None, preload_data=False)` | Same folder contract, then samples one random slice from each 3D volume. |
| `TestDataset` | `(root_dir, transform)` | Reads `root_dir/image/*.nii.gz`; optional labels from `root_dir/label/*.nii.gz`. |
| `load_nifti_img` | `(filepath, dtype)` | Loads a NIfTI file with nibabel, squeezes singleton dimensions, and returns `(array, meta)`. |
| `write_nifti_img` | `(input_nii_array, meta, savedir)` | Writes a NIfTI using metadata captured by `load_nifti_img`. |
| `check_exceptions` | `(image, label=None)` | Raises on image/label shape mismatch or blank images. |

## Losses and metrics

`models.utils.get_criterion(opts)` selects:

- `cross_entropy_2D` or `cross_entropy_3D` when `criterion='cross_entropy'` and
  `opts.type='seg'`;
- `SoftDiceLoss(opts.output_nc)` when `criterion='dice_loss'`;
- `CustomSoftDiceLoss(opts.output_nc, class_ids=[0, 2])` when
  `criterion='dice_loss_pancreas_only'`.

Important metrics in `utils.metrics`:

| Function | Signature | Notes |
| --- | --- | --- |
| `segmentation_scores` | `(label_trues, label_preds, n_class)` | Overall accuracy, mean accuracy, frequency-weighted accuracy, and mean IoU. |
| `dice_score_list` | `(label_gt, label_pred, n_class)` | Mean dice per class across a batch/list. |
| `dice_score` | `(label_gt, label_pred, n_class)` | Dice per class for one volume. |
| `precision_and_recall` | `(label_gt, label_pred, n_class)` | Per-class precision and recall from scikit-learn. |
| `distance_metric` | `(seg_A, seg_B, dx, k)` | Mean and Hausdorff contour distance for one class across slices; returns `None` when no valid contour pairs exist. |

## Feature and attention hooks

`HookBasedFeatureExtractor(submodule, layername, upscale=False)` registers hooks
on `submodule._modules[layername]`. For multi-attention U-Net configs, useful
layers include `attentionblock2`, `attentionblock3`, `attentionblock4`, and
`center`. The bundled segmentation helper exports these layers without relying
on private output paths.
