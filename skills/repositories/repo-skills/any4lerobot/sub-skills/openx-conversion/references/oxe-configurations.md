# OXE configuration and transform lookup

This catalog is a self-contained snapshot of the Open X-Embodiment configuration
and standardization rules reviewed for this route. Dataset names are exact,
case-sensitive TFDS/OXE identifiers. The snapshot had **70 configuration
entries** and **73 standard-transform entries**. It is a lookup aid, not a
promise that an external TFDS release contains every builder or that a current
LeRobot release accepts every generated feature.

## How to use the catalog

1. Derive `dataset_name` from the raw path before consulting this table.
2. Find an exact configuration row. Do not turn hyphens into underscores,
   shorten an externally converted name, or use a nearby dataset's mapping.
3. Confirm the builder's transformed observation keys and widths against the
   `state keys` column. A listed key may be nested or may be created by the
   standardizer; it is not proof that the raw observation has that key.
4. Select the listed default FPS and normalized robot type only when they are
   appropriate for the actual data. Override them explicitly when the source
   metadata differs.
5. Check the transform registry below. A configuration without a transform is
   still a valid catalog entry, but its raw action/state semantics must be
   independently validated. A transform without a configuration is not safe to
   run through the eight-column state builder.

`P`, `S`, and `W` in the RGB column mean primary, secondary, and wrist camera.
A `—` state-key slot is a one-wide float32 zero pad. Camera entries describe
catalog intent; the converter selects actual observation keys by its
case-sensitive `image`/`rgb` filter, not by this camera column.

## Encoding semantics

### State encoding

| Encoding | Intended layout | Generated names |
| --- | --- | --- |
| `POS_EULER` | EEF XYZ + roll/pitch/yaw + one pad + gripper | `x,y,z,roll,pitch,yaw,pad,gripper` |
| `POS_QUAT` | EEF XYZ + quaternion + gripper | `x,y,z,rx,ry,rz,rw,gripper` |
| `JOINT` | Joint values with zero pads as needed + gripper | seven `motor_i` slots plus `gripper`, with configured pad slots renamed `pad` |
| `NONE` | No configured proprioception | eight `motor_i` names and eight zero columns unless a custom key list says otherwise; treat as unsupported for production without review |

The special LIBERO names use `axis_angle1`, `axis_angle2`, and
`axis_angle3`, and the state gripper is represented by two values. The
catalog's state-key lists are concatenated in order; each non-`None` source
array must have the expected trailing width. The implementation does not
reshape a malformed source array.

### Action encoding

| Encoding | Intended generated width | Generated names |
| --- | ---: | --- |
| `EEF_POS` | 7 | `x,y,z,roll,pitch,yaw,gripper` conceptually as EEF translation/rotation plus gripper; dataset-specific transforms determine exact rotation convention |
| `JOINT_POS` | 8 | `motor_0` through `motor_6`, then `gripper` |

The source feature builder explicitly specializes these two encodings. The
catalog reviewed here uses them; do not infer support for other enum values
without checking the implementation. Actions are cast to float32 after
standardization and are not padded or clipped by the generic writer.

## Configuration catalog

| Dataset name | State | Action | Default Hz | Robot type | State keys in concatenation order | RGB camera intent |
| --- | --- | --- | ---: | --- | --- | --- |
| `fractal20220817_data` | POS_QUAT | EEF_POS | 3 | Google Robot | base_pose_tool_reached; gripper_closed | P=image |
| `kuka` | POS_QUAT | EEF_POS | 10 | Kuka iiwa | clip_function_input/base_pose_tool_reached; gripper_closed | P=image |
| `bridge_oxe` | POS_EULER | EEF_POS | 5 | WidowX | EEF_state; —; gripper_state | P=image, S=image_1 |
| `bridge_orig` | POS_EULER | EEF_POS | 5 | WidowX | EEF_state; —; gripper_state | P=image_0, S=image_1 |
| `bridge_dataset` | POS_EULER | EEF_POS | 5 | WidowX | EEF_state; —; gripper_state | P=image_0, S=image_1 |
| `taco_play` | POS_EULER | EEF_POS | 15 | Franka | state_eef; —; state_gripper | P=rgb_static, W=rgb_gripper |
| `jaco_play` | POS_EULER | EEF_POS | 10 | Jaco 2 | state_eef; —; state_gripper | P=image, W=image_wrist |
| `berkeley_cable_routing` | JOINT | EEF_POS | 10 | Franka | robot_state; — | P=image, S=top_image, W=wrist45_image |
| `roboturk` | NONE | EEF_POS | 10 | Sawyer | —; —; —; —; —; —; —; — | P=front_rgb |
| `nyu_door_opening_surprising_effectiveness` | NONE | EEF_POS | 3 | Hello Stretch | —; —; —; —; —; —; —; — | W=image |
| `viola` | JOINT | EEF_POS | 20 | Franka | joint_states; gripper_states | P=agentview_rgb, W=eye_in_hand_rgb |
| `berkeley_autolab_ur5` | POS_QUAT | EEF_POS | 5 | UR5 | state | P=image, W=hand_image |
| `toto` | JOINT | EEF_POS | 30 | Franka | state; — | P=image |
| `language_table` | POS_EULER | EEF_POS | 10 | xArm | effector_translation; —; —; —; —; —; — | P=rgb |
| `columbia_cairlab_pusht_real` | POS_EULER | EEF_POS | 10 | UR5 | robot_state; —; —; —; —; —; — | P=image, W=wrist_image |
| `stanford_kuka_multimodal_dataset_converted_externally_to_rlds` | POS_QUAT | EEF_POS | 20 | Kuka iiwa | ee_position; ee_orientation; — | P=image |
| `nyu_rot_dataset_converted_externally_to_rlds` | POS_EULER | EEF_POS | 3 | xArm | eef_state; —; gripper_state | P=image |
| `stanford_hydra_dataset_converted_externally_to_rlds` | POS_EULER | EEF_POS | 10 | Franka | eef_state; —; gripper_state | P=image, W=wrist_image |
| `austin_buds_dataset_converted_externally_to_rlds` | JOINT | EEF_POS | 20 | Franka | state | P=image, W=wrist_image |
| `nyu_franka_play_dataset_converted_externally_to_rlds` | POS_EULER | EEF_POS | 3 | Franka | eef_state; —; — | P=image, S=image_additional_view |
| `maniskill_dataset_converted_externally_to_rlds` | POS_QUAT | EEF_POS | 20 | Franka | tcp_pose; gripper_state | P=image, W=wrist_image |
| `furniture_bench_dataset_converted_externally_to_rlds` | POS_QUAT | EEF_POS | 10 | Franka | state | P=image, W=wrist_image |
| `cmu_franka_exploration_dataset_converted_externally_to_rlds` | NONE | EEF_POS | 10 | Franka | —; —; —; —; —; —; —; — | P=highres_image |
| `ucsd_kitchen_dataset_converted_externally_to_rlds` | JOINT | EEF_POS | 2 | xArm | joint_state; — | P=image |
| `ucsd_pick_and_place_dataset_converted_externally_to_rlds` | POS_EULER | EEF_POS | 3 | xArm | eef_state; —; gripper_state | P=image |
| `austin_sailor_dataset_converted_externally_to_rlds` | POS_QUAT | EEF_POS | 20 | Franka | state | P=image, W=wrist_image |
| `austin_sirius_dataset_converted_externally_to_rlds` | POS_QUAT | EEF_POS | 20 | Franka | state | P=image, W=wrist_image |
| `bc_z` | POS_EULER | EEF_POS | 10 | Google Robot | present/xyz; present/axis_angle; —; present/sensed_close | P=image |
| `utokyo_pr2_opening_fridge_converted_externally_to_rlds` | POS_EULER | EEF_POS | 10 | PR2 | eef_state; —; gripper_state | P=image |
| `utokyo_pr2_tabletop_manipulation_converted_externally_to_rlds` | POS_EULER | EEF_POS | 10 | PR2 | eef_state; —; gripper_state | P=image |
| `utokyo_xarm_pick_and_place_converted_externally_to_rlds` | POS_EULER | EEF_POS | 10 | xArm | end_effector_pose; —; — | P=image, S=image2, W=hand_image |
| `utokyo_xarm_bimanual_converted_externally_to_rlds` | POS_EULER | EEF_POS | 10 | xArm Bimanual | pose_r; —; — | P=image |
| `robo_net` | POS_EULER | EEF_POS | 1 | Multi-Robot | eef_state; —; gripper_state | P=image, S=image1 |
| `berkeley_mvp_converted_externally_to_rlds` | POS_QUAT | JOINT_POS | 5 | xArm | pose; gripper | W=hand_image |
| `berkeley_rpt_converted_externally_to_rlds` | JOINT | JOINT_POS | 30 | Franka | joint_pos; gripper | W=hand_image |
| `kaist_nonprehensile_converted_externally_to_rlds` | POS_QUAT | EEF_POS | 10 | Franka | state; — | P=image |
| `stanford_mask_vit_converted_externally_to_rlds` | POS_EULER | EEF_POS | — | Sawyer | eef_state; —; gripper_state | P=image |
| `tokyo_u_lsmo_converted_externally_to_rlds` | POS_EULER | EEF_POS | 10 | Cobotta | eef_state; —; gripper_state | P=image |
| `dlr_sara_pour_converted_externally_to_rlds` | POS_EULER | EEF_POS | 10 | DLR SARA | state; —; — | P=image |
| `dlr_sara_grid_clamp_converted_externally_to_rlds` | POS_EULER | EEF_POS | 10 | DLR SARA | state; —; — | P=image |
| `dlr_edan_shared_control_converted_externally_to_rlds` | POS_EULER | EEF_POS | 5 | DLR EDAN | state; — | P=image |
| `asu_table_top_converted_externally_to_rlds` | POS_EULER | EEF_POS | 12.5 | UR5 | eef_state; —; gripper_state | P=image |
| `stanford_robocook_converted_externally_to_rlds` | POS_EULER | EEF_POS | 5 | Franka | eef_state; —; gripper_state | P=image_1, S=image_2 |
| `imperialcollege_sawyer_wrist_cam` | NONE | EEF_POS | 10 | Sawyer | —; —; —; —; —; —; —; state | P=image, W=wrist_image |
| `iamlab_cmu_pickup_insert_converted_externally_to_rlds` | JOINT | EEF_POS | 20 | Franka | joint_state; gripper_state | P=image, W=wrist_image |
| `uiuc_d3field` | NONE | EEF_POS | 1 | Kinova Gen3 | —; —; —; —; —; —; —; — | P=image_1, S=image_2 |
| `utaustin_mutex` | JOINT | EEF_POS | 20 | Franka | state | P=image, W=wrist_image |
| `berkeley_fanuc_manipulation` | JOINT | EEF_POS | 10 | Fanuc Mate | joint_state; —; gripper_state | P=image, W=wrist_image |
| `cmu_playing_with_food` | POS_EULER | EEF_POS | 10 | Franka | state; —; — | P=image, W=finger_vision_1 |
| `cmu_play_fusion` | JOINT | EEF_POS | 5 | Franka | state | P=image |
| `cmu_stretch` | POS_EULER | EEF_POS | 10 | Hello Stretch | eef_state; —; gripper_state | P=image |
| `berkeley_gnm_recon` | POS_EULER | EEF_POS | 3 | Jackal | state; —; — | W=image |
| `berkeley_gnm_cory_hall` | POS_EULER | EEF_POS | 5 | RC Car | state; —; — | W=image |
| `berkeley_gnm_sac_son` | POS_EULER | EEF_POS | 10 | TurtleBot 2 | state; —; — | W=image |
| `droid` | POS_EULER | EEF_POS | 15 | Franka | EEF_state; —; gripper_state | P=exterior_image_1_left, S=exterior_image_2_left, W=wrist_image_left |
| `fmb_dataset` | POS_EULER | EEF_POS | 10 | Franka | proprio | P=image_side_1, S=image_side_2, W=image_wrist_1 |
| `dobbe` | POS_EULER | EEF_POS | 3.75 | Hello Stretch | EEF_state; —; gripper_state | P=wrist_image |
| `roboset` | JOINT | JOINT_POS | 5 | Franka | proprio | P=image_left, S=image_right, W=image_wrist |
| `rh20t` | POS_EULER | EEF_POS | 10 | Flexiv | proprio | P=image_front, S=image_side_right, W=image_wrist |
| `tdroid_carrot_in_bowl` | POS_EULER | EEF_POS | 5 | Franka | EEF_state; —; gripper_state | P=static_image |
| `tdroid_pour_corn_in_pot` | POS_EULER | EEF_POS | 5 | Franka | EEF_state; —; gripper_state | P=static_image |
| `tdroid_flip_pot_upright` | POS_EULER | EEF_POS | 5 | Franka | EEF_state; —; gripper_state | P=static_image |
| `tdroid_move_object_onto_plate` | POS_EULER | EEF_POS | 5 | Franka | EEF_state; —; gripper_state | P=static_image |
| `tdroid_knock_object_over` | POS_EULER | EEF_POS | 5 | Franka | EEF_state; —; gripper_state | P=static_image |
| `tdroid_cover_object_with_towel` | POS_EULER | EEF_POS | 5 | Franka | EEF_state; —; gripper_state | P=static_image |
| `droid_wipe` | POS_EULER | EEF_POS | 15 | Franka | proprio | P=exterior_image_2_left, W=wrist_image_left |
| `libero_spatial_no_noops` | POS_EULER | EEF_POS | 20 | Franka | EEF_state; gripper_state | P=image, W=wrist_image |
| `libero_object_no_noops` | POS_EULER | EEF_POS | 20 | Franka | EEF_state; gripper_state | P=image, W=wrist_image |
| `libero_goal_no_noops` | POS_EULER | EEF_POS | 20 | Franka | EEF_state; gripper_state | P=image, W=wrist_image |
| `libero_10_no_noops` | POS_EULER | EEF_POS | 20 | Franka | EEF_state; gripper_state | P=image, W=wrist_image |

## Catalogued depth intent

These entries list depth in the OXE configuration. The current conversion
contract still excludes keys containing lowercase `depth` from LeRobot
features and frame writes. Preserve this table when deciding whether an
explicit depth-capable implementation is needed; do not claim the base route
converted these streams.

| Dataset name | Depth camera intent |
| --- | --- |
| `taco_play` | P=depth_static, W=depth_gripper |
| `berkeley_autolab_ur5` | P=depth |
| `stanford_kuka_multimodal_dataset_converted_externally_to_rlds` | P=depth_image |
| `nyu_franka_play_dataset_converted_externally_to_rlds` | P=depth, S=depth_additional_view |
| `maniskill_dataset_converted_externally_to_rlds` | P=depth, W=wrist_depth |
| `stanford_robocook_converted_externally_to_rlds` | P=depth_1, S=depth_2 |
| `uiuc_d3field` | P=depth_1, S=depth_2 |
| `fmb_dataset` | P=image_side_1_depth, S=image_side_2_depth, W=image_wrist_1_depth |
| `tdroid_carrot_in_bowl` | P=static_depth_image |
| `tdroid_pour_corn_in_pot` | P=static_depth_image |
| `tdroid_flip_pot_upright` | P=static_depth_image |
| `tdroid_move_object_onto_plate` | P=static_depth_image |
| `tdroid_knock_object_over` | P=static_depth_image |
| `tdroid_cover_object_with_towel` | P=static_depth_image |

## Standard-transform registry

The standardizer is selected by exact dataset name. The names on the left are
registry keys; the function labels on the right are behavioral labels, not
imports that a runtime user should resolve from a source checkout.

| Registry keys | Standardization behavior |
| --- | --- |
| `bridge_oxe` | Remove first no-op, relabel reached-state movement, normalize gripper and derive EEF/gripper state |
| `bridge_orig`, `bridge_dataset` | Remove first no-op, binarize/relabel Bridge actions, derive EEF/gripper state |
| `ppgm`, `ppgm_static`, `ppgm_wrist` | Clip/binarize gripper and derive EEF/gripper state |
| `fractal20220817_data`, `kuka` | Convert relative gripper action to absolute and use natural-language instruction |
| `taco_play` | Derive EEF/gripper state, clip relative action, preserve language |
| `jaco_play` | Derive EEF state, create zero rotation, convert gripper to absolute |
| `berkeley_cable_routing` | Build EEF action and zero gripper component |
| `roboturk` | Clip and invert gripper action |
| `nyu_door_opening_surprising_effectiveness` | Convert relative gripper action to absolute |
| `viola` | Clip and invert gripper action |
| `berkeley_autolab_ur5` | Reverse wrist BGR, extract state/depth, convert gripper action |
| `toto` | Build EEF action and language from observation |
| `language_table` | Pad action, decode null-padded instruction text |
| `columbia_cairlab_pusht_real` | Build action from world, rotation, and gripper fields |
| `stanford_kuka_multimodal_dataset_converted_externally_to_rlds` | Squeeze depth channel and build a 7-wide action with zero rotation |
| `nyu_rot_dataset_converted_externally_to_rlds` | Derive EEF/gripper state and retain action prefix |
| `stanford_hydra_dataset_converted_externally_to_rlds` | Reverse BGR images, invert gripper, derive state slices |
| `austin_buds_dataset_converted_externally_to_rlds` | Clip/invert gripper and retain first eight state values |
| `nyu_franka_play_dataset_converted_externally_to_rlds` | Squeeze/cast depth, derive EEF state, clip gripper |
| `maniskill_dataset_converted_externally_to_rlds` | Derive gripper state from state |
| `furniture_bench_dataset_converted_externally_to_rlds` | Retain state, convert quaternion action rotation to Euler, invert gripper |
| `cmu_franka_exploration_dataset_converted_externally_to_rlds` | Drop the final action component |
| `ucsd_kitchen_dataset_converted_externally_to_rlds` | Derive seven-wide joint state and drop final action component |
| `ucsd_pick_and_place_dataset_converted_externally_to_rlds` | Derive EEF/gripper state and insert zero rotation |
| `austin_sailor_dataset_converted_externally_to_rlds`, `austin_sirius_dataset_converted_externally_to_rlds` | Clip and invert gripper action |
| `bc_z` | Build action from future XYZ/axis-angle residual and target-close |
| `utokyo_pr2_opening_fridge_converted_externally_to_rlds`, `utokyo_pr2_tabletop_manipulation_converted_externally_to_rlds` | Derive EEF/gripper state and drop final action component |
| `utokyo_xarm_pick_and_place_converted_externally_to_rlds` | Preserve trajectory after prior dataset preparation |
| `utokyo_xarm_bimanual_converted_externally_to_rlds` | Retain the final seven action values |
| `robo_net` | Derive EEF/gripper state and insert zero rotation |
| `berkeley_mvp_converted_externally_to_rlds`, `berkeley_rpt_converted_externally_to_rlds` | Add a singleton dimension to gripper observation |
| `kaist_nonprehensile_converted_externally_to_rlds` | Retain state suffix and insert zero gripper action |
| `stanford_mask_vit_converted_externally_to_rlds` | Derive padded EEF/gripper state and action |
| `tokyo_u_lsmo_converted_externally_to_rlds` | Derive EEF/gripper state |
| `dlr_sara_pour_converted_externally_to_rlds` | Preserve trajectory |
| `dlr_sara_grid_clamp_converted_externally_to_rlds` | Retain first six state values |
| `dlr_edan_shared_control_converted_externally_to_rlds` | Invert gripper action |
| `asu_table_top_converted_externally_to_rlds` | Use ground-truth EEF and observation gripper state |
| `stanford_robocook_converted_externally_to_rlds` | Derive EEF/gripper state |
| `imperialcollege_sawyer_wrist_cam` | Drop final action component |
| `iamlab_cmu_pickup_insert_converted_externally_to_rlds` | Derive joint/gripper state and convert quaternion action rotation |
| `uiuc_d3field` | Pad action with zero rotation/gripper components |
| `utaustin_mutex` | Reverse BGR images, retain state prefix, clip/invert gripper |
| `berkeley_fanuc_manipulation` | Reverse BGR images, derive joint/gripper state, derive action gripper from state |
| `cmu_playing_with_food` | Convert quaternion action rotation to Euler |
| `cmu_play_fusion` | Retain translation and quaternion action suffix |
| `cmu_stretch` | Derive padded EEF/gripper state and drop final action component |
| `berkeley_gnm_recon`, `berkeley_gnm_cory_hall`, `berkeley_gnm_sac_son` | Build padded state/action from mobile-base fields |
| `droid` | Build base-frame action/state, invert gripper, and randomly swap exterior cameras |
| `fmb_dataset` | Reverse known BGR images and construct proprioception |
| `dobbe` | Derive EEF/gripper state |
| `roboset` | Use state as proprioception and clip/invert gripper |
| `rh20t_rlds` | Build action/proprioception from TCP and gripper fields |
| `tdroid_carrot_in_bowl`, `tdroid_pour_corn_in_pot`, `tdroid_flip_pot_upright`, `tdroid_move_object_onto_plate`, `tdroid_knock_object_over`, `tdroid_cover_object_with_towel` | Binarize gripper action and derive EEF/gripper state |
| `droid_wipe` | Build finetuning proprioception and action from DROID fields |
| `libero_spatial_no_noops`, `libero_object_no_noops`, `libero_goal_no_noops`, `libero_10_no_noops` | Clip/invert LIBERO gripper and derive EEF plus two-value gripper state |

## Important asymmetries and unsupported cases

- `rh20t` is present in the configuration catalog while `rh20t_rlds` is the
  standard-transform key. Do not assume the transform is selected for the
  configured name; resolve this mismatch against the actual dataset identity.
- `ppgm`, `ppgm_static`, and `ppgm_wrist` have transforms but no configuration
  row in this snapshot. They require an explicit state/action contract before
  the generic eight-column state fallback could be considered.
- Some standardizers use optional TensorFlow Graphics for quaternion/Euler
  conversion. That dependency is not required for catalog lookup but is
  required for those transformations.
- A listed depth intent does not override the base image filter. Depth is
  documented here so a caller can reject the base route or choose an explicitly
  depth-capable implementation.
- Unknown names receive no standardizer, eight `None` state slots, 10 FPS, and
  `unknown` robot type in the reviewed fallback. Stop and request a mapping
  rather than treating that output as semantically correct.
