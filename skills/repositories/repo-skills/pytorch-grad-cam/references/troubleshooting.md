# Cross-Cutting Troubleshooting

## Install/import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'pytorch_grad_cam'` | The PyPI distribution is named `grad-cam`, not `pytorch-grad-cam`. | Run `pip install grad-cam`, then verify `import pytorch_grad_cam`. |
| Import fails for `cv2`, `ttach`, `sklearn`, or `scipy` | Runtime dependencies are missing or a partial install was used. | Reinstall with `pip install grad-cam` or install the missing package explicitly. |
| `torch` / `torchvision` binary errors | Python, CUDA, platform, or wheel ABI mismatch. | Install a compatible PyTorch/TorchVision pair first, then install `grad-cam`. Keep CPU vs CUDA wheel choices explicit. |
| CLIP or Swin example import fails for `transformers` or `timm` | Optional example dependency is not part of the base package. | Install only the needed optional package, e.g. `pip install transformers` for CLIP or `pip install timm` for Swin. |

Run [`../scripts/check_grad_cam_environment.py`](../scripts/check_grad_cam_environment.py)
for a safe import and optional-backend diagnostic.

## Device and backend issues

- Place the model and input tensor on the same device before invoking CAM.
- A CUDA-capable PyTorch import does not prove a user's model can run on CUDA;
  run a tiny tensor allocation first when device execution matters.
- HPU support requires `habana_frameworks.torch.core` when the model device
  string contains `hpu`; do not present HPU as verified unless that vendor
  package imports and a device smoke passes.
- MPS requires macOS/Apple Silicon and PyTorch MPS support; Linux CPU/CUDA
  checks do not verify MPS.

## Source-independence mistakes

Future agents should not tell users to run repository-local example files or
notebooks from a vanished checkout. Use this skill's bundled scripts and
references instead:

- Method/signature discovery: `scripts/inspect_cam_methods.py`
- Environment/import check: `scripts/check_grad_cam_environment.py`
- Tiny CAM smoke: `sub-skills/cam-generation/scripts/tiny_cam_smoke.py`
- Reshape transform validation:
  `sub-skills/model-task-adaptation/scripts/validate_reshape_transform.py`
- Tiny metric smoke:
  `sub-skills/metrics-and-evaluation/scripts/tiny_metric_smoke.py`

## Runtime CAM failures

If a CAM output is blank, all zeros, or shape-mismatched:

1. Confirm the selected target layer is spatial and participates in the target
   scalar's computation.
2. Confirm `targets` is `None` or has one callable per batch member.
3. Confirm the model returns tensors or output structures expected by the
   target callable.
4. For transformers or detection models, confirm `reshape_transform` returns a
   channel-first spatial tensor.
5. For visualization, confirm the base image is float `[0, 1]` and the mask is
   scaled to the input spatial size.

Route to the nearest sub-skill troubleshooting file for workflow-specific
symptoms.
