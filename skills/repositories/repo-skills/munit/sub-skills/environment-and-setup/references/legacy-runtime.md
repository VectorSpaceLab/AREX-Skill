# Legacy Runtime for MUNIT

This reference distills the setup facts from the public MUNIT documentation, tutorial, Docker build recipe, CLI entry scripts, and runtime imports. It is self-contained so future agents do not need the original checkout to understand the environment contract.

## Runtime Identity

MUNIT was released for a 2018-era NVIDIA stack and is no longer maintained. The repository advertises Python 2.7 and Python 3.6 support. Its documented package recipe targets:

| Component | Legacy target | Why it matters |
|---|---:|---|
| Python | 2.7 or 3.6 | The code contains Python 2 compatibility shims, but the documented Anaconda path uses Anaconda3. Python 3.6 is the safest legacy choice when available. |
| PyTorch | 0.4.1 | Required by legacy APIs and checkpoint conversion helpers. Modern PyTorch removes `torch.utils.serialization.load_lua`, causing import-time failure in MUNIT utilities. |
| TorchVision | 0.2.x, commonly 0.2.1 | The code imports `torchvision.transforms` and `torchvision.utils`; pair the version with PyTorch 0.4.1. |
| CUDA | 9.1 in docs; 9.x family in practice | Training and inference scripts call CUDA unconditionally. The documented conda package is `cuda91`; the Docker base is CUDA 9.1 with cuDNN 7. |
| cuDNN | 7.x | The Docker base image includes cuDNN 7 runtime. |
| PyYAML | legacy PyYAML | Config loading uses `yaml.load(stream)` without a Loader argument. New PyYAML can warn or fail. |
| Pillow | any version compatible with the selected Python/TorchVision stack | Data and inference image loading use `PIL.Image`. |
| tensorboard | legacy package named `tensorboard` | Documentation lists tensorboard and the Dockerfile installs it with pip. |
| tensorboardX | legacy tensorboardX | `train.py` imports `tensorboardX.SummaryWriter`. |
| NumPy | compatible with PyTorch 0.4.1 | Used in interpolation utilities and batch metrics. |
| SciPy | optional, for batch metric mode | `test_batch.py` imports `scipy.stats.entropy` when computing IS/CIS-style metrics. |

## Conda Guidance

For faithful reproduction, create a dedicated legacy environment rather than installing into a modern project environment. A representative historical recipe is:

```bash
conda create -n munit-legacy python=3.6
conda activate munit-legacy
conda install pytorch=0.4.1 torchvision=0.2.1 cuda91 -c pytorch
conda install -c anaconda pip pyyaml pillow
pip install tensorboard tensorboardX
```

Notes:

- Package availability may require old conda channels, archived mirrors, or an existing lockfile because Python 3.6, CUDA 9.1, PyTorch 0.4.1, and TorchVision 0.2.x are end-of-life.
- A Python 2.7 environment can be attempted only when the selected PyTorch and TorchVision builds still exist on the chosen package source. Prefer Python 3.6 unless exact Python-2 reproduction is required.
- Keep this environment isolated. Modern packages often pull incompatible PyYAML, Pillow, NumPy, or TorchVision versions.
- CPU-only PyTorch is not enough for the original training/inference scripts because they call `.cuda()` directly. CPU-only work is limited to static checks and documentation/config inspection unless code is deliberately ported.

## Docker Guidance

The bundled Docker recipe is a historical environment blueprint, not a command that should be run automatically by an agent. It uses:

- `nvidia/cuda:9.1-cudnn7-runtime-ubuntu16.04`
- Anaconda3 5.0.1 installed under `/opt/anaconda`
- system packages for building, image conversion, downloads, archives, and OpenCV headers/runtime
- conda installs for PyTorch 0.4.1, TorchVision, CUDA 9.1, pip, and YAML support
- pip installs for tensorboard and tensorboardX

Use Docker only when the user approves container builds and has a host NVIDIA driver/runtime that can run CUDA 9.1-era containers. Original examples used the old `nvidia-docker` runtime style. Modern Docker installations may use `--gpus all`, but that does not solve framework/kernel incompatibility with newer GPU architectures.

## Hardware Compatibility

The tutorial names NVIDIA Titan-class GPUs for standard experiments and P100/V100-class GPUs with 16GB+ memory for large-resolution images. This matches the CUDA 9.1/PyTorch 0.4.1 generation.

Warnings:

- A100/Ampere or newer GPUs are not a good target for the unmodified legacy stack. CUDA 9.1 and PyTorch 0.4.1 do not include native Ampere support, so failures can include missing kernel images, unsupported architecture, driver/runtime mismatch, or binary import errors.
- A modern NVIDIA driver may be backward-compatible with old CUDA user-space libraries, but old PyTorch binaries still lack kernels for modern compute capabilities.
- If the only available hardware is A100 or newer, choose between (a) limiting this skill's runtime checks to static/import checks and requiring different hardware for faithful execution, or (b) doing a deliberate port to a newer PyTorch/CUDA stack under `model-internals` plus workflow-specific retesting.

## External Assets and Boundaries

MUNIT setup does not bundle research assets:

- pretrained translation checkpoints must be supplied by the user or acquired with explicit approval;
- full datasets are external and may require task-specific license/download decisions;
- the VGG `.t7` model used by perceptual-loss training is downloaded lazily by the original utility when `vgg_w > 0` and no converted weight exists;
- Inception weights for optional batch metrics are not bundled.

Environment setup may verify that local paths exist, but it must not download these assets or infer their licenses. Dataset schema and YAML path editing belong to `data-and-configuration`; training and inference commands belong to their own sub-skills.

## Safe Smoke Check

Use the bundled helper for non-destructive checks:

```bash
python scripts/check_munit_environment.py --repo-root /path/to/user/munit-checkout
```

The helper imports dependency packages, compares versions against the legacy target, checks whether `load_lua` is available, optionally parses YAML configs with the installed PyYAML, and statically notes CUDA-only code paths. It does not run repository scripts, allocate CUDA tensors, build models, start training, perform inference, or download assets.

Add CUDA probing only on explicit request:

```bash
python scripts/check_munit_environment.py --repo-root /path/to/user/munit-checkout --expect-cuda
```

`--expect-cuda` checks availability and reports device metadata when the selected PyTorch build exposes it. It still avoids tensor allocation.
