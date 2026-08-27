# Configuration guide

This skill centers on the files that control task layout, embodiment wiring,
robot action profiles, and camera presets.

## Task config files

| File | Purpose |
| --- | --- |
| `_config_template.yml` | Canonical starting point for a new task config. |
| `demo_clean.yml` | Clean scene/eval preset with no clutter and clean backgrounds. |
| `demo_randomized.yml` | Randomized preset with background and clutter variation. |
| `_camera_config.yml` | Camera resolution and FOV presets. |
| `_embodiment_config.yml` | Robot embodiment roots and joint/camera metadata. |
| `_eval_step_limit.yml` | Per-task step budgets used in eval mode. |

### Common task keys

The task config files typically control:

- `render_freq`: render cadence during action execution.
- `episode_num`: number of episodes to collect or evaluate.
- `use_seed`: whether to reuse deterministic seeds.
- `save_freq`: frame save cadence.
- `embodiment`: one or more robot/embodiment names.
- `language_num`: number of language instructions to generate or load.
- `eval_instruction`: `seen` or `unseen` instruction split.
- `domain_randomization`: background, clutter, table height, and light controls.
- `camera`: head/wrist camera selection and capture flags.
- `data_type`: observation channels such as `rgb`, `depth`, `pointcloud`, `endpose`, and `qpos`.
- `pcd_down_sample_num`: pointcloud downsample count.
- `pcd_crop`: whether to crop the pointcloud to the workspace volume.
- `save_path`: output root for collected data.
- `clear_cache_freq`: cache-cleanup cadence.
- `collect_data`: whether the task should save trajectories.
- `eval_video_log`: whether eval video logging is enabled.

### `demo_clean` vs `demo_randomized`

- `demo_clean`: no random background, no cluttered table, no random lights, and seen-instruction evaluation.
- `demo_randomized`: background and clutter randomization enabled, table-height jitter enabled, and unseen-instruction evaluation.

## Embodiment config file

`_embodiment_config.yml` maps each embodiment name to the robot asset root.
The runtime robot wrapper expects these fields to be present in the embodiment
payload that is merged into the task config.

| Field | Meaning |
| --- | --- |
| `file_path` | Root directory for the robot assets. |
| `urdf_path` | URDF path relative to the robot asset root. |
| `srdf_path` | Optional SRDF path relative to the robot asset root. |
| `planner` | Planner family name used by the robot wrapper. |
| `move_group` | Move group names for the left and right arms. |
| `ee_joints` | End-effector joint names for both arms. |
| `arm_joints_name` | Joint name lists for the arm chains. |
| `gripper_name` | Gripper joint metadata, including base and mimic joints. |
| `gripper_bias` | Offset used to normalize gripper target values. |
| `gripper_scale` | Normalization scale used by the gripper controller. |
| `homestate` | Home joint targets per arm. |
| `fix_gripper_name` | Joints that should be treated as fixed grippers. |
| `delta_matrix` | Frame correction matrix for the end-effector pose. |
| `global_trans_matrix` | Global pose correction matrix for the end-effector pose. |
| `robot_pose` | Root pose for the robot entity or entities. |
| `static_camera_list` | Static camera definitions, including the optional head camera. |
| `rotate_lim` | Arm rotation limits used by the pose search helpers. |
| `grasp_perfect_direction` | Preferred grasp orientations for left and right arms. |

### Practical embodiment notes

- `aloha-agilex` is the default bimanual setup used by the tasks in this checkout.
- The robot action profile table in `_robot_info.json` classifies the active arm and end-effector dimensions for each supported robot family.
- The simulator embodiment and the policy action profile must be compatible, but that compatibility check belongs to the policy-eval skill.

## Camera presets

`_camera_config.yml` defines the render dimensions and field of view used by
both wrist and static cameras.

| Preset | Resolution | FOV |
| --- | --- | --- |
| `D435` | 320×240 | 37° |
| `Large_D435` | 640×480 | 37° |
| `L515` | 320×180 | 45° |
| `Large_L515` | 640×360 | 45° |

### Camera wiring rules

- `head_camera_type` and `wrist_camera_type` choose the preset.
- `collect_head_camera` and `collect_wrist_camera` decide which cameras are attached.
- Wrist cameras are always named `left_camera` and `right_camera` when enabled.
- Static cameras come from the embodiment config and may include `head_camera`.
- The render path should always call `_update_render()` or `scene.update_render()` before capture.

## Eval step limits

`_eval_step_limit.yml` provides a task-name keyed step budget for eval mode.
When `eval_mode` is enabled, the task bootstrap reads the task name from this
file and uses the configured limit. If a task is missing, the runtime falls
back to a conservative default.

## Configuration changes to avoid

- Do not invent new top-level task keys without also updating the bootstrap logic.
- Do not rename camera presets unless the robot/camera wiring is updated in lockstep.
- Do not point a task at an embodiment whose asset root or joint names do not match the robot wrapper.
- Do not rely on the policy-eval profile table to fix simulator-side embodiment errors.
