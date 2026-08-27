---
name: environment-and-setup
description: "Select and validate the legacy runtime, dependencies, and setup
  boundaries for NVlabs/MUNIT without running training or inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Environment and Setup

Use this sub-skill when a Researcher needs to choose, prepare, or triage a MUNIT runtime before touching data, training, or inference. MUNIT is a legacy CUDA-era PyTorch project: treat environment selection as part of the experiment design, not as a routine modern-package install.

## Responsibilities

- Pick a legacy-compatible runtime: Python 2.7 or 3.6, PyTorch 0.4.1, TorchVision 0.2.x, CUDA 9.x, cuDNN 7.x, PyYAML, Pillow, tensorboard, and tensorboardX.
- Explain the historical Docker and conda setup choices and their compatibility limits.
- Define checkpoint, VGG-weight, and dataset acquisition boundaries without performing downloads.
- Run safe environment smoke checks that import dependencies and statically inspect the checkout; do not launch `train.py`, `test.py`, `test_batch.py`, dataset download scripts, CUDA kernels, or full model construction from this sub-skill.
- Diagnose installation and compatibility failures such as missing tensorboardX/PyYAML/Pillow/TorchVision, modern PyTorch `load_lua` removal, PyYAML Loader changes, and modern-GPU mismatch.

## Start Here

1. Read `references/legacy-runtime.md` to decide whether the task needs exact legacy reproduction, a Docker-style legacy container, or a porting-oriented modern environment.
2. If a Python environment already exists, run the bundled helper from any directory:

   ```bash
   python scripts/check_munit_environment.py --repo-root /path/to/user/munit-checkout
   ```

   Add `--expect-cuda` only when the user explicitly wants a CUDA availability probe. The helper does not allocate CUDA tensors by default.
3. If the helper reports missing packages or legacy incompatibilities, read `references/troubleshooting.md` before changing the environment.
4. Route non-setup work to sibling sub-skills:
   - dataset layout, list files, YAML schema, and config editing: `data-and-configuration`
   - actual train/resume commands and output interpretation: `training`
   - single-image, batch, checkpoint, or metric inference commands: `inference-and-evaluation`
   - network/trainer class internals or code porting details: `model-internals`

## Safety Gates

- Do not run repository demo shell scripts as setup checks: they remove/create dataset folders, download archives, invoke ImageMagick conversion, and start training.
- Do not auto-download pretrained checkpoints, datasets, VGG `.t7` files, or Inception weights. Require the user to provide local paths or explicit approval.
- Do not treat a CPU-only import as proof that training or inference can run: the original scripts call `.cuda()` unconditionally.
- Do not use modern PyTorch success as compatibility proof. Importing MUNIT utilities depends on `torch.utils.serialization.load_lua`, which is absent from modern PyTorch.
