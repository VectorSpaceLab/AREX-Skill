# Cross-cutting Troubleshooting

## When to read

Read this when a face.evoLVe task fails before the workflow-specific sub-skill can proceed: imports fail, the wrong Paddle package is loaded, training entrypoints do not compile, optional datasets/checkpoints are missing, or backend assumptions are unclear.

## Repository root shadows PaddlePaddle

**Symptom:** `import paddle` succeeds but `paddle.nn` is missing, PaddleSlim fails with `No module named 'paddle.nn'`, or Paddle scripts import the local source directory instead of the PaddlePaddle framework.

**Likely cause:** the target checkout has a top-level `paddle/` directory. If the checkout root is on `PYTHONPATH`, Python may load that local package as `paddle`.

**Recovery:** run Paddle helpers that import the PaddlePaddle framework from a neutral path first, then add the checkout's `paddle/` source directory. Use `sub-skills/paddle-workflows/scripts/inspect_paddle_components.py` for this pattern.

## PyTorch training entrypoint does not compile

**Symptom:** `SyntaxError` appears around the `LOSS_DICT` block in the PyTorch training entrypoint.

**Likely cause:** this snapshot contains a malformed expansion of experimental losses in the PyTorch training script: missing comma separators and undefined constructors appear after the stable `Focal`/`Softmax` entries.

**Recovery:** do not run full training until the entrypoint is repaired. For stable README behavior, reduce the loss dictionary to `FocalLoss()` and `nn.CrossEntropyLoss()` or explicitly import and instantiate every experimental class correctly. Then run `sub-skills/pytorch-training/scripts/inspect_pytorch_components.py` before launching a real train job.

## `head.metrics` fails with `NameError: Module`

**Symptom:** importing PyTorch `head.metrics` fails, even if `torch` is installed.

**Likely cause:** later experimental head classes inherit from `Module`, but the file imports `torch.nn as nn` and `Parameter` without importing `Module`.

**Recovery:** for inspection, use the bundled PyTorch component inspector, which patches `Module` in memory without modifying the checkout. For real training, add `from torch.nn import Module` or change those experimental classes to inherit from `nn.Module`, then re-run smoke checks.

## `bcolz` or validation data errors

**Symptom:** validation utilities fail with `ModuleNotFoundError: bcolz`, `np.bool` errors, missing `lfw`, `cfp_fp`, `agedb_30`, or `_list.npy` files.

**Likely cause:** `bcolz` is an old dependency and validation arrays are external artifacts. The training utilities expect `bcolz.carray` folders and matching `<name>_list.npy` files under the configured data root.

**Recovery:** use a compatible NumPy/`bcolz` pair or port validation loading to a maintained format. Verify the data layout with `sub-skills/data-preparation/SKILL.md` before training.

## Missing model weights, datasets, or demo artifacts

**Symptom:** checkpoint loading fails, feature extraction cannot start, Paddle Inference cannot find `.pdmodel`/`.pdiparams`, Paddle Lite cannot find `.nb`, or demo recognition cannot build `face_data.fdb`.

**Likely cause:** model-zoo weights, public datasets, exported Paddle models, FaceDatabase images, and demo videos are not bundled with this repo skill.

**Recovery:** route to the nearest workflow sub-skill and check its artifact list. Do not start downloads or long training without user approval and adequate storage/runtime.

## Backend mismatch

**Symptom:** CUDA requested but `torch.cuda.is_available()` is false, Paddle Inference hard-codes GPU but no GPU is usable, or `GPU_ID` does not match visible devices.

**Likely cause:** CPU-only framework wheels, missing driver/container GPU passthrough, or config copied from multi-GPU README examples.

**Recovery:** for planning, use CPU smoke checks. For real training/deployment, install the correct framework build, verify a tiny CUDA/Paddle backend operation, and update `MULTI_GPU`, `GPU_ID`, or Paddle predictor settings before running expensive workloads.

## Where to go next

- Alignment failures: `sub-skills/face-alignment/references/troubleshooting.md`.
- Data layout and low-shot failures: `sub-skills/data-preparation/references/troubleshooting.md`.
- PyTorch model/training failures: `sub-skills/pytorch-training/references/troubleshooting.md`.
- Feature extraction or verification failures: `sub-skills/feature-extraction-verification/references/troubleshooting.md`.
- Paddle training/quant/deployment failures: `sub-skills/paddle-workflows/references/troubleshooting.md`.
