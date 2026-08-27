---
name: installation-and-backends
description: "Install, inspect, and troubleshoot ProtoMotions package
  environments and simulator backend variants."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ProtoMotions installation and backends

Use this sub-skill when the task is about installing ProtoMotions, choosing simulator extras, verifying package imports, resolving assets, or diagnosing backend availability.

## Read first

- `references/backend-matrix.md`: per-backend Python, dependency, and hardware rules.
- `references/package-assets.md`: package-vs-source asset behavior and `PROTOMOTIONS_ASSET_ROOT` handling.
- `references/troubleshooting.md`: install, import, backend, and asset failures.
- Root `../../scripts/inspect_protomotions_install.py`: safe JSON inspection script for an existing environment.

## Decision flow

1. Identify the requested workflow and backend. Do not install all optional extras.
2. If the task only needs package inspection or config generation, a CPU/MuJoCo-capable environment is often enough.
3. If the task needs real simulator execution, choose a backend-specific environment:
   - IsaacGym: Python 3.8 + manual IsaacGym Preview 4.
   - IsaacLab: Python 3.12 + pinned IsaacLab/IsaacSim workspace.
   - Newton: CUDA torch + Newton/Warp stack on NVIDIA GPU.
   - MuJoCo: CPU/debug/deploy validation, usually Python 3.10+.
   - Genesis: separate experimental environment.
   - PyRoki retargeting: separate JAX/PyRoki environment.
4. Verify with `protomotions info --json`, `protomotions train-agent --help`, and the bundled inspection script before running examples.
5. If assets fail, inspect `PROTOMOTIONS_ASSET_ROOT`, Git LFS state, and SMPL/SMPL-H license carve-outs before changing code.

## Environment rules

- Never mutate a user's Conda base environment for ProtoMotions.
- Prefer one environment per simulator backend because optional dependencies conflict.
- Install torch/backend foundations first when the backend requires a specific CUDA or Python stack.
- For IsaacGym/IsaacLab, preserve import order: backend before torch.
- Treat `protomotions info` reporting a module unavailable as a dependency-selection signal, not a package failure.

## Good first checks

```bash
python -m pip check
protomotions info --json
protomotions train-agent --help
protomotions inference-agent --help
python ../../scripts/inspect_protomotions_install.py --json
```

When a task provides an existing traceback, classify it before acting: package metadata, import order, asset root, backend dependency, hardware/driver, config/checkpoint, or headless rendering.
