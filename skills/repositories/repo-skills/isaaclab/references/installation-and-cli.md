# Installation and CLI

This reference summarizes the user-facing install and wrapper commands for Isaac Lab.

## Package layout

- Core submodules installed by `./isaaclab.sh -i`:
  - `isaaclab`
  - `isaaclab_ppisp`
  - `isaaclab_assets`
  - `isaaclab_contrib`
  - `isaaclab_experimental`
  - `isaaclab_newton`
  - `isaaclab_ov`
  - `isaaclab_ovphysx`
  - `isaaclab_physx`
  - `isaaclab_rl`
  - `isaaclab_tasks`
  - `isaaclab_tasks_experimental`
  - `isaaclab_visualizers`
- Optional submodules:
  - `mimic`
  - `teleop`
- Extra feature selectors:
  - `contrib[rlinf]`
  - `newton`
  - `ov[ovrtx|ovphysx|all]`
  - `rl[rsl-rl|skrl|sb3|rl-games]`
  - `visualizer[kit|newton|rerun|viser]`
- Special install values:
  - `all` — core packages plus optional submodules and the automatic extra features `newton`, `rl`, and `visualizer`
  - `core` — core packages only
  - `isaacsim` — request the Isaac Sim pip package when the full stack is needed

## Wrapper commands

- `./isaaclab.sh --help` or `./isaaclab.bat --help` shows the repo wrapper commands.
- `./isaaclab.sh -p <python args>` runs Python inside the selected Isaac Lab environment.
- `./isaaclab.sh train ...` and `./isaaclab.sh play ...` dispatch the reinforcement learning entrypoints.
- `./isaaclab.sh -t` runs tests.
- `./isaaclab.sh -f` runs formatting and lint hooks.
- `./isaaclab.sh -d` builds the docs.
- `./isaaclab.sh -n ...` scaffolds a new project or internal task.
- `./isaaclab.sh -c [name]` and `./isaaclab.sh -u [name]` create Conda or uv environments.

## Minimal verification

Run these checks after installation:

```bash
python -m pip check
python -I -c "import isaaclab, isaaclab_tasks, isaaclab_assets"
./isaaclab.sh --help
```

If CUDA packages are installed, also verify that PyTorch can see the GPU:

```bash
python -I -c "import torch; print(torch.cuda.is_available(), torch.cuda.device_count())"
```

## Practical notes

- Prefer `./isaaclab.sh` for repo-aware installs and runtime commands.
- Use `--viz none` or omit `--viz` for headless runs; `--headless` still exists for compatibility but is deprecated.
- Quote bracketed install selectors on shells that treat brackets specially, for example `./isaaclab.sh -i 'rl[rsl-rl]'`.
- Use `./isaaclab.sh -i core` when you need a light install for core packages and bundled helpers.
