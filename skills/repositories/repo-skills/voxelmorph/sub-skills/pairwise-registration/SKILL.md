---
name: pairwise-registration
description: "Construct and smoke-test VoxelMorph VxmPairwise registration
  models with current PyTorch APIs, Neurite losses, checkpoint patterns, and
  legacy-script caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Pairwise Registration

Use this sub-skill when the task is to build, call, smoke-train, checkpoint, or troubleshoot the current PyTorch `voxelmorph.nn.models.VxmPairwise` pairwise registration model.

## Route here for

- Constructing `VxmPairwise` with dimensionality, image channels, UNet features, integration steps, and Neurite-backed modules.
- Understanding `forward()` return options: displacement/velocity fields, warped source images, warped target images, and their shapes.
- Writing short synthetic training loops that use Neurite losses and avoid dataset, download, or institutional-path dependencies.
- Saving/loading model checkpoints using a config plus `state_dict` pattern.
- Migrating or rejecting legacy registration examples that refer to APIs not exposed by the current package.

## Route elsewhere

- Dense transform math, coordinate conventions, composition, affine-to-displacement conversion, and standalone spatial warping: use `transform-ops`.
- Volume files, `.npz`/NIfTI schema preparation, image lists, real-data generators, segmentation labels, and validation of file layouts: use `data-generators`.
- Long real training jobs, benchmark-quality registration, model downloads, or clinical validation: out of scope for this operating sub-skill unless a separate task supplies data, runtime, and acceptance criteria.

## Current operating contract

- Public model entry point: `voxelmorph.nn.models.VxmPairwise`.
- Tensor convention: images are PyTorch tensors shaped `(B, C, *spatial)`, and predicted fields are shaped `(B, ndim, *spatial)`.
- Losses should come from `neurite.nn.modules`; `voxelmorph.nn.losses` classes are compatibility stubs that raise deprecation errors.
- The bundled smoke script uses deterministic synthetic 2D tensors on CPU by default and performs a tiny optimizer loop only.
- Do not present old TensorFlow script paths, `vxm.networks.VxmDense`, or the legacy registration CLI as runnable guidance for this PyTorch package.

## Bundled references

- `references/api-reference.md` — verified constructor/forward signatures, return-shape matrix, Neurite loss choices, and error cases.
- `references/workflows.md` — model construction, tiny training loop, checkpoint round-trip, and current inference/legacy-script caveats.
- `references/troubleshooting.md` — failures around integration flags, `unet_kwargs`, Neurite imports/losses, shape divisibility, checkpoint mismatches, and stale scripts.
- `scripts/tiny_pairwise_training_smoke.py` — safe synthetic CPU smoke for model construction, Neurite losses, one or more optimizer steps, and optional checkpoint round-trip.

## Quick safe check

From this sub-skill directory, run:

```bash
python scripts/tiny_pairwise_training_smoke.py --help
python scripts/tiny_pairwise_training_smoke.py --steps 1 --spatial-size 16 --features 4 4 4
```

The check should finish quickly without downloading data or writing files unless `--checkpoint-out` is explicitly provided.
