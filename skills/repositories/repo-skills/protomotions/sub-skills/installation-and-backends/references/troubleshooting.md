# Installation/backend troubleshooting

## Missing optional backend modules

`protomotions info --json` reports simulator modules by import availability. `false` for IsaacGym, IsaacLab, Newton, or Genesis usually means that backend stack was not installed. Do not repair by installing all extras; choose the environment for the intended backend.

## Import-order crashes

IsaacGym and IsaacLab require import before torch. If a custom script imports torch first, restructure it:

```python
# parse args here
from protomotions.utils.simulator_imports import import_simulator_before_torch
AppLauncher = import_simulator_before_torch(args.simulator)
import torch
```

## Headless warnings

A GLFW/X11 warning on import can appear when MuJoCo or dm-control imports GLFW on a server. If the task is only package inspection, a warning is acceptable when the command exits zero. If the task requires rendering, set up an appropriate display/EGL/Kit headless mode.

## Pip conflicts

If `pip check` fails after installing a simulator extra, inspect which optional group created the conflict. ProtoMotions metadata declares conflicts among simulator extras because backend stacks pin different versions. Create a clean backend-specific env instead of repeatedly upgrading packages in place.

## Driver/CUDA mismatches

For CUDA backends, check:

```bash
nvidia-smi
python - <<'PY'
import torch
print(torch.__version__, torch.version.cuda, torch.cuda.is_available())
if torch.cuda.is_available():
    print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
    torch.empty((1,), device='cuda')
PY
```

A CPU torch import does not prove Newton, IsaacGym, or IsaacLab GPU readiness.

## Asset-root errors

If `get_asset_root()` or `asset_path()` fails:

1. Run `protomotions info --json`.
2. If package assets are incomplete, set `PROTOMOTIONS_ASSET_ROOT` to a complete asset tree.
3. If SMPL assets are needed, confirm the user has licensed local files.
4. If source checkout assets are LFS pointers, fetch the real LFS objects.
