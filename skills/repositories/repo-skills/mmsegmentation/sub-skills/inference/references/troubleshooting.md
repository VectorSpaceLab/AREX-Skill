# Inference Troubleshooting

## Missing or wrong checkpoint

Symptoms:

- `FileNotFoundError` or checkpoint load errors.
- Warnings that no checkpoint is loaded and predictions use a randomly initialized model.
- Poor or nonsensical masks despite a valid-looking run.

Fixes:

- Confirm the checkpoint path exists and matches the config architecture/classes.
- Use local checkpoints for deterministic automation.
- Treat `checkpoint=None` as a smoke-test-only mode.
- For model aliases, remember that omitted `weights` can trigger automatic checkpoint resolution/download.

## Model alias downloads or offline failures

Symptoms:

- A run hangs or fails while resolving a model alias.
- Network/cache errors during `MMSegInferencer(model='alias')`.

Fixes:

- Ask the user before allowing network downloads.
- Prefer `MMSegInferencer(model='path/to/config.py', weights='path/to/checkpoint.pth')` for offline work.
- Use `MMSegInferencer.list_models('mmseg')` only when listing aliases is needed; it does not replace checking whether weights are already local.

## Headless display failures

Symptoms:

- GUI/display errors from matplotlib/OpenCV.
- Inference works locally but fails on CI, SSH, or containers.

Fixes:

- Set `show=False`.
- Pass `out_file` to `show_result_pyplot` for a single rendered image.
- Pass `out_dir` to `MMSegInferencer` for saved overlays and predicted masks.
- For video, use `--output-file` instead of `--show`.

## CPU fallback and SyncBN

Symptoms:

- CUDA device requested but unavailable.
- BatchNorm/SyncBN-related CPU errors.

Fixes:

- Check `torch.cuda.is_available()` before using `cuda:0`.
- Pass `device='cpu'` on CPU-only machines.
- After `init_model(..., device='cpu')`, apply `mmengine.model.revert_sync_batchnorm(model)` before inference.
- `MMSegInferencer` already reverts SyncBN when `device == 'cpu'` or CUDA is unavailable.

## Class and palette mismatch

Symptoms:

- Wrong label names or colors in overlays.
- Assertion that class and palette lengths differ.
- Warnings that checkpoint metadata is missing and Cityscapes is used by default.

Fixes:

- Prefer checkpoints that contain `dataset_meta`.
- Pass `dataset_name` for known MMSegmentation datasets.
- Pass both `classes` and `palette` for custom datasets, ensuring identical lengths.
- Do not interpret label-index masks with a different dataset palette than the training dataset.

## Missing GDAL for remote sensing

Symptoms:

- `ImportError: No module named osgeo`.
- `AttributeError` or failed assertions when constructing `RSImage`.

Fixes:

- Install GDAL/`osgeo` bindings compatible with the active Python environment before using `RSImage`.
- Verify `python -c "from osgeo import gdal; print(gdal.VersionInfo())"`.
- Use ordinary image inference for PNG/JPEG inputs when geospatial metadata and tiling are not required.
- Keep `batch_size` and `thread` conservative for large rasters.

## MMCV full package vs mmcv-lite

Symptoms:

- Missing custom ops or import failures in `mmcv`.
- Model components fail even though `mmseg` imports.

Fixes:

- MMSegmentation inference expects compatible `mmcv`, `mmengine`, `torch`, and `mmsegmentation` versions.
- Install full `mmcv` when model components or transforms need compiled ops.
- Use MIM or the official compatibility matrix for the installed PyTorch/CUDA version.

## Torch, NumPy, and OpenCV compatibility

Symptoms:

- Import failures after package upgrades.
- ABI errors, OpenCV image read/write failures, or dtype surprises.
- CUDA packages installed on a CPU-only host or mismatched with the driver.

Fixes:

- Check versions with `python -c "import mmseg, mmcv, mmengine, torch, numpy, cv2; print(mmseg.__version__, mmcv.__version__, mmengine.__version__, torch.__version__, numpy.__version__, cv2.__version__)"`.
- Keep NumPy and OpenCV versions compatible with the installed wheels.
- Use CPU-only PyTorch wheels on CPU-only machines.
- Reinstall `mmcv` after changing PyTorch/CUDA versions.

## CUDA unavailable or wrong device

Symptoms:

- `Torch not compiled with CUDA enabled`.
- `CUDA error: invalid device ordinal`.
- Slow or memory-constrained runs.

Fixes:

- Use `device='cpu'` unless `torch.cuda.is_available()` is true and the requested index exists.
- Use smaller batch sizes for `MMSegInferencer` and remote-sensing tiling.
- For TensorRT deployment, switch to deployment tooling and a CUDA-capable environment.
