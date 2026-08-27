# Motion tools troubleshooting

## Install/import problems

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError: mimickit` while running a bundled converter | The target checkout was not made importable, or the checkout is script-oriented rather than installed as a package. | Pass `--repo-root path/to/mimickit-checkout` if you want the helper to use the target `Motion` class. The bundled converters can also write schema-compatible pickles without importing MimicKit. |
| `ModuleNotFoundError: numpy` or `matplotlib` | The Python environment lacks basic requirements. | Install the target checkout requirements or the missing plotting/conversion dependency in the active environment. |
| A converter works from one directory but not another | A script or wrapper relied on current working directory. | Use the bundled scripts with explicit input/output paths and, only if needed, explicit `--repo-root`. Do not depend on `sys.path.append(".")` behavior from source tools. |

## Invalid motion shapes

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `Expected root_pos shape (N, 3)` or `root_rot shape (N, 4)` | GMR input keys exist but arrays have the wrong rank/order. | Re-export or reshape the source data; `root_rot` must be quaternion `(x, y, z, w)`, not Euler angles or `(w, x, y, z)`. |
| `root_pos, root_rot, and dof_pos must have the same frame count` | Clipped or separately sampled arrays were combined incorrectly. | Align all arrays to the same frame count before conversion, then use `--start_frame`/`--end_frame` for final trimming. |
| Motion loads but the character explodes or joints are scrambled | `frames[:, 6:]` does not match the selected character's DoF count or order. | Use the motion-format validation checklist and the DOF test workflow. Confirm hinge versus spherical joint dimensions and depth-first character order. |
| SMPL converter raises a pose-size error | AMASS file has fewer than the first 66 SMPL pose parameters required by this converter. | Use a standard SMPL/AMASS `poses` array or adapt the source mapping intentionally before conversion. |
| `Invalid frame range` | `--start_frame`/`--end_frame` did not satisfy `0 <= start < end <= num_frames`. | Inspect the input frame count and remember `--end_frame -1` means through the final frame. |

## Quaternion, rotation, and axis-order mistakes

- GMR root quaternions are expected in `(x, y, z, w)` order. `(w, x, y, z)` input usually produces large orientation errors rather than a clean exception.
- MimicKit frame rotations are exponential maps in radians, not degrees.
- SMPL conversion applies the preserved Y-up/Z-up correction. If a sequence lies sideways or underground, compare `--z_correction none`, `calibrate`, and `full`, then inspect the root transform before blaming the policy.
- For cyclic clips, inspect the first/last frame before using `--loop wrap`; a bad seam causes root-position jumps because wrap mode accumulates horizontal root displacement.

## Missing motions, models, assets, or configs

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `FileNotFoundError` for `data/motions/...` | Motion archives were not downloaded or the converted output was saved elsewhere. | Download/extract the data required by the checkout or update `motion_file` to the actual converted pickle/dataset path. |
| `FileNotFoundError` for non-humanoid character assets | Some presets refer to assets that may not be present in a shallow checkout. | Use a preset whose `char_file` exists or install/download the missing assets before running viewer or DOF workflows. |
| A dataset YAML loads no useful clips | All weights are zero, files are missing, or paths are relative to a different working directory. | Validate each `motions` entry, use nonnegative weights with a positive sum, and run from the intended checkout root or use explicit paths. |
| Viewer config references key bodies that are absent | The selected character asset differs from the preset's key-body list. | Update key-body names to match the character, or omit them for a minimal visualization check. |

## Viewer/backend failures

`view_motion` and `char_dof_test` are simulator-native workflows. They require a supported external backend such as Isaac Gym, Isaac Lab/Isaac Sim, or Newton/Warp, plus compatible GPU/device setup and local assets. Lightweight verification for this generated skill covered CPU/CUDA torch imports, parser help, compile checks, and tiny converter fixtures only; it did not prove simulator-native viewer startup.

Actions:

1. Route backend installation, engine YAML choice, `--devices`, and runner mechanics to `runner-and-backends`.
2. Start with a small `--num_envs` and the simplest character whose asset and motion file are known to exist.
3. If rendering fails in a headless session, distinguish simulator import/device errors from display/windowing errors; try a backend-supported headless/video workflow only after backend setup is confirmed.
4. If body markers draw in the wrong places, check the key-body names and the motion's root/DoF mapping before tuning a policy.

## Conversion-source path mismatch

The source GMR README used an outdated converter path under `tools/data_format_conversion/`, but the actual source converter lived under `tools/gmr_to_mimickit/`. Future agents should use this sub-skill's bundled `scripts/convert_gmr_to_mimickit.py` rather than either source path.

## Log plotting failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `Missing x/y key` | The selected `--x-key` or `--y-key` is not a column in the text log. | Re-run the plotting helper with the default `Samples`/`Test_Return` or one of the printed available columns. |
| Empty plot or window error | `--window` is larger than the available rows, or the log only has a header. | Use a smaller window and confirm the run wrote numeric rows. |
| `UnicodeDecodeError` or parse errors | The file is not a MimicKit text log, or it is a TensorBoard event file. | Use TensorBoard for event files; use the plotting helper only for text tables. |
| Plot tries to open a GUI | A non-headless plotting script was used. | Use the bundled `plot_training_log.py`, which saves to `--out` with an Agg backend unless `--show` is requested. |
