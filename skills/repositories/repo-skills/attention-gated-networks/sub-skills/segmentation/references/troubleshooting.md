# Segmentation Troubleshooting

## Purpose

Read this when 3D segmentation training, validation, NIfTI export, or attention
map extraction fails.

## CUDA and memory failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `CUDA is not available`, `AssertionError`, or `.cuda()` failure | The unmodified wrappers move networks and tensors to CUDA. | Use a CUDA-enabled PyTorch environment and verify with `../../scripts/check_env.py --repo-root /path/to/repo --mode cuda`. CPU-only use requires source edits. |
| `RuntimeError: CUDA out of memory` | 3D patch size, batch size, deep supervision, or attention gates exceed GPU memory. | Reduce `training.batchSize`, reduce `augmentation.*.patch_size`, increase `model.feature_scale`, or start from `unet_ct_dsv` before `unet_ct_multi_att_dsv`. |
| Size mismatch inside upsampling/concatenation | Input dimensions are not compatible with the downsampling and deep-supervision stack. | Use dimensions divisible by 16 for CT deep-supervision models, or pad with the `test_sax` transform / `division_factor`. |

## Data and NIfTI failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `FileNotFoundError` under `train/image` or `validation/label` | Dataset root or split names do not match the source loader contract. | Read [data-layout.md](data-layout.md) and align folder names with the script. |
| `image and label sizes do not match` | Paired NIfTI image and label shapes differ after squeezing. | Resample/crop labels to image geometry before training. |
| `blank image exception` | An input volume has near-zero max intensity. | Remove blank files or fix preprocessing before starting the run. |
| NIfTI outputs have unexpected orientation | The source validation code transposes arrays and sets a fixed direction in SimpleITK. | Inspect a tiny exported case before launching a full validation sweep; adapt orientation handling for the dataset if needed. |

## Dependency failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: SimpleITK` | `validation.py` uses SimpleITK for NIfTI export. | Install SimpleITK or use the generated helper, which writes NIfTI with nibabel for smoke validation. |
| `ModuleNotFoundError: torchsample` | Transform builders import `torchsample.transforms`. | Install the legacy torchsample package and apply the `collections.abc.Iterable` compatibility patch if needed. |
| `ModuleNotFoundError: cv2` | `utils.metrics.distance_metric` imports OpenCV. | Install OpenCV or skip distance metrics for smoke-only runs. |
| `AttributeError: module 'numpy' has no attribute 'float'` | Legacy `StatLogger` uses `np.float`. | Use a compatible NumPy or update the source to use `float`/`np.float64`. Generated helpers avoid `StatLogger`. |

## Metrics and label errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Dice/IoU are `nan` or unstable | A class is absent from both prediction and label in a tiny or imbalanced volume. | Treat this as a fixture issue for smoke tests; use representative labels for real validation. |
| Cross entropy or dice loss target error | Label values are outside `[0, output_nc-1]` or have wrong dtype/shape. | Inspect label volumes, remap class ids, and confirm `model.output_nc`. |
| `distance_metric` returns `None` | The selected class has no contour in one or both segmentations. | This is expected for sparse volumes; choose a class with present contours or skip contour distance for that case. |

## Attention and feature-map export failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `none of the requested layers were found` | The config builds a model without those layer names. | For `unet_ct_multi_att_dsv`, use `attentionblock2`, `attentionblock3`, `attentionblock4`, or `center`. For other models, inspect `model.net._modules`. |
| Hook output has unsupported shape | The layer returns a nested tuple/list or channel dimensions unlike attention maps. | Use the generated helper's layer defaults first, then inspect the hook output shape before exporting custom layers. |
| Map previews look noisy in synthetic mode | Synthetic inputs validate wiring only. | For interpretation, use a real preprocessed 3D volume and a trained checkpoint. |

## CRF post-processing

The source repository contains a CRF post-processing script, but it hard-codes
private dataset/output paths and depends on `pydensecrf`. It is intentionally
not bundled as a runnable helper. If a task requires CRF post-processing,
extract only the `apply_crf(input_image, input_prob, theta_a, theta_b, theta_r,
mu1, mu2)` logic into a new project-local script, install `pydensecrf`, and add
explicit arguments for input/output paths.
