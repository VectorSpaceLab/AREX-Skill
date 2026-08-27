# API Registry

## When to read

Read this when you need a verified inventory of robosuite's public registries, loaders, wrappers, and common helper signatures before routing into a sub-skill.

## Registries verified for this skill

### Environments

`Door`, `Lift`, `NutAssembly`, `NutAssemblyRound`, `NutAssemblySingle`, `NutAssemblySquare`, `PickPlace`, `PickPlaceBread`, `PickPlaceCan`, `PickPlaceCereal`, `PickPlaceMilk`, `PickPlaceSingle`, `Stack`, `ToolHang`, `TwoArmHandover`, `TwoArmLift`, `TwoArmPegInHole`, `TwoArmTransport`, `Wipe`.

### Robots

`Baxter`, `GR1`, `GR1ArmsOnly`, `GR1FixedLowerBody`, `GR1FloatingBody`, `IIWA`, `Jaco`, `Kinova3`, `LeggedManipulatorModel`, `Panda`, `PandaDexLH`, `PandaDexRH`, `PandaOmron`, `Sawyer`, `SpotArm`, `SpotWithArm`, `SpotWithArmFloating`, `Tiago`, `UR5e`, `XArm7`.

### Grippers

`RethinkGripper`, `PandaGripper`, `JacoThreeFingerGripper`, `JacoThreeFingerDexterousGripper`, `WipingGripper`, `Robotiq85Gripper`, `Robotiq140Gripper`, `RobotiqThreeFingerGripper`, `RobotiqThreeFingerDexterousGripper`, `BDGripper`, `InspireLeftHand`, `InspireRightHand`, `FourierLeftHand`, `FourierRightHand`, `XArm7Gripper`, `SuctionGripper`, and `None` for no gripper.

### Bases

`FloatingLeggedBase`, `NoActuationBase`, `NullBase`, `NullMobileBase`, `NullMount`, `OmronMobileBase`, `RethinkMinimalMount`, `RethinkMount`, `Spot`, `SpotFloating`.

### Controllers

Part controllers: `IK_POSE`, `JOINT_POSITION`, `JOINT_TORQUE`, `JOINT_VELOCITY`, `OSC_POSE`, `OSC_POSITION`.

Composite controllers: `BASIC`, `HYBRID_MOBILE_BASE`, `WHOLE_BODY_COMPOSITE`, `WHOLE_BODY_IK`.

`WHOLE_BODY_MINK_IK` can be registered by importing the optional Mink example when `mink` is installed; it was not part of the verified core environment.

## Core constructors and helpers

### Environment construction

```python
robosuite.make(env_name, *args, **kwargs)
```

Creates a registered robosuite environment by name.

Important constructor layers:

```python
MujocoEnv(
    has_renderer=False,
    has_offscreen_renderer=True,
    render_camera="frontview",
    render_collision_mesh=False,
    render_visual_mesh=True,
    render_gpu_device_id=-1,
    control_freq=20,
    lite_physics=True,
    horizon=1000,
    ignore_done=False,
    hard_reset=True,
    load_model_on_init=True,
    renderer="mjviewer",
    renderer_config=None,
    seed=None,
)
```

```python
RobotEnv(
    robots,
    env_configuration="default",
    base_types="default",
    controller_configs=None,
    initialization_noise=None,
    use_camera_obs=True,
    has_renderer=False,
    has_offscreen_renderer=True,
    render_camera="frontview",
    control_freq=20,
    horizon=1000,
    ignore_done=False,
    camera_names="agentview",
    camera_heights=256,
    camera_widths=256,
    camera_depths=False,
    camera_segmentations=None,
    robot_configs=None,
    renderer="mjviewer",
    seed=None,
)
```

Task constructors such as `Lift` add task-specific options like `gripper_types`, `use_object_obs`, `reward_scale`, `reward_shaping`, table settings, and placement samplers.

### Controller loaders

```python
from robosuite.controllers import load_composite_controller_config, load_part_controller_config

config = load_composite_controller_config(controller=None, robot="Panda")
basic = load_composite_controller_config(controller="BASIC")
part = load_part_controller_config(default_controller="OSC_POSE")
```

### Robot and gripper helpers

```python
from robosuite.models.grippers import gripper_factory
from robosuite.utils.robot_composition_utils import create_composite_robot

gripper = gripper_factory("PandaGripper")
Custom = create_composite_robot("CustomPanda", robot="Panda", base="RethinkMount", grippers="PandaGripper")
```

### Wrappers

```python
DataCollectionWrapper(env, directory, collect_freq=1, flush_freq=100, use_env_xml_for_reset=False)
DemoSamplerWrapper(env, demo_path, need_xml=False, num_traj=-1, sampling_schemes=("uniform", "random"), scheme_ratios=(0.9, 0.1), ...)
DomainRandomizationWrapper(env, seed=None, randomize_color=True, randomize_camera=True, randomize_lighting=True, randomize_dynamics=True, ...)
VisualizationWrapper(env, indicator_configs=None)
GymWrapper(env, keys=None, flatten_obs=True)
```

### Observables and camera utilities

```python
Observable(name, sensor, corrupter=None, filter=None, delayer=None, sampling_rate=20, enabled=True, active=True)
```

```python
get_camera_transform_matrix(sim, camera_name, camera_height, camera_width)
project_points_from_world_to_camera(points, world_to_camera_transform, camera_height, camera_width)
transform_from_pixels_to_world(pixels, depth_map, camera_to_world_transform)
get_real_depth_map(sim, depth_map)
```

## Runtime facts verified

- `Lift` + `Panda` can be created headlessly without camera observations and reports `action_dim == 7`.
- `Lift` + `Panda` with `MUJOCO_GL=egl`, offscreen renderer, and `agentview` camera can return an RGB image observation.
- `GymWrapper` can wrap a `Lift` + `Panda` env and return Gymnasium-style reset/step tuples when `gymnasium` is installed.

## Do not overclaim

Do not claim these as verified core runtime capabilities unless a later workflow explicitly verifies them:

- external `robosuite_models`
- SpaceMouse / DualSense HID hardware
- optional `mink` whole-body controller example
- USD / Isaac / Omniverse rendering
- on-screen viewer operation on a headless host
