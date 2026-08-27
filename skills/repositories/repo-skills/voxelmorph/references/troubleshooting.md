# VoxelMorph Troubleshooting

## Purpose

Use this root guide for cross-cutting install/import, dependency, API-version, backend, and routing failures. For workflow-specific problems, follow the linked sub-skill troubleshooting references.

## First triage

1. Confirm the package imports:

   ```python
   import voxelmorph as vxm
   import neurite
   import torch
   print(vxm.__version__, neurite.__version__, torch.__version__)
   ```

2. Run the root smoke checker:

   ```bash
   python scripts/check_voxelmorph_env.py
   ```

3. Route by symptom:
   - Tensor shape, affine, displacement, coordinate, interpolation, integration, or composition issue → `sub-skills/transform-ops/references/troubleshooting.md`.
   - `VxmPairwise`, Neurite losses, checkpoint, or synthetic training issue → `sub-skills/pairwise-registration/references/troubleshooting.md`.
   - `.npz`, NIfTI/MGZ, file lists, labels, segmentations, atlas arrays, or generator issue → `sub-skills/data-generators/references/troubleshooting.md`.

## Cross-cutting failure table

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: voxelmorph` | Package not installed in the current Python environment. | Install with `python -m pip install voxelmorph` or, for a source checkout, `python -m pip install -e .`; then run `python -m pip check`. |
| `ImportError: voxelmorph requires neurite version 0.3 or greater` | Missing or outdated Neurite dependency. | Install/upgrade the base dependencies so `neurite>=0.3` is available. |
| `ModuleNotFoundError` for `nibabel`, `scipy`, `skimage`, `h5py`, or `pystrum` | Incomplete base installation or dependency resolver failure. | Reinstall the package in an isolated environment and run `python -m pip check`. |
| Old tutorial command uses `scripts/tf/...` | The command is from TensorFlow-era documentation and does not match this PyTorch branch. | Use the current sub-skills for PyTorch APIs, or explicitly switch to the TensorFlow branch/package required by that tutorial. |
| `AttributeError: module 'voxelmorph' has no attribute 'networks'` | A legacy `VxmDense` example or script is being used against the current package. | Use `vxm.nn.models.VxmPairwise` for current workflows; do not run old `vxm.networks.VxmDense.load(...)` examples unless using a matching legacy branch. |
| `NotImplementedError` from `voxelmorph.nn.losses.*` | Loss classes in this branch are compatibility stubs. | Use `neurite.nn.modules.MSE`, `NCC`, `Dice`, or `SpatialGradient`. |
| CPU checks pass but CUDA is unavailable | Installed PyTorch is CPU-only, the driver/runtime is unavailable, or the container does not expose GPUs. | Use CPU for synthetic verification. For real GPU tasks, install a CUDA-capable PyTorch build and verify `torch.empty((1,), device='cuda')`. |
| Real training consumes too much memory or time | VoxelMorph 3D training and integration are memory-intensive. | Start with synthetic smoke, reduce spatial shape/features/batch size/integration steps, then scale up only after data and device are validated. |
| Registration quality is poor even though code runs | Data preprocessing, intensity normalization, affine alignment, loss choice, or training duration may be unsuitable. | Validate data shape/keys, normalize intensities, confirm affine alignment assumptions, inspect losses, and request explicit evaluation criteria before making quality claims. |

## Deprecated or stale surfaces

This skill is based on the current PyTorch package surface. Treat the following as warnings, not runnable guidance:

- `scripts/tf/train.py`, `scripts/tf/register.py`, and other TensorFlow branch paths.
- `.h5` model-loading examples tied to TensorFlow/Keras networks.
- `vxm.networks.VxmDense.load(...)` in legacy scripts.
- Lab-local dataset paths or examples that assume private OASIS preprocessing directories.

## Safe escalation path

When a user brings a real dataset or checkpoint:

1. Validate `.npz` data with the data-generators validator, or separately inspect NIfTI/MGZ shapes/affines.
2. Run the pairwise-registration tiny smoke on the intended device.
3. If fields or warps look wrong, run transform-ops smoke and inspect sign/axis conventions.
4. Only then attempt real training, checkpoint loading, or registration evaluation.

Stop and ask for concrete files, checkpoint architecture, device requirements, and expected outputs if any of those are missing.
