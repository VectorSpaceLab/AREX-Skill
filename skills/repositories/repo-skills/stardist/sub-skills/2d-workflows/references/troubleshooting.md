# 2D troubleshooting and recovery

Diagnose in order: environment → model artifact → image contract →
normalization → config/parameters → memory → result quality. Preserve the
exception and the original run contract; do not silently change axes, channels,
weights, or thresholds.

## Environment and import

| Symptom | Cause/check | Recovery |
|---|---|---|
| `import stardist` fails | TensorFlow/CSBDeep missing or incompatible | Verify the active interpreter, TensorFlow 2.x, CSBDeep, NumPy/Keras, and StarDist versions; install a compatible StarDist wheel or rebuild in a clean environment. |
| Missing compiled extension, binary symbol, or ABI error | No compatible wheel or broken C/C++ build | Prefer a matching CPU wheel. If building, use a supported C++ compiler and rebuild consistently. On macOS resolve OpenMP compiler/runtime symbols. `gputools` is not the CPU-extension fix. |
| Channels-first unsupported | Keras data format is not channels-last | Set the environment to `channels_last` and restart; do not transpose only one input. |
| OpenCL/CUDA error | Optional backend selected without verified driver/package | Set `use_gpu=False` for the CPU baseline. OpenCL/gputools data generation and CUDA TensorFlow are separate optional paths; verify before retrying. |
| Unexpected GPU memory use in CPU plan | TensorFlow sees an inherited GPU policy | Apply the intended device visibility/CPU policy in a fresh process and record it. |

The required baseline is CPU TensorFlow 2.x plus compiled CPU extensions.
Network model downloads, OpenCL, CUDA, BioImage.IO, QuPath, and Zarr are
optional and must be explicit blockers or dependencies.

## Model source and artifact

| Symptom | Cause/check | Recovery |
|---|---|---|
| Unknown `from_pretrained` name | Key is not registered | Call `StarDist2D.from_pretrained()` to list names; use `2D_versatile_fluo`, `2D_versatile_he`, `2D_paper_dsb2018`, or `2D_demo` in this baseline. |
| Pretrained download fails/hangs | Network, remote archive, cache, permissions, or checksum | Report the optional network/model-data block and retry after repair. Never substitute a new untrained model. |
| Local model cannot load | Wrong `basedir/name`, incomplete copy, incompatible model version | Check the actual model directory for persisted config and weights, then reload with the exact root/name. |
| Local model loads but outputs are wrong | Config/modalities differ from assumptions | Print `model.config` and compare axes, `n_channel_in`, `n_rays`, `grid`, `n_classes`, modality, and normalization before tuning. |

Successful `StarDist2D(Config2D(...))` construction proves only that an
untrained graph was built; it is not successful weight loading.

## Axes, shape, dtype, normalization

| Symptom | Cause/check | Recovery |
|---|---|---|
| Axes length/normalization error | `axes` rank/order is wrong or has invalid/duplicate symbols | Use `YX` for rank 2 and `YXC` for rank 3 channel-last input; pass axes explicitly. |
| `ZYX`/`ZYXC` rejected | Volume/time axis was given to a 2D model | Select and document a 2D plane, or use the 3D workflow. Never relabel Z/T as Y. |
| Channel mismatch | `shape[-1]` differs from `config.n_channel_in` | Use a matching model and `YXC`, or consistently use rank-2 `YX` only for a one-channel model. Do not average/duplicate channels without recording it. |
| Training image/mask mismatch | Label has C, spatial shapes differ, or list lengths differ | Make each label integer `YX`, pair exact `(Y,X)` shapes, and validate all entries before `train`. |
| Star-distance/data generation failure | Floating/malformed labels, too-small images, or invalid negatives | Preserve integer instance ids; use negatives only for intentional ignored loss regions; adjust patch/image sizes with grid constraints. |
| Empty/nonsensical predictions | Unnormalized integer input, modality mismatch, or untrained/wrong weights | Normalize once, inspect finite/range statistics, verify weights/config, and run a known fixture before changing thresholds. |
| Warning about non-float prediction input | `normalizer=None` received non-float/un-normalized data | Normalize explicitly or provide a `Normalizer` implementing `before(x,axes)`. Record percentile/statistics and channel policy. |

## Grid and training

| Symptom | Cause/check | Recovery |
|---|---|---|
| Unsupported backbone | `Config2D` only implements `unet` | Use `backbone='unet'` or treat a different backbone as an unsupported source change. |
| Invalid grid | Wrong rank/nonpositive/non-power-of-two spatial factors | Use a two-entry grid such as `(1,1)` or `(2,2)` and inspect the exact error. |
| Patch not divisible | U-Net pooling depth and grid impose an effective divisor | Choose compatible `train_patch_size` or reduce grid/depth. With completion apply divisibility to `train_patch_size-2*train_completion_crop`. |
| Shape completion crop rejected | Crop not grid-divisible or remaining patch too small | Choose grid-compatible `train_completion_crop`, keep the remainder positive and divisible, and base crop on object size. |
| Boundary objects truncated | Model trained with default `train_shape_completion=False` or crop too small | Inspect persisted config and retrain with completion enabled and justified crop; this is not an inference switch. |
| Loss/class-weight length error | Weights do not match output heads | Ordinary: two loss and two class weights. K-class: three loss and K+1 class weights. |
| No foreground patches | High foreground sampling but masks have no positive ids | Check annotations. The generator may fall back to general patches, but the dataset may not support the task. |
| Cannot reload after training | Unwritable/incomplete model directory or changed name/root | Let the side-effectful run finish, verify config/checkpoints and permissions, and reload with the exact root/name. |

## Thresholds and prediction options

| Symptom | Cause/check | Recovery |
|---|---|---|
| Too many false positives | Low probability threshold, normalization/domain mismatch, or weak model | Validate model/preprocessing first, then tune on held-out labels or raise `prob_thresh`; record the value. |
| Merged/missing neighbors | NMS threshold, coarse rays/grid, or poor object representation | Tune `nms_thresh` with `optimize_thresholds` and inspect polygons; threshold tuning is not a model fix. |
| `thresholds.json` ignored | Missing/invalid file, wrong model directory, or read-only load | Print `model.thresholds`, inspect loaded directory, and pass explicit thresholds. Valid values are between 0 and 1. |
| `scale` error | Wrong iterable length or nonpositive values | Use scalar or `(sY,sX)` for YX and scalar or `(sY,sX,1)` for YXC; all values positive and non-spatial values one. |
| `overlap_label` `NotImplementedError` | 2D does not implement it in this revision | Leave it `None`; apply any reviewed downstream overlap policy separately. |
| `return_predict` OOM | It forces `sparse=False` and returns dense maps | Omit it for ordinary segmentation; use `model.predict` on a small crop for map diagnostics. |

## Tiling, blocks, and OOM

| Symptom | Cause/check | Recovery |
|---|---|---|
| `n_tiles` length error | Tuple rank does not match input rank | Use `(ny,nx)` for YX and `(ny,nx,1)` for YXC. |
| Tile-axis error | A channel entry is greater than one | Set C to one; only spatial axes may be tiled. |
| Ordinary prediction OOM | Forward pass or assembled maps/candidates too large | Increase spatial `n_tiles`, retain sparse mode, disable `return_predict`, reduce concurrency/crop, then use `predict_instances_big` if global NMS remains too large. |
| Tiled seams/difference | Tiles too small for receptive field/context or parameters changed | Compare a small untiled crop, increase tile size/context, and keep normalizer/scale/thresholds fixed. |
| Big block assertion/value error | Wrong tuple rank, grid incompatibility, or `min_overlap+2*context >= block_size` | Provide one value per axis, make values grid-compatible, keep C full with zero overlap/context, and recheck the inequality. |
| Big object-size `RuntimeError` | Object is not smaller than `min_overlap` or spans responsibility region | Increase `min_overlap` and usually `block_size`, while preserving the block inequality. Estimate extents from representative labels. |
| Big output shape/allocation error | `labels_out` includes C or has wrong shape/dtype | Output shape is input shape with C removed; allocate an integer writable store of exactly that shape. Use `labels_out=False` only when labels are not needed. |
| RAM remains high with labels suppressed | Polygon details are still accumulated/concatenated | Reduce scope, process results incrementally where possible, or change the downstream detail contract. |
| Process killed without exception | OS-level memory pressure/TensorFlow allocator | Reduce concurrent jobs, increase spatial tiling, keep sparse mode, avoid dense return, then block-process. Do not change thresholds to hide OOM. |

## Export boundary and unresolved failures

`export_TF` is TensorFlow SavedModel export, not BioImage.IO. With grid greater
than one, `upsample_grid=True` produces same-size outputs; multiclass export
warns and drops classification output; `basedir=None` requires explicit
`fname`. Console, Fiji/ROI, QuPath, and BioImage.IO belong to
[deployment-integration](../../deployment-integration/SKILL.md).

When unresolved, hand off the exact model source/config, input shape/axes/dtype,
normalization, parameters, exception, recovery attempts, and whether the block
is CPU-required or optional-backend-specific. Import success alone is not
workflow verification.
