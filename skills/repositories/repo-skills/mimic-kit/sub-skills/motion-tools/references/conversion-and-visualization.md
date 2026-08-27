# Conversion, visualization, DOF diagnostics, and log plotting

Use these recipes inside or alongside a target MimicKit checkout. The bundled helper scripts live in this sub-skill and do not depend on source-repo tool paths.

## Convert GMR motion data

Use the bundled GMR converter for GMR-style pickle files containing `fps`, `root_pos`, `root_rot`, and `dof_pos`.

```bash
python scripts/convert_gmr_to_mimickit.py \
  --input_file path/to/gmr_motion.pkl \
  --output_file path/to/output_motion.pkl \
  --loop wrap \
  --start_frame 0 \
  --end_frame -1 \
  --output_fps -1 \
  --repo-root path/to/mimickit-checkout
```

Inputs and output:

- `root_pos`: `(num_frames, 3)` root translations.
- `root_rot`: `(num_frames, 4)` root quaternions in `(x, y, z, w)` order.
- `dof_pos`: `(num_frames, num_dofs)` character DoF values already ordered for the target character.
- Output pickle schema is the MimicKit `Motion` schema with frames `[root_pos, root_rot_expmap, dof_pos]`.

`--repo-root` is optional. When supplied, the helper can save through the target checkout's `Motion` class; otherwise it writes the same pickle schema directly. The verified tiny fixture for this route produced `frames.shape == (2, 8)` when the input had two DoFs.

The source GMR README advertised an older `tools/data_format_conversion/gmr_to_mimickit.py` path, while the actual source file was under `tools/gmr_to_mimickit/`. Prefer the bundled script path above.

## Convert SMPL/AMASS motion data

Use the bundled SMPL converter for AMASS-style `.npz` files.

```bash
python scripts/convert_smpl_to_mimickit.py \
  --input_file path/to/amass_sequence.npz \
  --output_file path/to/smpl_motion.pkl \
  --loop clamp \
  --start_frame 0 \
  --end_frame -1 \
  --output_fps -1 \
  --z_correction calibrate \
  --repo-root path/to/mimickit-checkout
```

Required input keys:

- `poses`: `(num_frames, num_pose_params)` axis-angle pose array; the converter uses the first 66 SMPL pose parameters and zero-fills the final hand parameters needed for the 24-joint internal layout.
- `trans`: `(num_frames, 3)` root translation array.
- `mocap_framerate` or `fps`: scalar source rate; defaults to 30 when neither is present.

The converter preserves the source SMPL-to-Mujoco joint-name reorder, parent indices, local translations, and Y-up/Z-up quaternion correction constants. It writes a MimicKit SMPL humanoid motion with 69 joint DoFs plus six root values; the verified tiny fixture produced `frames.shape == (2, 75)`.

`--z_correction` choices:

| Mode | Effect | Use when |
| --- | --- | --- |
| `none` | Leave root height unchanged. | You already trust the sequence height. |
| `calibrate` | Shift root `z` using the minimum estimated body height in the first 30 frames, with a small foot offset. | Default quick AMASS cleanup. |
| `full` | Shift root `z` using the minimum estimated body height over the full sequence. | The initial frames are not representative. |

After conversion, either place the output under the target checkout's motion data area or update an environment config's `motion_file` to point to the converted file. For non-cyclic AMASS clips, prefer `--loop clamp` unless the seam has been inspected.

## Visualize a motion clip

The `view_motion` environment loads `motion_file`, builds a disabled-motor character, and synchronizes the simulator body state to reference motion frames on each update. It can also render configured key bodies as red cross markers.

Typical generated-skill wrapper command:

```bash
python ../runner-and-backends/scripts/run_mimickit.py \
  --repo-root <mimickit-checkout> \
  -- --mode test --arg_file args/view_motion_humanoid_args.txt --visualize true
```

Source presets cover humanoid, humanoid sword/shield, SMPL, G1, Go2, and high-torque Pi+ variants with names following `args/view_motion_*_args.txt`. They select `env_name: view_motion`, a character asset, key bodies, and a `motion_file` value. In a fresh checkout, many motions and non-humanoid assets may be missing until external data is downloaded.

Checklist before launching:

1. Pick a backend configuration through the runner guidance; this sub-skill does not install Isaac Gym, Isaac Lab/Isaac Sim, or Newton/Warp.
2. Confirm the selected `char_file` exists in the target checkout and matches the motion's DoF tail.
3. Confirm `motion_file` exists, or that the dataset YAML it points to resolves all entries.
4. Use a small `--num_envs` and `--visualize true` for inspection; disable rendering only when another workflow is recording headless video.
5. For wrap clips, remember the viewer can run five loops before timing out.

## Run character DoF diagnostics

The character DoF test environment fixes the root and sweeps one DoF at a time between the action-space low/high limits. Each environment is phase-shifted by its environment id, so multiple envs can show multiple DoFs at once.

Typical generated-skill wrapper command:

```bash
python ../runner-and-backends/scripts/run_mimickit.py \
  --repo-root <mimickit-checkout> \
  -- --arg_file args/dof_test_humanoid_args.txt --visualize true
```

Use this when a converted motion appears to bend the wrong joint, when hinge signs look inverted, or before authoring a new character-specific converter. If the sweep order or axis does not match your expected `frames[:, 6:]` order, fix the converter/mapping before training.

## Plot a text training log

MimicKit's text logger writes a fixed-width `log.txt` table with headers on the first row. Common x/y keys are `Samples` and `Test_Return`. Use the bundled plotting helper instead of the source plotting script when you need an explicit input and headless-safe output; it preserves the line-and-band plotting behavior of the shared source plotting utility.

```bash
python scripts/plot_training_log.py \
  --log path/to/output/log.txt \
  --out path/to/plots/test_return.png \
  --x-key Samples \
  --y-key Test_Return \
  --title "MimicKit performance"
```

Notes:

- `--log` accepts one or more log files or directories. Directories are expanded to files whose names contain `log`.
- Use `--window N` to average non-overlapping windows before plotting.
- Use `--std-key SomeColumn` when a log contains an explicit standard-deviation column; otherwise multiple logs are aggregated with an empirical band by default.
- TensorBoard event files are viewed with TensorBoard, not this text-log plotting helper.
