# Installation, Package Identity, and Boundaries

## Package facts

- Distribution: `roboverse-py`, version `1.0.0b0` at the captured source commit.
- Import roots: `roboverse_pack` and `roboverse_learn`.
- Upstream dependency: `metasim` from the public RoboVerseOrg MetaSim project.
- Package discovery: `metasim.toml` declares `roboverse_pack` as a MetaSim package root.
- Supported Python metadata: `>=3.8`; use a version supported by the selected
  simulator and learning wheels (Python 3.11 is a practical inspection choice).

## Install variants

The base package depends on MetaSim, Gymnasium, Loguru, NumPy, PyYAML, SciPy,
and Torch. Public extras include:

- `dev`: pytest, coverage, Ruff, and MetaSim development dependencies;
- `examples`: image/video, OpenCV, pygame, rich, Stable-Baselines3, torchvision,
  tqdm, and CLI helpers;
- `learn`: broad RL/IL/data/training dependencies;
- `vla`: LeRobot, TensorFlow, TensorFlow Datasets/Hub, and Transformers;
- `mujoco`, `pybullet`, `sapien2`, `sapien3`, `genesis`, `isaacgym`,
  `isaacsim`, `newton`, `mjx`, and other MetaSim backend extras.

Install the smallest extra set for the selected route:

```bash
python -m pip install -e ".[mujoco]"
python -m pip install -e ".[dev,mujoco]"       # focused development checks
python -m pip install -e ".[learn,mujoco]"     # only for selected learning APIs
python -m pip install -e ".[vla,mujoco]"       # large, model/data-dependent path
```

Do not mix incompatible backend variants casually in one environment. Follow
the MetaSim backend's own documented system/runtime requirements.

## Ownership boundary

RoboVerse owns tasks, robots, scenes, grounds, assets, callbacks, queries and
randomization extensions, teleoperation metadata, benchmark adapters, learning
code, examples, and repository tools. MetaSim owns the core simulator
abstractions, config types, registry, handlers, package discovery, and backend
implementations. For a missing core capability, draft or land the MetaSim
change first, then consume it here. Do not duplicate core types downstream.

## Safe install verification

```bash
python -m pip check
python -c "import roboverse_pack, metasim, gymnasium; print('package imports OK')"
```

A successful import does not verify assets, renderers, native simulators, VLA
models, external benchmark data, or cross-simulator parity. Record those as
separate backend gates.
