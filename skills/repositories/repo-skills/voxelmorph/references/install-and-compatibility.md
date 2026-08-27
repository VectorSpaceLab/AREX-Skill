# Install and Compatibility

## Purpose

Read this before relying on VoxelMorph APIs in a new Python environment, especially when old tutorials, TensorFlow-era commands, or GPU expectations are involved.

## Current package identity

- Distribution name: `voxelmorph`.
- Import name: `voxelmorph`.
- Distilled version: `0.3.3`.
- Python support from package metadata: `>=3.8`.
- Core runtime dependencies from package metadata: `torch`, `scikit-image`, `packaging`, `numpy`, `scipy`, `nibabel`, `h5py`, and `neurite>=0.3`.
- Current primary model API: `voxelmorph.nn.models.VxmPairwise`.
- Current public data utilities: `voxelmorph.py.utils` and `voxelmorph.py.generators`.

## Install patterns

For normal users, install the published package:

```bash
python -m pip install voxelmorph
python - <<'PY'
import voxelmorph as vxm
import neurite
import torch
print(vxm.__version__, neurite.__version__, torch.__version__)
PY
```

For source development or local branch inspection, use an isolated environment and editable install:

```bash
python -m pip install -e .
python -m pip check
python - <<'PY'
import voxelmorph as vxm
print(vxm.__version__)
PY
```

If using Conda or another environment manager, create the environment first and then run the same `python -m pip ...` commands through that environment's Python.

## Backend guidance

VoxelMorph's current PyTorch APIs run on CPU for package inspection, synthetic smokes, transform operations, and small tests. Install a CUDA-capable PyTorch build only when the task explicitly needs GPU execution for real training or large registration workloads.

Before claiming GPU readiness, verify the actual environment:

```python
import torch
print(torch.__version__, torch.version.cuda)
print(torch.cuda.is_available(), torch.cuda.device_count())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
    torch.empty((1,), device="cuda")
```

A host with a visible NVIDIA GPU is not enough if the installed PyTorch wheel is CPU-only or the container lacks GPU passthrough.

## Quick package smoke

Use the bundled root checker when VoxelMorph is importable in the current environment:

```bash
python scripts/check_voxelmorph_env.py --help
python scripts/check_voxelmorph_env.py
```

This checks import/version facts, current signatures, a tiny `VxmPairwise` forward pass, and a tiny transform operation. It does not download data or run real training.

## Branch and API drift warnings

The public README contains both current PyTorch branch notes and older TensorFlow-era examples. For this distilled skill:

- Treat `voxelmorph.nn.models.VxmPairwise` as the current pairwise model entry point.
- Do not route users to `scripts/tf/...`; those paths are not part of this branch.
- Do not present `vxm.networks.VxmDense.load(...)` as a runnable current API; the distilled branch does not expose `vxm.networks`.
- `voxelmorph.nn.losses` classes are deprecation stubs. Use Neurite loss modules instead.
- If the user has `.h5` weights, TensorFlow/Keras model artifacts, or a tutorial requiring `VxmDense`, ask for the matching branch/package or a converted current checkpoint.

## Optional docs and development dependencies

Documentation build dependencies live separately from runtime package usage and are not needed for this operating skill. Pre-commit/pycodestyle tooling is for repository maintenance, not for using VoxelMorph as a registration library.

## Minimum self-checks before a real task

1. Run the root environment checker.
2. For transform math, run `sub-skills/transform-ops/scripts/transform_ops_smoke.py`.
3. For model construction/training loops, run `sub-skills/pairwise-registration/scripts/tiny_pairwise_training_smoke.py`.
4. For `.npz` data lists, run `sub-skills/data-generators/scripts/validate_vxm_npz.py`.
5. Only then move to real data, long training, CUDA execution, or checkpoint handling.
