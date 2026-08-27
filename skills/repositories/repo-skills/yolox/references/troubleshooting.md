# YOLOX Cross-Cutting Troubleshooting

Use this root reference for problems that happen before a workflow clearly belongs to inference, training/data, or export/deployment. For workflow-specific failures, continue to the nearest sub-skill troubleshooting reference.

## First triage

```bash
python scripts/check_yolox_install.py --name yolox-nano --device auto --test-size 64
python -c "import yolox; print(yolox.__version__)"
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.device_count())"
```

Then route:

- Inference/checkpoint/demo failures: `sub-skills/inference-and-api/references/troubleshooting.md`
- Dataset, `Exp`, train, eval, logger, cache, distributed failures: `sub-skills/training-and-data/references/troubleshooting.md`
- ONNX/TorchScript/TensorRT/OpenVINO/ncnn/MegEngine/nebullvm failures: `sub-skills/export-and-deployment/references/troubleshooting.md`

## Failure matrix

| Symptom | Likely cause | Checks | Fix |
|---|---|---|---|
| `ModuleNotFoundError: No module named 'yolox'` | YOLOX is not installed in the active Python environment. | Run `python -c "import sys; print(sys.executable)"`; check `python -m pip show yolox`. | Install YOLOX into the same environment used for the command. Prefer package/module commands after install. |
| Import finds a stale or unintended YOLOX copy | Multiple installs or current directory shadowing. | Print `yolox.__file__`; check `PYTHONPATH` and current working directory. | Use an isolated environment; remove stale installs; avoid running from directories that shadow package names. |
| Source install fails compiling `fast_cocoeval` | Missing compiler, Python headers, PyTorch C++ headers, `ninja`, or pybind11 headers. | Inspect build stderr for missing header/tool names. | Install compatible build tools and headers. If COCO fast eval is not needed immediately, still verify ordinary package imports and document the extension limitation. |
| `pip check` reports dependency conflicts | Mismatched PyTorch/torchvision/OpenCV/ONNX packages or resolver drift. | Run `python -m pip check`. | Reinstall compatible versions in a clean environment. Do not mix CPU and CUDA variants accidentally. |
| `torchvision::nms` or operator import errors | Torch and torchvision ABI/CUDA tags are incompatible. | Print `torch.__version__`, `torch.version.cuda`, and `torchvision.__version__`. | Install matching torch/torchvision builds for the same Python/CUDA/CPU variant. |
| CUDA requested but unavailable | CPU-only torch, driver/runtime mismatch, no visible GPU, or container lacks device passthrough. | Run the CUDA check in `installation-and-environment.md`. | Use `--device cpu` for smoke checks or install/use a CUDA-capable PyTorch runtime on compatible hardware. |
| FP16 fails | `--fp16` was used without compatible CUDA AMP support. | Check `torch.cuda.is_available()` and device placement. | Drop `--fp16` for CPU; fix CUDA runtime before training/eval/inference with FP16. |
| Command uses a source script path that does not exist | User is following checkout-specific examples without a checkout. | Inspect command for checkout-specific script paths. | Prefer installed module commands (`python -m yolox.tools.demo`, `python -m yolox.tools.train`, `python -m yolox.tools.eval`) or bundled helper scripts in this skill. |
| Checkpoint path missing | YOLOX examples assume manually downloaded weights. | Check file existence before running. | Ask for/download the correct checkpoint with permission; use dry-run helpers when no weights are available. |
| Checkpoint load shape mismatch | Model name/Exp differs from checkpoint architecture or `num_classes`. | Compare built-in model name/custom Exp fields and checkpoint source. | Select the matching `--name`/`--exp-file`; for new class counts, fine-tune with a compatible backbone and train the head. |
| Old checkpoint only works with `--legacy` | YOLOX preprocessing changed in older releases. | Try PyTorch demo/eval guidance with `--legacy`. | Use `--legacy` only for PyTorch demo/eval; deployment demos do not support old legacy weights. |
| Full workflow would require downloads, credentials, or long compute | Missing resources or unapproved side effects. | Identify checkpoint/data/logger/backend requirements. | Ask for resource paths and permission; otherwise run only smoke/dry-run checks. |
| Optional backend import fails (`onnxruntime`, TensorRT, OpenVINO, ncnn, MegEngine, nebullvm) | Optional deployment stack is not installed or does not match the platform. | Route to export/deployment backend matrix. | Install the selected backend stack only when that workflow is required; do not install all optional stacks by default. |

## Safety rules

- Do not start long training, benchmark evaluation, dataset downloads, checkpoint downloads, webcam access, network loggers, or vendor toolchain builds unless the user has supplied resources and permission.
- Do not treat a skipped optional deployment backend as verified.
- Do not use CPU smoke checks as proof of CUDA, TensorRT, or vendor accelerator readiness.
