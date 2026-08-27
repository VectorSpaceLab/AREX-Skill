# Simulation Workflow Recipes

## Install and backend selection

The distribution is `roboverse-py`; imports use `roboverse_pack` and upstream
`metasim`. Install only the selected route:

```bash
python -m pip install -e ".[mujoco]"
# add [dev] for focused tests or [examples] for tutorial helpers
python -c "import roboverse_pack, metasim; print('imports ok')"
```

The backend extras are MetaSim variants. Isaac Sim/Gym, Genesis, Newton,
SAPIEN, PyBullet, MJX, and related paths may require vendor runtimes, GPU,
display, or separate processes. A CPU import does not verify them.

## Scenario composition

Use the upstream config types and RoboVerse content:

```python
from metasim.constants import PhysicStateType
from metasim.scenario.cameras import PinholeCameraCfg
from metasim.scenario.objects import PrimitiveCubeCfg
from metasim.scenario.scenario import ScenarioCfg
from metasim.utils.setup_util import get_handler

scenario = ScenarioCfg(
    robots=["franka"], simulator="mujoco", num_envs=1, headless=True,
    cameras=[PinholeCameraCfg(width=320, height=240, pos=(1.5, -1.5, 1.5), look_at=(0, 0, 0))],
    objects=[PrimitiveCubeCfg(name="cube", size=(0.1, 0.1, 0.1), physics=PhysicStateType.RIGIDBODY)],
)
handler = get_handler(scenario)
try:
    handler.simulate()
    state = handler.get_states(mode="tensor")
finally:
    handler.close()
```

The exact config fields are versioned upstream APIs. Inspect live signatures
before using unfamiliar fields. Compose existing `RobotCfg`, scene, ground,
asset, camera, and query objects; do not duplicate MetaSim core classes.

## Content and observation checklist

- Import robot configs from `roboverse_pack.robots`; verify joint/body names,
  asset format, limits, actuators, and initial pose.
- Import scenes or grounds from `roboverse_pack.scenes` and
  `roboverse_pack.grounds`; use a primitive fixture before external assets.
- Add cameras with `PinholeCameraCfg`; validate dimensions, pose, and mount link.
- Use `roboverse_pack.queries` for contacts, sites, sensors, or lidar. Lidar may
  need Warp, trimesh, and a backend sensor implementation.
- Apply randomization only after deterministic reset/step works. Seed Python,
  NumPy, Torch, and the environment as appropriate.
- Teleoperation and real-time devices are a separate boundary. Validate packet,
  calibration, transforms, and joint slices with recorded/synthetic input first.

## Safe progression

1. Import and discover the selected task or package.
2. Build one headless environment and reset it.
3. Step a zero/bounded action; assert observation, reward, termination, and
   truncation shapes.
4. Increase environment count or add robots only after the one-env contract.
5. Add rendering, replay, motion planning, cameras, teleoperation, and external
   assets one at a time, with a timeout and explicit backend prerequisites.

A rollout or rendered image is evidence for the selected backend only. Use the
parity route for measured cross-simulator comparisons.
