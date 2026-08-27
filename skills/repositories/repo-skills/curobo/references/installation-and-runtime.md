# Installation and runtime contract

## Supported baseline

The current v2 package metadata requires Python `>=3.10`; the installation guide
validates Ubuntu 20.04+ and an NVIDIA GPU newer than Turing with at least 4 GB
VRAM. It documents driver `>=580.65.06` for current CUDA 12+ use and recommends
Python 3.11. Choose the CUDA extra matching the driver/runtime:

```bash
uv venv --python 3.11
uv pip install .[cu12-torch]  # fresh install, CUDA 12
uv pip install .[cu13-torch]  # fresh install, CUDA 13
uv pip install .[cu12]        # existing compatible PyTorch
uv pip install .[cu13]        # existing compatible PyTorch
```

The package distribution is `nvidia-curobo`, while the import package is
`curobo`. The base requirements include `numpy`, `scipy`, `networkx`, `pyyaml`,
`trimesh`, `yourdfpy`, `viser`, `warp-lang`, and numerical/UI support. The
`cu12-torch` and `cu13-torch` extras add CUDA Python runtime components and
PyTorch; the non-torch variants assume PyTorch is already installed. The
`pybind` extra is for deprecated compiled-extension mode, `usd` enables USD
support, and `doc`/`benchmark` are not core runtime requirements.

## Device and tensor rules

Public configs default to a CUDA `DeviceCfg` with `float32`. Create tensors on
the same device as the robot/solver. On shared hosts, set an explicit
`CUDA_VISIBLE_DEVICES` or pass a `DeviceCfg(device=torch.device("cuda:N"))`.
Always run a tiny allocation first:

```python
import torch
assert torch.cuda.is_available()
device = torch.device("cuda:0")
probe = torch.zeros(1, device=device, dtype=torch.float32)
```

A CPU probe establishes import and pure data-structure behavior only. It is not
a substitute for FK, Warp geometry, collision kernels, IK, trajectory
optimization, MPC, or mapping kernels.

## CUDA graphs and resource use

`use_cuda_graph=True` is the normal performance path and is the documented
default for the public config factories. Graph capture needs stable tensor
shapes and may require reset/rebuild after changing batch size or solver shape.
Use `use_cuda_graph=False` only for a focused debug/test run. Large seed counts,
`max_batch_size`, high-DoF self-collision spheres, mapper extents, and multiple
parallel environments are the dominant memory drivers.

## v1 boundary

The README states that cuRoboV2 is a significant rewrite with a changed public
API. If a request specifically requires the v1 API, use the documented v0.7.8
pin and do not apply these v2 config names or result contracts.
