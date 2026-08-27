# Install and Compatibility

Read this before debugging MMSegmentation import errors, backend failures, or environment issues.

## Baseline Requirements

MMSegmentation 1.x is an OpenMMLab package built around these layers:

- `mmsegmentation` imports as `mmseg`.
- `mmcv` must satisfy `>=2.0.0rc4,<2.2.0` for this source snapshot.
- `mmengine` must satisfy `>=0.5.0,<1.0.0` for this source snapshot.
- `torch` is required for public API modules such as `mmseg.apis`, `mmseg.datasets`, `mmseg.models`, and `mmseg.evaluation`.
- Runtime requirements include `matplotlib`, `numpy`, `packaging`, `prettytable`, and `scipy`; practical OpenMMLab use also requires the matching `mmcv`/`mmengine` stack.

Use this import check first:

```bash
python -c "import mmseg, mmcv, mmengine, torch; print(mmseg.__version__, mmcv.__version__, mmengine.__version__, torch.__version__)"
```

## Recommended Install Shape

For users installing normally:

```bash
pip install -U openmim
mim install mmengine
mim install "mmcv>=2.0.0,<2.2.0"
pip install "mmsegmentation>=1.0.0"
```

For source development, install the local project in editable mode after installing compatible OpenMMLab foundations:

```bash
pip install -U openmim
mim install mmengine
mim install "mmcv>=2.0.0,<2.2.0"
pip install -e .
```

Pick a PyTorch build first, then install an MMCV wheel compatible with that PyTorch/CUDA or CPU runtime. Do not mix arbitrary `torch` and `mmcv` versions.

## CPU, CUDA, and Optional Backends

- CPU is enough for config inspection, registry checks, signature inspection, and many small tests.
- CUDA is needed for realistic training/inference speed and some CUDA/C++ ops; install a CUDA-enabled PyTorch build and matching MMCV wheel for the host driver.
- `nvidia-smi` showing a CUDA version means the driver can support up to that runtime. It does not mean a toolkit or compatible wheel is installed.
- NPU or other vendor accelerators need vendor-compatible PyTorch/MMCV builds. Do not apply CUDA fixes to NPU failures.
- `mmcv-lite` may import top-level packages but lacks compiled ops; use full `mmcv` when models or APIs import `mmcv._ext` or `mmcv.ops`.

## NumPy and OpenCV Compatibility

Older PyTorch/MMCV wheels may warn or fail with `numpy>=2` because extensions were compiled against NumPy 1.x. If you see `_ARRAY_API not found` or a warning that modules compiled using NumPy 1.x cannot run in NumPy 2.x:

1. Pin `numpy<2`.
2. Pin OpenCV to a version compatible with NumPy 1.x, for example `opencv-python<4.12`.
3. Run `python -m pip check`.
4. Re-run the MMSegmentation import check.

## Optional Dependencies

Install optional packages only for the selected workflow:

- `ftfy` and `regex` support tokenizer/open-vocabulary paths imported by some MMSegmentation utilities and multimodal models.
- `GDAL`/`osgeo` is required for remote-sensing `RSImage` geospatial raster IO.
- Dataset converters can require packages such as Cityscapes scripts or dataset-specific dependencies.
- Open-vocabulary, depth, diffusion, CLIP, TorchServe, deployment, and project-specific workflows can require substantial optional stacks.

Do not install broad optional groups just to inspect configs or public APIs. Add optional dependencies when a user task actually needs that workflow.

## Quick Compatibility Script

Run the bundled helper from the skill root or pass no special paths:

```bash
python scripts/check_mmseg_env.py
```

Use `--require-cuda` only when the user explicitly needs CUDA availability:

```bash
python scripts/check_mmseg_env.py --require-cuda
```

The script checks imports, versions, CUDA visibility, and common dependency traps; it does not download weights or run training.
