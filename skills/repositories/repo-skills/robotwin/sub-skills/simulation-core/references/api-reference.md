# API reference

## Task class pattern

Most RoboTwin tasks follow the same structure:

```python
class beat_block_hammer(Base_Task):
    def setup_demo(self, **kwags):
        super()._init_task_env_(**kwags)

    def load_actors(self):
        ...

    def play_once(self):
        ...

    def check_success(self):
        ...
```

Use the pattern below:

- `setup_demo`: always call `super()._init_task_env_(**kwags)`.
- `load_actors`: create the task objects, name them, and register prohibited zones when needed.
- `play_once`: compose robot actions with `move`, `grasp_actor`, `place_actor`, `move_by_displacement`, `open_gripper`, and `close_gripper`.
- `check_success`: inspect pose tolerances, actor contacts, and functional points.

### Canonical example shape

A task like `beat_block_hammer` typically:

1. chooses an arm from the object position,
2. grasps the object with a contact point,
3. moves or lifts the object if needed,
4. places it on a functional point,
5. checks success with pose/contact logic.

## `Base_Task`

`Base_Task` owns scene construction, robot/camera bootstrap, observation assembly, action execution, and picture saving.

| Method | What it does | Notes |
| --- | --- | --- |
| `_init_task_env_(...)` | Seeds numpy and torch, stores task metadata, configures randomization, creates the scene, loads robot/cameras, opens grippers, loads actors, and checks stability. | Also loads per-task eval step limits when eval mode is active. |
| `setup_scene(...)` | Creates the SAPIEN engine, renderer, scene, ground plane, default material, and lights. | Viewer creation is tied to `render_freq`. |
| `create_table_and_wall(...)` | Builds the wall and table and applies random textures when enabled. | Table height may include a task-specific bias. |
| `load_robot(...)` | Instantiates or resets the robot wrapper and initializes planners and joints. | Link masses are normalized after load. |
| `load_camera(...)` | Instantiates the camera wrapper and synchronizes render state. | Uses the camera config YAML. |
| `_update_render()` | Refreshes camera poses and render state. | Call before RGB/depth capture. |
| `get_obs()` | Returns observation, pointcloud, joint action, and endpose payloads. | Fields depend on `data_type`. |
| `move(...)` | Executes one or two arm action streams. | Two simultaneous move actions become one coordinated trajectory. |
| `take_dense_action(...)` | Interleaves arm and gripper trajectories into simulator steps. | Used internally by `move`. |
| `left_move_to_pose(...)`, `right_move_to_pose(...)`, `together_move_to_pose(...)` | Plan one-arm or dual-arm pose motions. | Returns `None` and marks planning failure when the planner fails. |
| `grasp_actor(...)` | Builds a pre-grasp + close sequence from actor contact points. | Can add a constraint pose for collision-sensitive moves. |
| `place_actor(...)` | Builds a pre-place + place + optional open sequence. | Supports functional-point placement and alignment control. |
| `move_by_displacement(...)` | Moves in world coordinates or along the current arm axis. | Useful for lift/retract steps. |
| `open_gripper(...)`, `close_gripper(...)`, `back_to_origin(...)` | Convenience helpers that return action tuples. | `back_to_origin` uses the stored original end-effector pose. |
| `check_actors_contact(...)` | Checks whether two actors are in contact. | Good for final success checks. |
| `add_prohibit_area(...)` | Adds a 2D keep-out zone derived from an actor or pose. | Helps avoid collisions and clutter overlap. |

## Robot and planner API

`Robot(scene, need_topp=False, **kwargs)` expects left and right embodiment configuration plus the robot asset root paths.

### Required inputs

- `left_embodiment_config`
- `right_embodiment_config`
- `left_robot_file`
- `right_robot_file`
- `dual_arm_embodied`
- `embodiment_dis` for separated arms

### Core responsibilities

- Load URDF/SRDF and planner configs.
- Resolve joint names, gripper joints, home states, and pose transforms.
- Support either one shared dual-arm entity or two separate arm entities.
- Build planners for path and gripper interpolation.

### Key methods

| Method | What it gives you |
| --- | --- |
| `set_planner(scene)` | Creates Curobo and/or Mplib planners for both arms. |
| `init_joints()` | Resolves active joints, cameras, end-effector joints, and grippers. |
| `move_to_homestate()` | Sends both arms to their home joint targets. |
| `set_arm_joints(...)` | Applies planned position/velocity trajectories. |
| `set_gripper(...)` | Applies normalized gripper targets. |
| `plan_grippers(...)` | Generates 200-step gripper interpolation. |
| `left_plan_path(...)`, `right_plan_path(...)` | Plans a single arm to a target pose. |
| `left_plan_multi_path(...)`, `right_plan_multi_path(...)` | Plans a batch of candidate poses. |
| `get_left_ee_pose()`, `get_right_ee_pose()` | Returns the current end-effector pose as a 7-value pose list. |
| `get_left_tcp_pose()`, `get_right_tcp_pose()` | Returns the tool-center-point pose. |
| `get_left_orig_endpose()`, `get_right_orig_endpose()` | Returns end-effector pose in the robot-origin frame. |

### Planner notes

- `need_topp=True` enables the top-level motion planning helpers.
- `communication_flag` decides whether the Curobo planner runs in-process or in a worker process.
- The planner bias and frame transforms come from the embodiment config and the robot asset metadata.
- A planning failure should be treated as a real task failure until the target pose or constraint is adjusted.

## Camera API

`Camera(bias=0, random_head_camera_dis=0, **kwags)` wires both wrist cameras and static cameras.

### Config inputs

- `camera.head_camera_type`
- `camera.wrist_camera_type`
- `camera.collect_head_camera`
- `camera.collect_wrist_camera`
- `left_embodiment_config.static_camera_list`

### Output helpers

- `get_config()` → camera intrinsics/extrinsics/model matrices.
- `get_rgb()` / `get_rgba()` → per-camera image dicts.
- `get_depth()` → per-camera depth dicts.
- `get_segmentation(level=...)` → mesh- or actor-level segmentation images.
- `get_observer_rgb()` → the third-person observer image.
- `get_pcd(if_combine=False)` → combined pointcloud path.
- `get_world_pcd()` → world pointcloud from the far cameras.

### Important behavior

- Wrist cameras are named `left_camera` and `right_camera`.
- Static cameras come from the embodiment config.
- The head camera may be optional, but pointcloud collection expects it when using the default combined path.
- Pointcloud downsampling depends on `pytorch3d`; the fallback path is not a CPU substitute.

## Actor and action helpers

### Actor helpers

- `create_actor(...)` / `create_glb(...)` / `create_obj(...)`: load mesh-backed actors and attach metadata.
- `create_box(...)`, `create_sphere(...)`, `create_cylinder(...)`: create primitive actors.
- `create_table(...)`: build the task table.
- `rand_pose(...)`: sample a free pose.
- `rand_pose_cluttered(...)`: sample a collision-aware clutter pose.

### `Actor` API

The wrapped actor exposes:

- `get_contact_point(...)`
- `get_functional_point(...)`
- `get_target_point(...)`
- `get_orientation_point(...)`
- `iter_contact_points(...)`
- `get_pose()`
- `set_mass(...)`
- `set_name(...)`

### `Action` and `ArmTag`

- `ArmTag("left")` and `ArmTag("right")` normalize arm references.
- `Action(arm_tag, "move", target_pose=...)` creates a motion action.
- `Action(arm_tag, "open", target_gripper_pos=...)` and `Action(arm_tag, "close", ...)` create gripper actions.
- `move` actions accept either `sapien.Pose` or a pose list.

## Practical usage cues

- Use `grasp_actor` when the object has meaningful contact points.
- Use `place_actor` when the target has a functional point or target pose.
- Use `constraint_pose` when alternating arms or threading through a narrow space.
- Use `move_by_displacement(..., move_axis="arm")` for short retract or lift motions.
- Use `check_actors_contact` together with a pose tolerance in `check_success`.
