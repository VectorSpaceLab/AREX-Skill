# Benchmark and Integration Workflows

## Portable benchmark metadata

RoboVerse's benchmark metadata separates task, scene, robot, and teleoperation
selection. `BenchmarkTaskSpec` contains `name`, `family`, `description`, a
`BenchmarkSceneSpec`, supported simulators and robots, `default_robot`, robot
profiles, and aliases. `BenchmarkSceneSpec` contains objects, camera presets,
and physics hints. A robot profile contains control joint count, named joint
slices, and body names.

`BenchmarkTaskSpec` validates that the default robot is supported and every
supported robot has a profile. `robot_profile(robot=None)` selects the default;
an unsupported robot raises a `ValueError` listing supported robots.
`get_benchmark_task_spec(name)` accepts canonical names, aliases, and a
convenient `benchmark.` prefix; unknown names raise a `KeyError` listing
available tasks. Use `list_benchmark_task_specs()` for discovery.

```python
from roboverse_pack.benchmark import get_benchmark_task_spec, list_benchmark_task_specs
print(list_benchmark_task_specs())
spec = get_benchmark_task_spec("cube_reach")
profile = spec.robot_profile()
```

Use metadata validation before choosing a native simulator or teleoperation
path.

## Integration decision tree

1. **Metadata only:** validate task/robot/scene/camera declarations and use a
   synthetic or local fixture. No external package or data is needed.
2. **Conversion:** validate one local trajectory/demo and preserve format
   version, time order, action/observation keys, camera names, and task identity.
3. **Replay/passthrough:** install the selected native stack, check assets and
   version compatibility, then reset/replay one episode headlessly.
4. **Parity/render/evaluation:** align state, action convention, control rate,
   camera and seed; run one bounded rollout before a sweep. Record backend and
   measured deltas.
5. **Large benchmark/training:** require explicit data, storage, GPU/display,
   credentials, and runtime budget. It is not a default verification case.

## External families

- LIBERO: task names, assets, native task implementation, and passthrough must
  be version-aligned; empty trajectories and asset bundles need explicit tests.
- ManiSkill: native controller/action levels, friction/contact and success
  semantics are not interchangeable with MetaSim defaults; preserve the native
  backend requirement.
- MJLab: configuration, reward/MDP terms, asset locator, and MuJoCo backend
  version must be aligned.
- robosuite: controller, joint order, rendering, and native asset assumptions
  require a separate install and parity check.
- RobotWin: locators, URDF instances, multi-camera demos, and conversion are
  often data/asset dependent; validate path logic with fixtures first.
- SimplerEnv: native controller/task stack is vendored or external in parts;
  passthrough does not imply the native backend is installed.

The integration tools are source evidence and diagnostics, not runtime
requirements. Avoid running sweeps, downloads, vendor/asset generation, or
external policy servers as a generic smoke test.
