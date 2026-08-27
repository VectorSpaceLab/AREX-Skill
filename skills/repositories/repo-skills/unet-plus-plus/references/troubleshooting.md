# Cross-cutting troubleshooting

## Environment split problems

### Symptom
A user asks about both `nnUNet_*` commands and `segmentation_models` in one
place, or a single environment starts failing after trying to support both
stacks.

### Cause
The repo's PyTorch and Keras stacks live in different compatibility eras.
The PyTorch route needs a modern torch/CUDA installation. The Keras route is a
legacy TensorFlow 1.4.1 / Keras 2.2.2 stack.

### Fix
Use separate environments and route to the correct sub-skill before making any
install decisions.

## Source-checkout dependency leakage

### Symptom
A workflow only works when the original checkout is still present.

### Cause
The user-facing skill was not fully distilled into its own runtime references or
scripts.

### Fix
Read the bundled reference or script under `sub-skills/<id>/` instead of using
source-repo paths.

## Backend confusion

### Symptom
A PyTorch workflow is treated as CPU-only, or a legacy Keras workflow is
presented as if it were a modern TF2 package.

### Cause
The repo contains two very different backend stories.

### Fix
- For nnU-Net, keep the CUDA-capable PyTorch environment and verify `torch.cuda.is_available()`.
- For Keras, keep the legacy CPU-friendly model-construction environment and do
  not claim modern TensorFlow 2 behavior.

## Long-running workflows

### Symptom
A user expects training or dataset conversion to be a quick smoke test.

### Cause
Both stacks include workflows that can be expensive or data-bound.

### Fix
Use the bundled scripts for tiny runtime checks only. Leave full training,
large downloads, and dataset-specific runs to the explicit workflow references
and the verification layer.

## What this file does not replace

Stack-specific issues belong in the nearest sub-skill troubleshooting reference.
Read the following instead when the issue is specific:

- `sub-skills/nnunet/references/troubleshooting.md`
- `sub-skills/keras/references/troubleshooting.md`
