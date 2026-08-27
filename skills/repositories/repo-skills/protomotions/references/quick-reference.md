# ProtoMotions quick reference

## Main public commands

Use installed console scripts when possible:

```bash
protomotions info --json
protomotions train-agent --robot-name g1 --simulator mujoco --experiment-path <experiment.py> --experiment-name <run> --motion-file <motions.pt> --num-envs 1 --batch-size 1024
protomotions inference-agent --checkpoint <run>/last.ckpt --simulator mujoco --num-envs 1 --headless --full-eval
```

The package also exposes `protomotions-train-agent` and `protomotions-inference-agent`, but the top-level `protomotions train-agent` and `protomotions inference-agent` routes are preferred because `protomotions info` is available beside them.

## Core Python imports

```python
from protomotions.robot_configs.factory import robot_config
from protomotions.simulator.factory import simulator_config, get_simulator_config_class
from protomotions.components.motion_lib import MotionLib, MotionLibConfig
from protomotions.envs.mdp_component import MdpComponent
from protomotions.envs.context_views import EnvContext
from protomotions.utils.simulator_imports import import_simulator_before_torch
```

For IsaacGym or IsaacLab scripts, call `import_simulator_before_torch(simulator_name)` before importing `torch` or modules that import it transitively.

## Common robot names

- `smpl`: SMPL humanoid digital human. SMPL assets require separate license handling.
- `smplx`: SMPL-X humanoid with hands. SMPL-X assets require separate license handling.
- `g1`: Unitree G1 humanoid robot; primary deployment-tracker target.
- `h1_2`: Unitree H1 v2 humanoid robot.
- `amp`: AMP humanoid.
- `soma23`: SOMA 23-body digital human.

## Simulator choices

- `isaaclab`: recommended training stack; Python 3.12 and pinned IsaacLab/IsaacSim workspace.
- `isaacgym`: legacy GPU stack; Python 3.8 and manual NVIDIA IsaacGym Preview 4 install.
- `newton`: GPU Newton 1.0 stack; Python 3.10+ with NVIDIA GPU and compatible driver.
- `mujoco`: CPU-oriented debug and deployment-validation backend; single environment for most workflows.
- `genesis`: experimental backend; use separate environment and expect weaker verification.

## Key artifact roles

- `MotionLib .pt`: packaged motion dataset containing body positions/rotations/velocities, DOF data, motion lengths, weights, and optional contact labels.
- `.motion`: single motion file used before packaging or for standalone deployment tests.
- `results/<experiment>/resolved_configs.pt`: exact training config object graph; primary resume source.
- `results/<experiment>/resolved_configs_inference.pt`: inference-time config object graph with evaluation overrides.
- `resolved_configs.yaml`: human-readable sidecar only; do not edit as source of truth.
- `last.ckpt`: full checkpoint for resume or warm start.
- `inference_last.ckpt`: small inference/share artifact for some model families; do not use it as a training-resume substitute.
- `unified_pipeline.onnx` plus `unified_pipeline.yaml`: deployment tracker model and machine-readable input/output contract.

## Sub-skill map

- Install/backend: environment separation, asset roots, backend extras, `protomotions info`.
- Simulator foundations: robot/simulator factories, terrain, scenes, tutorials, visualizers.
- Training/experiments: train/inference CLIs, configs, GPC/PEFT, domain randomization, SLURM.
- Retargeting/data: MotionLib schemas, data conversion, PyRoki, contacts, FPS, subsetting.
- Deployment/robots: ONNX export, MuJoCo contract, real-robot safety, custom robot, MJCF/USD.
