# Runtime prerequisites and verification boundary

## README installation facts

The repository README states the following intended simulation setup:

1. Install PyTorch `1.10.0+cu113`, `torchvision 0.11.1+cu113`, and
   `torchaudio 0.10.0+cu113` from the CUDA 11.3 wheel index.
2. Download Isaac Gym Preview 4 from NVIDIA, unpack it, and install its
   Python package from `isaacgym/python` with `pip install -e .`.
3. Verify Isaac Gym separately with an Isaac Gym example.
4. Install this repository with `pip install -e .`.
5. On a separately approved target checkout, run a bounded native simulator
   smoke adapted from the repository test; the expected progress signal is
   `Simulating step {i}`. Keep it headless unless display execution is
   explicitly required. The generated skill does not bundle or invoke that
   source launcher.

The README recommends at least 10 GB VRAM for default simulated training and
says the default training configuration uses approximately 12 GB. It suggests
reducing `Cfg.env.num_envs` on a smaller GPU. Those are upstream guidance,
not measurements made by this skill.

The package's declared install requirements include `ml_logger==0.8.117`,
`ml_dash==0.3.20`, `jaynes>=0.9.2`, `params-proto==2.10.5`, `gym>=0.14.0`,
`tqdm`, `matplotlib`, and `numpy==1.23.5`. The Isaac Gym package and the
pinned PyTorch build are not declared in `setup.py` and must be treated as a
separate prerequisite layer.

## PyTorch is not Isaac Gym

These checks answer different questions:

- A PyTorch import checks only that the installed PyTorch package can load.
- `torch.cuda.is_available()` checks PyTorch's CUDA discovery path and may
  report `False` because of drivers, the wheel, environment variables, or no
  GPU; it does not test PhysX, Isaac Gym tensor bindings, asset loading,
  viewer creation, or simulator stepping.
- Finding or importing the `isaacgym` Python package checks package visibility
  only. It does not create a gym, call `create_sim`, load a URDF, or exercise
  the GPU pipeline.
- A simulator runtime check requires Isaac Gym Preview 4, compatible NVIDIA
  driver/CUDA components, a supported GPU, the repository dependencies, the
  Go1 assets, and a separate execution of an approved environment test.

This host intentionally does not contain Isaac Gym Preview 4. Consequently,
this sub-skill must report the simulator runtime as **unverified** and must
not launch `scripts/test.py`, `VelocityTrackingEasyEnv`, `HistoryWrapper`,
training, playback, or rendering here.

## Read-only diagnostic

Run the bundled helper from any working directory by giving its explicit path;
use `--repo-root` only when checking assets in a caller-owned checkout:

```bash
python /path/to/this-skill/sub-skills/simulation-environment/scripts/check_runtime.py \
  --repo-root /path/to/caller-owned-checkout
```

The script does not use the repository's Python modules, does not launch a
simulation, and does not write files. It reports:

- installed `go1_gym` distribution metadata when available;
- whether an `isaacgym` module can be found/imported, with exception text if
  import fails;
- whether PyTorch is installed and what `torch.cuda.is_available()` reports;
- required Go1 URDF/mesh paths and the optional actuator-network asset;
- URDF-relative mesh references and their existence under `--repo-root`.

An absent Isaac Gym or CUDA backend is reported as an optional/unverified
condition by default. Use `--require-isaacgym` or `--require-cuda` only on a
machine intended to satisfy that prerequisite; use `--strict-assets` to make
missing required Go1 assets a nonzero result. No option starts simulation.

## Asset contract checks

The Go1 configuration resolves
`{MINI_GYM_ROOT_DIR}/resources/robots/go1/urdf/go1.urdf`. The URDF references
meshes relative to its own directory, including `../meshes/trunk.stl`,
`hip.stl`, `thigh.stl`, `thigh_mirror.stl`, and `calf.stl`. The static checker
also reports `resources/actuator_nets/unitree_go1.pt`; it is required for the
`actuator_net` control path, but not for the Go1 `config_go1` default `P`
path. Asset existence does not certify that Isaac Gym can parse or load the
asset.

## What cannot be verified here

- Isaac Gym Preview 4 installation or binary compatibility.
- PhysX simulation, GPU pipeline, simulator stepping, reset behavior, reward
  behavior, terrain generation, viewer/rendering, or camera output.
- The runtime assertion that privileged-observation width equals
  `Cfg.env.num_privileged_obs`.
- VRAM sufficiency, performance, stable headless execution, and any training
  or playback result.
- Compatibility of a locally installed package with the repository's old
  PyTorch/CUDA versions.
