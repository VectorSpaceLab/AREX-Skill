# Model Catalog Reference

This reference distills the Menagerie catalog structure so an agent can select model directories and XML variants without reopening repository docs.

## Evidence snapshot

The bundled `model-index.json` was generated from repository evidence that had:

- 68 top-level model directories containing top-level XML files;
- 215 top-level XML files and 97 `scene*.xml` files;
- 9 directories with MJX-named XMLs and 21 MJX XML files;
- 63 gallery entries across 11 gallery categories;
- `realsense_d435i` as the only directory exempt from the `scene*.xml` requirement.

The index stores only relative paths, not local checkout paths. It includes README first headings, gallery entries, category labels, recommended preview/load XMLs, XML file lists, MJX file lists, asset directory names, README/LICENSE/CHANGELOG booleans, a license SPDX heuristic, and minimum MuJoCo version evidence extracted from per-model READMEs.

## Directory anatomy

A normal Menagerie model directory is a top-level folder such as `unitree_go2/` or `franka_emika_panda/`. The common layout is:

```text
<model_dir>/
  assets/ or meshes/        mesh and visual/collision assets
  README.md                 generation notes and minimum MuJoCo version, when stated
  LICENSE                   model-specific license text
  CHANGELOG.md              model-specific change history
  <model>.xml               model-only MJCF, suitable for inclusion/composition
  scene.xml                 model plus plane/light/environment for direct loading
  <model>_mjx.xml           optional MJX-compatible model XML
  scene_mjx.xml             optional scene that loads the MJX model XML
  *.png                     preview images, not required for loading
  other *.xml               variants such as hands, actuator choices, poses, or terrain scenes
```

Important details:

- `scene*.xml` files are usually the right first choice for direct loading because they include a world, lights, plane, and sometimes keyframes or objects.
- Non-scene XMLs usually describe the robot or component alone. Use them when composing models or when the gallery explicitly uses a component XML, such as `franka_emika_panda/hand.xml`.
- `assets/` is the dominant mesh directory name. `iit_softfoot/` uses `meshes/` instead.
- `test/model_dir_test.py` expects every model directory to contain `README.md`, `LICENSE`, `CHANGELOG.md`, and at least one `scene*.xml`, except `realsense_d435i`, which is intentionally sensor-only and uses `d435i.xml` directly.

## XML selection rules

Use these rules in order:

1. **Known gallery entry:** use `recommended_load_xmls` from `model-index.json`. Those paths encode `generate_gallery.py` preview overrides and are the safest catalog answer for named model requests.
2. **Ordinary robot with `scene.xml`:** choose `<dir>/scene.xml` for first-time loading or viewer use.
3. **Multiple scene XMLs:** choose the scene that matches the task:
   - `scene_mjx.xml` or `scene_hfield_mjx.xml` for MJX variants;
   - `scene_left.xml` or `scene_right.xml` for handed end-effectors;
   - `scene_position.xml`, `scene_velocity.xml`, or `scene_motor.xml` for actuator/control-style variants;
   - `scene_arm.xml`, `scene_base.xml`, `scene_box.xml`, `scene_locomotion.xml`, or `scene_manipulation.xml` when the name matches the requested environment or variant.
4. **Component-only gallery override:** for Panda Gripper and xArm7 Gripper, choose `franka_emika_panda/hand.xml` or `ufactory_xarm7/hand.xml` rather than the arm scene.
5. **Sensor-only directory:** `realsense_d435i` has no `scene*.xml`; choose `realsense_d435i/d435i.xml` and state that it is a standalone sensor asset, not a robot scene.
6. **Unknown gallery category:** if a directory exists in the index but has no gallery category, use XML names and README title rather than inventing a category. Prefer `scene.xml` when present; otherwise use the most specific scene or model XML requested by the user.

## Category inventory

Categories come from `generate_gallery.py` `MODEL_MAP` and the generated README gallery. They are gallery entries, not necessarily one-to-one directories: `franka_emika_panda` and `ufactory_xarm7` each appear both as arms and end-effectors.

- **Arms (20):** `agilex_piper/piper`, `arx_l5/arx_l5`, `flexiv_rizon4/flexiv_rizon4`, `flexiv_rizon4s/flexiv_rizon4s`, `franka_emika_panda/panda`, `franka_fr3/fr3`, `i2rt_yam/yam`, `kinova_gen3/gen3`, `kuka_iiwa_14/iiwa14`, `low_cost_robot_arm/low_cost_robot_arm`, `rethink_robotics_sawyer/sawyer`, `seeed_rebot_devarm/seeed_rebot_devarm`, `trossen_vx300s/vx300s`, `trossen_wx250s/wx250s`, `trs_so_arm100/so_arm100`, `ufactory_lite6/lite6`, `ufactory_xarm7/xarm7`, `unitree_z1/z1`, `universal_robots_ur10e/ur10e`, `universal_robots_ur5e/ur5e`.
- **End-effectors (9):** `franka_emika_panda/hand`, `leap_hand/left_hand`, `robotiq_2f85/2f85`, `shadow_dexee/shadow_dexee`, `shadow_hand/left_hand`, `sharpa_wave/left_hand`, `ufactory_xarm7/hand`, `umi_gripper/umi_gripper`, `wonik_allegro/left_hand`.
- **Mobile manipulators (6):** `google_robot/robot`, `hello_robot_stretch/stretch`, `hello_robot_stretch_3/stretch`, `pal_tiago/tiago`, `pal_tiago_dual/tiago_dual`, `stanford_tidybot/tidybot`.
- **Quadrupeds (8):** `anybotics_anymal_b/anymal_b`, `anybotics_anymal_c/anymal_c`, `boston_dynamics_spot/spot_arm`, `google_barkour_v0/barkour_v0`, `google_barkour_vb/barkour_vb`, `unitree_a1/a1`, `unitree_go1/go1`, `unitree_go2/go2`.
- **Humanoids (11):** `apptronik_apollo/apptronik_apollo`, `berkeley_humanoid/berkeley_humanoid`, `booster_t1/t1`, `fourier_n1/n1`, `pal_talos/talos`, `pndbotics_adam_lite/adam_lite`, `robotis_op3/op3`, `toddlerbot_2xc/toddlerbot_2xc`, `toddlerbot_2xm/toddlerbot_2xm`, `unitree_g1/g1`, `unitree_h1/h1`.
- **Other categories:** `aloha/aloha` is Dual Arms; `agility_cassie/cassie` is Bipeds; `flybody/fruitfly`, `iit_softfoot/softfoot`, and `ms_human_700/MS-Human-700` are Biomechanical; `bitcraze_crazyflie_2/cf2` and `skydio_x2/x2` are Drones; `robot_soccer_kit/robot_soccer_kit` is Mobile Bases; `realsense_d435i/d435i` is Miscellaneous.

Directories present in the evidence snapshot but not mapped to a gallery category are: `dynamixel_2r`, `franka_fr3_v2`, `rainbow_robotics_rby1`, `robotiq_2f85_v4`, `robotstudio_so101`, `tetheria_aero_hand_open`, and `trossen_wxai`.

## MJX selection

Use MJX XMLs only when the user explicitly asks for MJX compatibility, JAX/MJX use, or the suffix is otherwise relevant. MJX variants are catalog variants, not proof that a JAX/GPU environment is available.

Directories with MJX-named XMLs in the bundled index:

| Directory | Gallery category | MJX XMLs | Non-MJX fallback |
|---|---|---|---|
| `anybotics_anymal_c` | Quadrupeds | `scene_mjx.xml`, `anymal_c_mjx.xml` | `anybotics_anymal_c/scene.xml` |
| `franka_emika_panda` | Arms, End-effectors | `mjx_scene.xml`, `mjx_panda.xml`, `mjx_panda_nohand.xml`, `mjx_hand.xml`, `mjx_single_cube.xml` | `franka_emika_panda/scene.xml` or `franka_emika_panda/hand.xml` for gripper-only |
| `google_barkour_v0` | Quadrupeds | `scene_mjx.xml`, `barkour_v0_mjx.xml` | `google_barkour_v0/scene.xml` |
| `google_barkour_vb` | Quadrupeds | `scene_mjx.xml`, `scene_hfield_mjx.xml`, `barkour_vb_mjx.xml` | `google_barkour_vb/scene.xml` |
| `robotiq_2f85_v4` | unknown in gallery | `mjx_2f85.xml` | `robotiq_2f85_v4/scene.xml` |
| `toddlerbot_2xc` | Humanoids | `scene_mjx.xml`, `toddlerbot_2xc_mjx.xml` | `toddlerbot_2xc/scene.xml` |
| `toddlerbot_2xm` | Humanoids | `scene_mjx.xml`, `toddlerbot_2xm_mjx.xml` | `toddlerbot_2xm/scene.xml` |
| `unitree_g1` | Humanoids | `scene_mjx.xml`, `g1_mjx.xml` | `unitree_g1/scene.xml` |
| `unitree_go2` | Quadrupeds | `scene_mjx.xml`, `go2_mjx.xml` | `unitree_go2/scene.xml` |

### Hard case: all MJX-capable quadrupeds

The MJX-capable quadrupeds in this snapshot are:

- `anybotics_anymal_c`: use `anybotics_anymal_c/scene_mjx.xml`; fallback `anybotics_anymal_c/scene.xml`.
- `google_barkour_v0`: use `google_barkour_v0/scene_mjx.xml`; fallback `google_barkour_v0/scene.xml`.
- `google_barkour_vb`: use `google_barkour_vb/scene_mjx.xml` or `google_barkour_vb/scene_hfield_mjx.xml` when hfield terrain is requested; fallback `google_barkour_vb/scene.xml`.
- `unitree_go2`: use `unitree_go2/scene_mjx.xml`; fallback `unitree_go2/scene.xml`.

Quadrupeds without MJX XMLs in this snapshot are `anybotics_anymal_b`, `boston_dynamics_spot`, `unitree_a1`, and `unitree_go1`; answer with their normal `scene.xml` and state that no bundled MJX XML is listed.

## Minimum MuJoCo version metadata

Per-model READMEs usually state `Requires MuJoCo X.Y.Z or later.` The index stores this as `min_mujoco_version` plus evidence lines. Four directories in the snapshot did not state an explicit minimum in the README evidence: `dynamixel_2r`, `rainbow_robotics_rby1`, `robot_soccer_kit`, and `tetheria_aero_hand_open`.

When a user asks whether a model requires a newer MuJoCo, report the indexed `min_mujoco_version` and route any actual compile failure or version-specific XML error to `model-loading`.

## License and README metadata

For each model directory, use these index fields:

- `has_readme`, `has_license`, `has_changelog`: structural expectations from the model directory test.
- `license_spdx`: a heuristic matching the gallery generator's license detector (`Apache-2.0`, `BSD-3-Clause-Clear`, `BSD-3-Clause`, `BSD-2-Clause`, `MIT`, `Unknown`, or `null` if missing).
- `title`: the first README heading. Gallery display names strip suffixes such as `Description (MJCF)`.

If a task involves changing or validating these files, route to `contribution-maintenance` after catalog identification.

## `robot_descriptions` naming hints

Menagerie directory names are not guaranteed to match `robot_descriptions` module names. The repository README gives `panda_mj_description` as an example for Franka Panda, but the catalog source of truth remains Menagerie-relative XML paths. When the user asks for `robot_descriptions` loading, identify the likely Menagerie directory here, then route loading/import details to `model-loading`.

## Inventory command examples

From the generated skill directory, inspect a current checkout with:

```bash
python sub-skills/model-catalog/scripts/inspect_model_catalog.py --repo-root "$MENAGERIE_ROOT" --markdown
python sub-skills/model-catalog/scripts/inspect_model_catalog.py --repo-root "$MENAGERIE_ROOT" --json /tmp/menagerie-catalog.json
```

Validate the bundled snapshot is parseable with:

```bash
python -m json.tool sub-skills/model-catalog/references/model-index.json >/tmp/model-index.pretty.json
```
