# Demonstration Collection and HDF5 Handoff

## Scope and side effects

The collector is an attended process: it opens an onscreen MuJoCo environment, starts keyboard and/or HID listeners, creates timestamped episode directories, writes NPZ/XML/JSON intermediates, rewrites an aggregate HDF5 file after accepted episodes, and performs an in-place robomimic-style metadata conversion. Run it only after the user approves the output location and interactive session.

The package and CLI parser were verified, but a complete collection/reset was not: the available installation did not include the opt-in kitchen fixture assets. Dataset playback is likewise deferred evidence and belongs to the `datasets-demonstrations` sub-skill.

## Preflight and command

Choose a writable directory outside the installed package and inspect it without writing:

```bash
python scripts/check_teleop_prereqs.py \
  --device spacemouse \
  --output-directory ./collected-demos
```

Then start an attended collection:

```bash
python -m robocasa.scripts.collect_demos \
  --directory ./collected-demos \
  --environment PickPlaceCounterToCabinet \
  --robots PandaOmron \
  --device spacemouse \
  --renderer mjviewer \
  --split pretrain \
  --layout 1 \
  --style 1
```

On macOS, repository documentation requires `mjpython` for this rendered script:

```bash
mjpython -m robocasa.scripts.collect_demos --directory ./collected-demos --environment PickPlaceCounterToCabinet
```

Current 1.0.1 source accepts `--environment`; it does **not** define the older documentation shorthand `--env`.

## Verified CLI options

| Option | Source default | Operational meaning |
|---|---|---|
| `--directory DIRECTORY` | package asset-root `demonstrations_private` | Parent of a timestamped collection directory. Prefer an explicit user-owned path rather than writing into an installation. |
| `--environment ENVIRONMENT` | `Kitchen` | robosuite/RoboCasa environment class name. For a concrete dataset, specify a registered task environment rather than relying on the generic default. |
| `--robots ROBOTS [ROBOTS ...]` | `PandaOmron` | One or more robot names; explicit use produces a list. |
| `--config CONFIG` | `single-arm-opposed` | Environment configuration, applied for `TwoArm` environments and passed to teleoperation action mapping. |
| `--arm ARM` | `right` | Controlled arm name. |
| `--obj_groups OBJ_GROUPS [OBJ_GROUPS ...]` | omitted | Kitchen object group names or MJCF XML paths. Custom object XML and asset semantics belong to the `tasks-scenes-assets` sub-skill. |
| `--camera CAMERA` | `robot0_frontview` after parsing | Render camera; the special value `free` becomes `None`, selecting the viewer's free camera behavior. |
| `--controller CONTROLLER` | robot default | Composite controller name such as `NONE` or `WHOLE_BODY_IK`, or a controller JSON path. Controller construction belongs to the `simulation-environments` sub-skill. |
| `--device {keyboard,spacemouse}` | auto | With no value, the collector enumerates HID entries and selects SpaceMouse only when the configured vendor/product pair matches exactly; otherwise it selects keyboard. |
| `--pos-sensitivity FLOAT` | `4.0` | Position input scale. |
| `--rot-sensitivity FLOAT` | `4.0` | Rotation input scale. |
| `--debug` | false | Skips timestamped output creation and `DataCollectionWrapper`; use only as an interactive no-save diagnostic, not for dataset collection. |
| `--renderer {mjviewer,mujoco}` | `mjviewer` | Both are onscreen. `mjviewer` manages its viewer update; `mujoco` causes the trajectory loop to call `env.render()` explicitly. This is not an offscreen switch. |
| `--max_fr INT` | `30` | Caps the input/step loop rate; spelling contains an underscore. |
| `--split {pretrain,target,all}` | `pretrain` | Selects scene/object split. With `target` and no layout/style, source chooses paired target layout/style IDs 1–10; explicit layout/style values override selection. |
| `--layout LAYOUT [LAYOUT ...]` | omitted | One or more layout IDs. Unlike the no-save demo, this flag accepts multiple integers. |
| `--style STYLE [STYLE ...]` | omitted | One or more style IDs. Unlike the no-save demo, this flag accepts multiple integers. |
| `--generative_textures` | false | Sets the environment's generative texture mode to `100p`; required texture assets remain external prerequisites. |

If SpaceMouse has a different product ID, auto device selection can fall back to keyboard even though robosuite's explicitly constructed SpaceMouse can auto-detect a 3Dconnexion device. Set the correct private macro and/or pass `--device spacemouse` deliberately after checking the HID listing.

## What happens during an episode

1. The environment resets and exposes episode metadata, including the language instruction when available.
2. Input control starts. Before the first nonzero action, empty SpaceMouse input does not create a demonstration.
3. The `DataCollectionWrapper` records a model XML, episode metadata, flattened simulator states, relative actions, and optional absolute actions into a timestamped `episodes/ep_*` directory.
4. The task must remain successful for 15 consecutive checks. The loop then ends with `discard_traj=False`.
5. A device reset returns no action and marks the episode discarded. Keyboard uses its reset command; SpaceMouse uses the right button.
6. Only a nonempty accepted episode is added to the in-memory `successful_episodes` allowlist.
7. The collector writes `ep_stats.json` and `env_info.json`, creates an episode-local `ep_demo.hdf5`, and rebuilds the collection-level `demo.hdf5` from the successful allowlist.
8. The collection-level HDF5 receives the in-place robomimic-format metadata/action-dictionary conversion.

The collector prints `Episode success: True/False`. Treat the HDF5 and persisted `ep_stats.json`, not terminal output alone, as the recovery evidence.

## Output layout

For a non-debug run, the parent contains a directory named like:

```text
<directory>/
  <YYYY-MM-DD-HH-MM-SS>_<Environment>/
    demo.hdf5
    episodes/
      ep_<timestamp>/
        model.xml
        ep_meta.json
        ep_stats.json
        env_info.json
        state_<timestamp>.npz
        ep_demo.hdf5
```

Multiple `state_*.npz` chunks are possible because the wrapper flushes periodically and on close. The collector's gather function sorts them, concatenates states/actions, deletes the last state to align lengths, and asserts `len(states) == len(actions)`.

## HDF5 structure and metadata

`gather_demonstrations_as_hdf5(directory, out_dir, env_info, successful_episodes=None, verbose=False, out_name="demo.hdf5")` was signature-checked from the installed package. It creates:

```text
data/                                      # group
  demo_1/                                  # accepted episode
    states                                 # flattened MuJoCo states
    actions                                # action vectors
    actions_abs                            # optional, when emitted by controller
    action_dict/                           # added by robomimic-format conversion
      rel_pos
      rel_rot_axis_angle
      rel_rot_6d
      gripper
      ...                                  # absolute/base fields when available
```

Per-demo attributes:

- `model_file`: the full episode MJCF XML (required by conversion);
- `ep_meta`: JSON text when `ep_meta.json` exists;
- `num_samples`: added during robomimic-format conversion.

`data` attributes initially include `date`, `time`, `robocasa_version`, `robosuite_version`, `mujoco_version`, `env`, and the JSON-encoded `env_info`. Conversion adds/replaces:

- `env_args`: JSON environment metadata with dataset type, versions, environment name, and constructor kwargs; it changes `translucent_robot` to false for replay/observation generation;
- `total`: total action samples;
- `mask/<N>_demos`: demo-key subsets for configured dataset sizes.

If no accepted episode has state data, gather closes the new file and returns `None`; the caller skips conversion. Do not claim a usable dataset merely because an empty `demo.hdf5` path exists.

For deeper schema validation, mask semantics, playback, or version compatibility, route to the `datasets-demonstrations` sub-skill.

## Robomimic and LeRobot boundaries

There are two distinct boundaries:

1. **Automatic in-place robomimic-style normalization.** After gathering, the collector calls RoboCasa's internal `convert_to_robomimic_format`. This adds environment metadata, sample counts, action dictionaries, and demo-count masks. It does not extract image observations. The implementation uses RoboCasa utilities and PyTorch; it does not itself import the external `robomimic` package.
2. **Optional state-to-observation/LeRobot conversion.** Repository documentation gives:

   ```bash
   python -m robocasa.scripts.dataset_scripts.convert_hdf5_lerobot \
     --raw_dataset_path ./collected-demos/<run>/demo.hdf5 \
     --camera_height 256 \
     --camera_width 256
   ```

   The conversion parser also accepts `--camera_names NAME [NAME ...]`, defaulting to `robot0_eye_in_hand`, `robot0_agentview_left`, and `robot0_agentview_right`. It reconstructs the simulation and renders observations, writes a sibling `lerobot/` directory, and therefore needs the same assets plus LeRobot/video dependencies. It is expensive and side-effectful; route execution and output validation to the `datasets-demonstrations` sub-skill.

External robomimic policy training, a repository-specific robomimic branch, and MimicGen generation are separate optional workflows. MimicGen was absent in the inspected environment. Do not make them prerequisites for raw collection or imply they were verified here.

## Safe interruption and recovery

### Intentional stop

Use `Ctrl+C`. The top-level collector catches `KeyboardInterrupt`, rebuilds `demo.hdf5` from the current in-memory successful allowlist, applies the robomimic-style conversion, prints the saved path, and exits. Wait for this cleanup message before moving files or killing the terminal.

### Abort or crash mid-episode

An exception, disconnect, forced kill, or power loss may leave raw episode material without a refreshed aggregate. Recovery must be conservative:

1. Stop all writers to that run directory. Never open the active HDF5 concurrently for repair.
2. Copy or snapshot the whole timestamped run directory before changes.
3. Inspect every `episodes/ep_*/ep_stats.json`. Include only records whose JSON says `{"success": true}` and that also contain `model.xml`, `ep_meta.json`, and at least one readable `state_*.npz`.
4. Treat an episode with no `ep_stats.json`, malformed NPZ, missing model XML, or inconsistent state/action lengths as incomplete. Quarantine it; do not relabel it successful from visual memory.
5. If the existing `demo.hdf5` opens read-only and contains consistent accepted demos, preserve it. If it is missing or corrupt, rebuild through a reviewed Python recovery program that calls the verified gather function with the explicit successful episode basenames and the original JSON `env_info`; do not improvise HDF5 edits in place.
6. Run dataset inspection before playback or LeRobot conversion. Playback remains deferred because it reconstructs simulation and requires complete assets.

The CLI has no resume flag. A new invocation creates a new timestamped run, so it will not silently append to the interrupted run. Merge or concatenate datasets only through the dataset-focused sub-skill.
