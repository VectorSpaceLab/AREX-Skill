# Habitat-Lab Installation Reference

## When To Read

Read this before recommending package installation, debugging imports, or deciding whether a user needs the core Lab package, Baselines, HITL, Habitat-Sim, PyTorch, or graphics support.

## Package Layout

| Distribution | Import | Use |
| --- | --- | --- |
| `habitat-lab` | `habitat` | Core configs, datasets, tasks, Env/RLEnv, Gym wrappers, registry, simulator integration |
| `habitat-baselines` | `habitat_baselines` | RL/IL trainers, policies, Hydra train/eval CLI, benchmark config families |
| `habitat-hitl` | `habitat_hitl` | Human-in-the-loop GUI/web/VR app framework and interactive services |
| `habitat-sim` | `habitat_sim`, `magnum` | Simulator backend, rendering, physics/Bullet, scene assets |

The three repo distributions were version `0.3.3` when this skill was generated.

## Recommended Public Install Order

```bash
conda create -n habitat python=3.9 cmake=3.14.0
conda activate habitat
conda install habitat-sim withbullet -c conda-forge -c aihabitat
pip install -e habitat-lab
pip install -e habitat-baselines  # optional: training/evaluation
pip install -e habitat-hitl       # optional: HITL apps
```

Install `habitat-baselines` only when the task involves training, evaluation, checkpoints, trainer configs, policies, or `habitat-baselines` CLI. Install `habitat-hitl` only when the task involves realtime HITL apps or viewers.

## Why Python 3.9 Matters

The README documents Python 3.9 and Habitat-Sim conda packages. During generation, a Python 3.11 core package install succeeded but `import habitat` failed because `magnum`/`habitat_sim` was missing; the available `habitat-sim 0.3.3` conda package matched Python 3.9. If users hit `ModuleNotFoundError: No module named 'magnum'` or `No module named 'habitat_sim'`, check Python and Habitat-Sim compatibility before changing Habitat-Lab code.

## Optional Dependencies

- Baselines pull in PyTorch, TensorBoard, movie/video dependencies, LMDB/WebDataset, and optional distributed training packages.
- HITL pulls in `websockets`, `aiohttp`, Hydra, Habitat-Sim graphics/physics modules, and may need a display or browser/client runtime.
- Interactive examples can need `pygame` and `pybullet`.
- Full simulator execution needs scene assets and task episode datasets under the expected `data/` layout.

## Minimal Import Check

```python
import habitat
print(habitat.__version__)

from habitat.config.default import get_config
cfg = get_config("benchmark/nav/pointnav/pointnav_habitat_test.yaml")
print(cfg.habitat.environment.max_episode_steps)
```

For Baselines:

```python
from habitat_baselines.config.default import get_config
cfg = get_config("pointnav/ppo_pointnav_example.yaml")
print(cfg.habitat_baselines.trainer_name)
```

For HITL:

```python
import habitat_hitl
from habitat_hitl.core import hitl_main
print(habitat_hitl.__version__)
```
