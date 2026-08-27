---
name: augmentation-and-sampling
description: "Guides braindecode signal transforms, composed augmentation
  loaders, and sequence, relative-positioning, and self-supervised samplers with
  shape-safe validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Augmentation and sampling

Use this route when augmentations, `Transform` composition,
`AugmentedDataLoader`, `n_augmentation`, sequence sampling, relative
positioning, or self-supervised sampling is the main task.

## Workflow

1. Confirm batches are `(X, y)` with `X` shaped `(batch, channels, time)` and
   that labels remain aligned after each transform.
2. Build a `Transform` or `Compose` with an explicit probability and random
   state. Test it on one batch and verify shape, dtype, device, and label
   invariants.
3. Use `AugmentedDataLoader` for training batches. Remember that
   `n_augmentation=0` preserves the original batch; positive values append
   transformed copies after clean originals and tile labels accordingly.
4. Choose sequence/relative-positioning/self-supervised samplers only when the
   dataset contains the required trial/session/window metadata. Verify indices
   and split boundaries before training.
5. Use CPU first. Move both model and batches to CUDA only after a bounded
   allocation succeeds; a CUDA availability flag is not a memory guarantee.

Read [API reference](references/api-reference.md), [sampling workflows](references/sampling-workflows.md),
and [troubleshooting](references/troubleshooting.md). Run the deterministic
[augmentation smoke](scripts/smoke_augmentation.py), which uses a local
`TensorDataset` and no network or credentials.
