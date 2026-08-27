# Cross-cutting troubleshooting

Use this for installation/import/backend failures before routing into a workflow-specific sub-skill.

## `ImportError: Unable to import modules due to missing mxnet & torch`

Cause: GluonCV's top-level import requires MXNet `>=1.4,<2.0` or PyTorch `>=1.4,<2.0`.

Fix:

1. Decide whether the task needs MXNet, PyTorch, or both.
2. Install only the selected backend stack.
3. Run `python scripts/check_gluoncv_environment.py`.

Route MXNet model-zoo work to `sub-skills/mxnet-model-zoo/`; route Torch action/video work to `sub-skills/torch-video-workflows/`.

## MXNet imports fail with NumPy alias errors

Symptoms include errors involving `np.bool`, `np.object`, or other removed aliases.

Cause: MXNet 1.x is not compatible with modern NumPy releases in many environments.

Fix:

```bash
python -m pip install 'numpy<1.24'
```

Then reinstall or recheck MXNet/GluonCV. Avoid upgrading NumPy in a working MXNet 1.x environment unless another package requires it and you have a plan.

## Torch side fails with `PIL.Image.LINEAR`

Symptom: importing `gluoncv.torch` fails with `AttributeError: module 'PIL.Image' has no attribute 'LINEAR'`.

Cause: legacy GluonCV Torch transforms reference constants removed by newer Pillow.

Fix:

```bash
python -m pip install 'Pillow<10'
```

Then rerun the Torch import or `sub-skills/torch-video-workflows/scripts/torch_video_model_smoke.py`.

## Both MXNet and PyTorch warning

Symptom: importing `gluoncv` warns that both frameworks are installed and may increase GPU memory footprint.

Cause: GluonCV detected both backends. This is expected if both packages are present.

Fix: Usually none. If memory-sensitive GPU work is planned, use a backend-specific environment to avoid importing the unused framework.

## Pretrained downloads, cache, and network failures

Symptoms: slow first model construction, hash/download errors, permission errors in model cache, or missing pretrained parameters.

Cause: `pretrained=True`, export helpers, demos, or evaluation scripts may fetch weights or expect existing cache files.

Fix:

1. For dry runs, use `pretrained=False` and initialize weights manually where needed.
2. Confirm network/cache policy before pretrained inference or export.
3. Use user-approved cache/output directories for real work.
4. Do not delete cache files without approval.

## GPU/CUDA mismatch

Symptoms: invalid device ordinal, no CUDA device, CPU-only package selected, driver/toolkit mismatch, NCCL failure, or out-of-memory.

Fix:

1. Confirm the backend package is CUDA-capable, not CPU-only.
2. Confirm visible GPUs and IDs.
3. Run a tiny backend CUDA allocation before launching GluonCV scripts.
4. Lower batch size, image shape, video clip length, and worker count.
5. Treat DDP/Horovod/DALI/benchmark jobs as optional hardware workflows requiring explicit resource approval.

## Optional dependency import errors

Common missing packages: `torchvision`, `decord`, `pycocotools`, `tensorboardX`, `autogluon.core`, `timm`, `onnx`, `onnxruntime`, `tvm`, `horovod`, `nvidia.dali`.

Fix: install only the dependency needed for the selected sub-skill. Do not use broad extras as a first step.

## Dataset and script failures

For dataset roots, annotation schemas, images/videos, transforms, and loader failures, route to `sub-skills/data-transforms-datasets/`.

For command construction, flags, GPUs, long training/evaluation, resume/checkpoints, and script-zoo side effects, route to `sub-skills/training-evaluation-scripts/`.

For AutoGluon/export/ONNX/TVM/quantized workflows, route to `sub-skills/automl-deployment-export/`.
