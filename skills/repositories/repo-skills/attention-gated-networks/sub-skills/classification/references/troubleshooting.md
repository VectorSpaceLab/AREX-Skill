# Classification Troubleshooting

## Purpose

Read this when ultrasound classification training, testing, or attention export
fails.

## CUDA and GPU errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `AssertionError` or `CUDA is not available` | The unmodified wrappers call `.cuda()` when building models and tensors. | Use a CUDA-enabled PyTorch environment and verify with `../../scripts/check_env.py --repo-root /path/to/repo --mode cuda`. CPU-only runs need source patches that are outside this skill's default workflow. |
| `RuntimeError: CUDA out of memory` | Batch size, feature scale, or image size is too large. | Reduce `training.batchSize`, increase `model.feature_scale`, lower crop size, or use a larger GPU. |
| `no kernel image is available` | Torch CUDA wheel does not support the GPU compute capability. | Install a PyTorch wheel matching the host driver and GPU generation. |

## Dependency and import errors

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: torchsample` | The repo depends on legacy `torchsample==0.1.3`, often from the GitHub dependency link. | Install torchsample from the upstream repository and verify `import torchsample`. Modern Python may need the `collections.abc.Iterable` compatibility patch in the private environment. |
| `ImportError: cannot import name 'Iterable' from 'collections'` | Legacy torchsample on Python 3.10+. | Patch only the private environment copy of torchsample to import from `collections.abc`, or use an older Python runtime supported by the rest of the stack. |
| `ModuleNotFoundError: visdom` | Training/testing creates `Visualiser`; Visdom is imported when `visualisation.display_id > 0`. | Install `visdom`, or set `display_id` to `0` when editing the source to skip live plotting. |
| `No module named sklearn`, `cv2`, `pandas`, or `dominate` | Metric, logger, HTML, or visualization dependency missing. | Install scikit-learn, opencv-python-headless or opencv, pandas, and dominate in the same environment. |
| `AttributeError: module 'numpy' has no attribute 'float'` | Legacy code in `utils.error_logger.StatMeter` on modern NumPy. | Use a compatible NumPy or update the source to use `float`/`np.float64`. Generated helpers avoid this path when possible. |

## HDF5 and label failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `KeyError: x_train` or `p_train` | HDF5 split keys do not match the expected names. | Rename/regenerate keys or adjust `UltraSoundDataset` for the dataset. Read [data-layout](data-layout.md). |
| `assert len(self.images) == len(self.labels)` | Image and label arrays have different lengths. | Rebuild the HDF5 file so each split has matching image/label lengths. |
| Cross entropy complains about target range | Labels exceed `model.output_nc - 1` or are not integer class ids. | Inspect `p_<split>` values and align `output_nc` with `label_names`. |
| `ValueError` from sampler or `np.random.choice` | The custom stratified sampler expects enough samples per hard-coded class. | Prefer the weighted sampler branch or modify the sampler for the actual class distribution. |

## Attention overlay failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `none of the requested attention layers were found` | The model is plain Sononet rather than `sononet_grid_attention`, or layer names differ. | Use a grid-attention config or pass layer names that exist on `model.net`. |
| Overlay image is blank or constant | The input is constant, attention is saturated, or synthetic smoke data is being used. | For real interpretation, use a preprocessed 2D ultrasound image and a trained checkpoint. Synthetic mode validates wiring only. |
| Shape error from `--input-npy` | The helper expects one 2D array. | Save a single image as `(H, W)` or squeeze a one-channel array before passing it. |

## Visualization behavior

The source `Visualiser` writes logs and optionally talks to a Visdom server. If
you do not need live plots, use generated helpers for smoke checks or set the
source config's `display_id` to `0` when adapting the repository code. If HTML
output is enabled, ensure the experiment checkpoint directory is writable.
