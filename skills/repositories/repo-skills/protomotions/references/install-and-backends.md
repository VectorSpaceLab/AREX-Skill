# Install and backend overview

ProtoMotions is intentionally backend-separable. Treat each simulator stack as its own environment unless you have evidence that two stacks share compatible Python, torch, CUDA, and optional dependencies.

## Package baseline

- Distribution/import: `protomotions`
- Python requirement: `>=3.8`
- Base dependencies include `torch`, `lightning`, `tensordict`, `dm-control`, `mujoco`, `numpy`, `scipy`, `trimesh`, `wandb`, and plotting/data utilities.
- Console scripts: `protomotions`, `protomotions-train-agent`, `protomotions-inference-agent`.
- Optional extras: `mujoco`, `newton`, `isaacgym`, `isaaclab`, `genesis`, `docs`, `dev`.
- The optional extras conflict with each other by design; do not install every extra into one prefix.

## Backend matrix

| Backend | Environment guidance | Runtime notes |
| --- | --- | --- |
| MuJoCo | Python 3.10+ or 3.11; install `protomotions[mujoco]` or base package plus MuJoCo/ONNX runtime dependencies | CPU-oriented, normally `num-envs=1`; good for debug, sim2sim smoke, and standalone deployment validation. |
| Newton | Python 3.10+; install CUDA-enabled torch first, then Newton/Warp stack and ProtoMotions Newton requirements | Requires NVIDIA GPU, driver 545+, and compatible torch/CUDA. Use separate env from MuJoCo if versions conflict. |
| IsaacLab | Python 3.12; create pinned IsaacLab/IsaacSim workspace first, then install ProtoMotions with IsaacLab requirements and NVIDIA package index | Isaac Sim/Kit may need EULA acceptance. Import IsaacLab before torch. |
| IsaacGym | Python 3.8; manual IsaacGym Preview 4 download and editable install, then ProtoMotions IsaacGym requirements | Legacy GPU backend, not on PyPI. Import IsaacGym before torch. |
| Genesis | Python 3.10; install Genesis stack separately, then ProtoMotions Genesis requirements | Marked experimental/untested in repo docs; verify before relying on results. |
| PyRoki retargeting | Separate Python 3.10/JAX/PyRoki environment from ProtoMotions | Retargeting convenience flows take both a ProtoMotions Python and a PyRoki Python. |

## Import ordering

For scripts that accept a simulator argument:

```python
# Parse args first, before importing torch.
from protomotions.utils.simulator_imports import import_simulator_before_torch
AppLauncher = import_simulator_before_torch(args.simulator)

import torch
```

`import_simulator_before_torch("isaacgym")` imports IsaacGym. `import_simulator_before_torch("isaaclab")` sets `OPENBLAS_NUM_THREADS=1`, validates the IsaacLab version, and returns IsaacLab `AppLauncher`. Other backends return `None`.

## Asset roots

The default portable asset root is `protomotions/data/assets`. At runtime, `protomotions.assets.get_asset_root()` resolves it relative to the installed package unless `PROTOMOTIONS_ASSET_ROOT` is set.

Set `PROTOMOTIONS_ASSET_ROOT` when:

- The installed distribution lacks an asset tree.
- You are using a package-only install but need assets from a separate Git LFS checkout.
- SMPL/SMPL-H assets are needed; they are excluded from built distributions because they carry separate license terms.

Use `protomotions info --json` to inspect the resolved asset root and backend module availability.

## Minimum safe inspection

A safe CPU/package inspection does not prove GPU simulator runtime. It can prove:

- package metadata exists;
- imports and factories work;
- CLI parsers load;
- MuJoCo/ONNX dependencies import;
- config objects can be constructed.

It cannot prove IsaacGym, IsaacLab, Newton, Genesis, GPU training, PyRoki/JAX retargeting, or real-robot deployment. Keep those as backend-specific verification tasks.
