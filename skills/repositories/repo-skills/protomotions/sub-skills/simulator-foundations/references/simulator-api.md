# Simulator and environment API notes

## Import-order skeleton

```python
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--simulator", required=True)
args = parser.parse_args()

from protomotions.utils.simulator_imports import import_simulator_before_torch
AppLauncher = import_simulator_before_torch(args.simulator)

import torch
```

Use this structure for custom scripts that support IsaacGym or IsaacLab. Parser construction is safe before backend import; torch import is not.

## Factory basics

```python
from protomotions.robot_configs.factory import robot_config
from protomotions.simulator.factory import simulator_config, get_simulator_config_class

robot_cfg = robot_config("g1")
sim_cfg = simulator_config(
    "mujoco",
    robot_cfg,
    headless=True,
    num_envs=1,
    experiment_name="debug",
)
print(get_simulator_config_class("mujoco").__name__)
```

`robot_config(name)` raises `ValueError` for unknown names. Valid names in the distilled snapshot include `smpl`, `smplx`, `amp`, `g1`, `h1_2`, and `soma23`.

## Base composition

ProtoMotions environments are composed rather than monolithic:

- Robot config: kinematics, asset, controls, body-name mappings, simulator params.
- Simulator config: backend-specific runtime target and simulation settings.
- Terrain config: flat or procedural terrain.
- Scene library: empty scenes, primitive/mesh objects, object options, replication/subset logic.
- Motion library: packaged motions or empty library.
- Env config: observation components, reward components, termination components, control components, reset behavior.
- Agent config: PPO, mimic, AMP, ASE, ADD, supervised, GPC/PEFT, or other learning algorithm settings.

## MDP component pattern

An `MdpComponent` binds a pure tensor function to dynamic context paths and static parameters. This makes dependencies explicit and testable:

```python
from protomotions.envs.context_views import EnvContext
from protomotions.envs.mdp_component import MdpComponent

component = MdpComponent(
    compute_func=my_tensor_kernel,
    dynamic_vars={"current_pos": EnvContext.current.rigid_body_pos},
    static_params={"weight": 1.0},
)
```

Use this pattern when adding custom observations, rewards, or terminations. Prefer pure kernels so unit tests can run without a simulator.

## Simulator switching at inference

The inference path can update simulator config target/default fields when switching backend names. This is useful for MuJoCo debug or sim2sim checks, but physical transfer depends on policy training and robot representation. Do not claim cross-sim compatibility solely because the config object can be switched.
