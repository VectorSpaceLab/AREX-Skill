# Environment and installation

## When to read

Read this reference when a task starts with installing MMAction2, verifying imports, choosing CPU versus CUDA, diagnosing optional dependencies, or deciding whether an inference/training/export workflow is safe to run.

## Public package identity

- Distribution name: `mmaction2`
- Import package: `mmaction`
- Generated skill baseline: MMAction2 `1.2.0`
- Core OpenMMLab dependencies verified for this skill: `mmcv>=2.0.0rc4,<2.2.0`, `mmengine>=0.7.1,<1.0.0`
- Core runtime surface: PyTorch, NumPy, OpenCV/decord video decoding, MMEngine configs/runners, MMAction2 registries.

## Recommended install shape

For most users, install PyTorch for the target CPU/CUDA platform first, then install OpenMMLab dependencies and MMAction2:

```bash
pip install -U openmim
mim install mmengine
mim install "mmcv>=2.0.0rc4,<2.2.0"
pip install mmaction2
```

For development, custom modules, or access to repo-provided config/tool files, use an editable install of the user's chosen checkout after the compatible dependencies are installed:

```bash
pip install -v -e .
```

For CPU-only environments, pass explicit CPU device options in APIs and command plans. For CUDA environments, match the PyTorch CUDA wheel, MMCV wheel, NVIDIA driver, and any compiled extension packages; do not treat a CPU import as proof that CUDA paths work.

## Core import check

```python
import mmaction, mmcv, mmengine, torch
print("mmaction", mmaction.__version__)
print("mmcv", mmcv.__version__)
print("mmengine", mmengine.__version__)
print("torch", torch.__version__, "cuda", torch.cuda.is_available())
```

Use the bundled helper for a more complete safe check:

```bash
python scripts/check_mmaction2_environment.py --probe-config USER_CONFIG.py
```

The helper reports core/optional package status, torch CUDA availability, and optional config parsing. It does not download weights, run inference, train, test, or scan datasets.

## Dependency groups and optional extras

| Surface | Packages / prerequisites | Notes |
| --- | --- | --- |
| Core recognizer APIs and configs | `torch`, `mmengine`, `mmcv`, `numpy`, `opencv-python`/`opencv-contrib-python`, `decord`, `Pillow`, `scipy`, `einops` | Enough for import/config/API smoke and many CPU workflows. |
| Detector-assisted or pose-assisted demos | `mmdet`, `mmpose`, local detector/pose configs and checkpoints | Required by `detection_inference` and `pose_inference`; missing packages raise explicit `ImportError`. |
| Audio workflows | audio feature `.npy` files; optional `librosa`, `soundfile`, movie/audio tooling for feature extraction | Core `AudioDataset` consumes prepared features; extraction utilities may need extras. |
| Multimodal/retrieval workflows | multimodal requirements such as tokenizer/CLIP-related packages depending on config | Install only when the selected model/config imports them. |
| Visualization/logging | local visualization backend by default; optional TensorBoard/W&B packages for those backends | Avoid GUI display on headless servers; prefer saved outputs. |
| Export/deployment | ONNX/ONNX Runtime, TorchServe model archiver, deployment-specific packages | These mutate/export artifacts; verify prerequisites before execution. |
| Distributed training/testing | working PyTorch distributed stack; GPUs/network/Slurm as applicable | Command templates are not verification of hardware or cluster readiness. |

## CPU and CUDA decision rules

- CPU is valid for import checks, config parsing, command planning, many unit-style model construction checks, and small inference/training experiments when performance is not the goal.
- CUDA is required only when the user's task explicitly needs GPU performance, multi-GPU/distributed execution, a GPU-only model/dependency, or a final verification case classified as CUDA-required.
- If CUDA is selected, verify at least:

```python
import torch
print(torch.__version__, torch.version.cuda)
print(torch.cuda.is_available(), torch.cuda.device_count())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
    torch.empty((1,), device="cuda")
```

## Safe setup triage

1. Run the core import check.
2. If import fails, compare `mmcv` and `mmengine` versions against MMAction2's expected ranges.
3. If config parsing fails, use `data-and-configs` before diagnosing training/inference.
4. If API construction fails, check whether the model type or registry class is registered; use `models-and-extension` for registry/custom-module issues.
5. If a demo path fails on optional packages, install only the package needed by that path rather than broad optional extras.
6. If CUDA fails, verify the framework backend first; do not debug MMAction2 model code until `torch.cuda` passes a tiny allocation.

## What this skill does not prove

A successful import/config check does not prove that user media decodes, checkpoints match a config, datasets are correctly formatted, distributed launch works, or optional deployment tooling is installed. Use the relevant sub-skill and run bounded checks for those workflows.
