# Install and Setup Reference

## When to Read

Read this before running any SiamMask workflow, or whenever imports, CUDA checks, OpenCV GUI behavior, or Cython extension builds fail.

## Runtime Model

SiamMask is a checkout-style research repository, not an installable distribution. The code expects:

- The checkout root on `PYTHONPATH` so `utils`, `models`, `datasets`, and `tools` import correctly.
- The selected experiment directory on `PYTHONPATH` or as the current working directory so `custom.py`, `resnet.py`, and experiment-local config files resolve.
- Local Cython extensions built in place for VOT overlap and pycocotools functionality.

Bundled helpers set `PYTHONPATH` for native script launches. If you run the repo manually, add the checkout root yourself before invoking Python entry points.

## Environment Choices

The official README states the original tested stack was Ubuntu 16.04, Python 3.6, PyTorch 0.4.1, CUDA 9.2, and RTX 2080 GPUs. Those exact pins are legacy and often unavailable on modern Python/GPU hosts.

For inspection and modern operation, use the smallest environment that covers the workflow:

- Base imports and CPU-capable tracking/evaluation: PyTorch, NumPy `<1.24`, OpenCV, Pillow, tqdm, colorama, numba, scipy, h5py, requests, fire, tensorboardX, Cython, and pycocotools.
- Training or VOS hyperparameter tuning: the same base environment plus a CUDA-capable PyTorch build that matches the host driver.
- Interactive demo: an OpenCV build with GUI support and a display/session capable of ROI selection.

Why NumPy `<1.24`: the legacy code uses aliases such as `np.float`, `np.int`, and `np.int0`; NumPy 1.24+ removes some aliases and can break unpatched workflows.

## Build Checkout-Local Extensions

Run the bundled extension builder with the Python that has Cython and NumPy installed:

```bash
bash scripts/build_extensions.sh --repo-root <siammask-checkout> --python <python-in-your-env>
```

It adapts the repo build flow and covers:

- `utils/pyvotkit/region` for VOT overlap utilities used by tracking.
- `utils/pysot/utils/region` for VOT evaluation helpers.
- `data/coco/pycocotools/_mask` for COCO mask preprocessing.

Use `--dry-run` first if you need to audit the commands without building.

## Verify the Environment

After dependency installation and extension build, run:

```bash
python scripts/check_environment.py --repo-root <siammask-checkout> --expect-cuda auto --check-cli
```

Use `--expect-cuda yes` before training or VOS tuning. A successful check proves imports, command-line help, compiled extension visibility, and CUDA allocation when requested; it does not prove full model checkpoints or benchmark datasets exist.

## Checkpoints, Datasets, and Network Steps

The repo workflows assume externally downloaded artifacts:

- SiamMask VOT/DAVIS checkpoints for demo and benchmark tracking.
- `resnet.model` for training initialization.
- VOT/DAVIS/YouTube-VOS benchmark data for testing.
- COCO, ImageNet DET, ImageNet VID, and YouTube-VOS raw data plus generated `crop511`/JSON files for training.

Do not start a download, unzip, crop, or training job until the user has authorized network/disk/runtime costs. Use [sub-skills/data-preparation/scripts/check_dataset_layout.py](../sub-skills/data-preparation/scripts/check_dataset_layout.py) to inspect local data first.

## Manual Runtime Pattern

If you bypass bundled wrappers, reproduce this pattern:

```bash
export PYTHONPATH=<siammask-checkout>:<selected-experiment-dir>:$PYTHONPATH
cd <selected-experiment-dir>
<python-in-your-env> <siammask-checkout>/tools/<entry>.py ...
```

Prefer bundled wrappers because they set this consistently and default to dry-run.
