# RoboTwin install, assets, and submodules

## Environment shape

Use an isolated Python 3.10 or 3.11 environment for RoboTwin simulation. Current evidence favors Python 3.11 and these constraints:

- `torch==2.4.1` with CUDA support when running simulation/evaluation on NVIDIA GPUs.
- `numpy==1.26.4`; RoboTwin native dependencies expect the NumPy 1.x ABI.
- `sapien==3.0.0b1`, `mplib==0.2.1`, `gymnasium==0.29.1`, `transforms3d==0.4.2`, `trimesh==4.4.3`, `open3d==0.18.0`, `opencv-python==4.10.0.84`, `opencv-python-headless==4.10.0.84`, `scipy==1.10.1`.
- Data/eval packages: `h5py`, `PyYAML`, `pydantic`, `zarr`, `huggingface_hub`, `websockets`, `msgpack`, `msgpack-numpy`, `rich`, `imageio`.
- SAPIEN may require `pkg_resources`; if missing with modern setuptools, use a setuptools release that still includes it.

Avoid Python 3.13 unless the compiled stack has been revalidated.

## Repository install behavior

This RoboTwin revision is not a normal pip-installable Python distribution: there is no `setup.py` or `pyproject.toml`. Most workflows run from the RoboTwin workspace root so local directories such as `envs/`, `scripts/`, and `description/` are importable by relative path.

Practical consequences:

- Use workspace-relative commands for RoboTwin scripts.
- Do not expect `python -m pip install -e .` to work.
- For programmatic inspection, run from the workspace root or set `PYTHONPATH` to the workspace root in the user's environment; do not bake local paths into reusable code.
- If you only have the generated skill tree, run the generated skill's `scripts/robotwin_workspace.py bootstrap` entry point to materialize a pinned public workspace, then run `scripts/check_robotwin_prereqs.py` against that workspace before any source-tree workflow.

## Assets

RoboTwin simulation and task imports need downloaded assets. Missing assets can block even simple `envs` imports because cluttered-table utilities read object metadata during import.

Required asset categories:

- `assets/objects/` including Objaverse metadata such as `assets/objects/objaverse/list.json` and `assets/objects/same.json`.
- `assets/embodiments/` containing robot URDF/SRDF/config files.
- `assets/background_texture/` when random backgrounds are used.

Asset download/extract commands can be large and network-heavy. Run them only when the user intends to simulate, collect demonstrations, or evaluate policies.

## XPolicyLab submodule

RoboTwin 2.0 shares policy evaluation/deployment through XPolicyLab. A fresh workspace should clone recursively, or initialize the submodule later:

```bash
git submodule update --init --recursive XPolicyLab
```

The updater script can fetch the latest configured XPolicyLab branch and optionally stage/install the submodule pin. Treat it as a mutating operation:

```bash
bash scripts/update_xpolicylab.sh          # fetch and update submodule working tree
bash scripts/update_xpolicylab.sh --stage  # also stage the gitlink
bash scripts/update_xpolicylab.sh --install  # also pip install XPolicyLab into the current env
```

Do not run update/stage/install modes unless the user wants to mutate the workspace or environment.

## Quick setup validation

1. Dependency imports:

   ```bash
   python - <<'PY'
   import numpy, torch, sapien, mplib, open3d, gymnasium, transforms3d, cv2, h5py, yaml
   print('imports ok', numpy.__version__, torch.__version__)
   PY
   ```

2. CUDA smoke when GPU simulation is required:

   ```bash
   python - <<'PY'
   import torch
   print(torch.cuda.is_available(), torch.cuda.device_count())
   if torch.cuda.is_available():
       print(torch.cuda.get_device_name(0), torch.cuda.get_device_capability(0))
       torch.empty((1,), device='cuda')
   PY
   ```

3. Render smoke: use the bundled `simulation-core/scripts/check_render_smoke.py`.
4. Asset smoke: confirm required asset metadata files and embodiment directories exist before importing `envs`.
5. XPolicyLab smoke for evaluation: confirm `XPolicyLab/setup_policy_server.py` and `XPolicyLab/policy/<policy_name>/` exist.
