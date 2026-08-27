# Simulation API and Configuration Notes

## Ownership and imports

`roboverse_pack` is the downstream content package. MetaSim owns `ScenarioCfg`,
`configclass`, handlers, simulator backends, task registry, state types, and
Gym integration. RoboVerse exposes content modules such as:

```python
from roboverse_pack.robots import franka_cfg, go2_cfg
from roboverse_pack.scenes import base_scene_cfg
from roboverse_pack.grounds import gap_cfg, pit_cfg, slope_cfg, stair_cfg, stone_cfg
from roboverse_pack.queries import ContactForces, SitePos, SensorData
```

Names vary by module; inspect the selected module's public symbols before
writing a new import. The package's `metasim.toml` declares `roboverse_pack` as
a discovered MetaSim package root.

## Config composition checklist

A scenario normally combines:

- a robot/articulation config;
- rigid or articulated objects with a `PhysicStateType` and pose;
- optional scene/ground configuration;
- cameras and sensor/query declarations;
- simulation parameters and a selected handler/backend.

Use MetaSim's `@configclass` decorator for configuration classes. Prefer
composing an existing `.Cfg` object and overriding a field over duplicating the
class. Treat config values as immutable declarations once passed to an
environment unless the MetaSim API explicitly supports mutation.

Before running:

1. Confirm every configured asset path is packaged, downloaded intentionally, or
   available in the target environment.
2. Confirm body/joint/site names against the selected robot/model.
3. Confirm camera resolution and renderer compatibility.
4. Confirm observation/action shapes after reset and one bounded step.
5. Confirm the chosen backend supports the asset format and query implementation.

## Queries and optional sensors

RoboVerse's query modules bridge MetaSim query types across handlers. Contact
and site queries may expose backend-specific tensor conversion. Lidar is not a
base import-only feature: its documented implementation may require a lidar
sensor, Warp, and trimesh. Treat absent optional dependencies as an explicit
capability error, not as valid zero data.

## Teleoperation and transforms

`roboverse_pack.teleop` contains control-flow, transforms, hand retargeting,
and shared teleoperation helpers. Before using a teleop profile, resolve the
benchmark/task robot profile and verify the control joint count and slices.
Interactive devices, real-time input, and real robots are separate safety
boundaries; first validate transforms with recorded or synthetic poses.

## Live inspection commands

Use the prepared environment or the user's target environment:

```bash
python -c "import roboverse_pack, metasim; print('imports ok')"
python - <<'PY'
import inspect
from roboverse_pack.benchmark import BenchmarkTaskSpec
print(inspect.signature(BenchmarkTaskSpec))
PY
```

Do not copy local `__file__` paths or environment names into public reports.
