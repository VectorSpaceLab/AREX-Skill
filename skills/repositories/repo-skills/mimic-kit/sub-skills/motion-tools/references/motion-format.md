# Motion format and dataset manifests

This reference distills MimicKit's motion data contract from the repository motion source, motion-library source, viewer/DOF environments, dataset YAMLs, and public motion sections.

## Motion pickle schema

A MimicKit motion clip is a Python pickle containing a dictionary with exactly the fields that `Motion.save()` writes and `load_motion(file)` reads:

| Key | Type/shape | Meaning |
| --- | --- | --- |
| `loop_mode` | integer enum value | `0` means `LoopMode.CLAMP`; `1` means `LoopMode.WRAP`. |
| `fps` | positive numeric scalar | Source sampling rate used for length and velocity estimates. |
| `frames` | array-like, saved as nested lists | Converted to `np.float32`; shape must be `(num_frames, 6 + character_dof_size)`. |

The frame vector layout is:

```text
[root position xyz (3), root rotation exp-map (3), joint DoFs]
```

`Motion.get_length()` computes `(num_frames - 1) / fps`, so clips used for interpolation should have at least two frames and a positive FPS. The loader does not deeply validate finiteness, frame count, or character compatibility; future agents should validate those before handing files to MimicKit.

## Loop modes

- `LoopMode.CLAMP` (`loop_mode: 0`) clamps phase to `[0, 1]`; after the clip end, the last frame remains the terminal reference.
- `LoopMode.WRAP` (`loop_mode: 1`) wraps phase by subtracting `floor(phase)`. MotionLib also accumulates a horizontal root-position wrap offset equal to `last_root_pos - first_root_pos` with the vertical component zeroed. Non-wrap clips use a zero wrap offset.
- The `view_motion` environment treats wrapping clips specially for display termination: wrap clips run for five loops before timeout, while clamp clips time out at one clip length.

Choose `WRAP` only for cyclic motions whose first/last pose and horizontal displacement make a sensible loop. Choose `CLAMP` for one-shot actions, AMASS snippets that are not cyclic, diagnostics, and any conversion whose seam has not been inspected.

## Character DoF implications

MimicKit interprets `frames[:, 6:]` through the kinematic character model loaded by the environment's `char_file`:

- spherical joints use 3D exponential-map rotations;
- hinge joints use one scalar angle around the joint axis;
- fixed joints contribute no DoFs;
- the root is not included in the joint DoF tail because root translation and rotation occupy the first six values.

The DoF order follows the character file's kinematic tree order, excluding the root. The public humanoid example orders the tail as abdomen `(3)`, neck `(3)`, right shoulder `(3)`, right elbow `(1)`, left shoulder `(3)`, left elbow `(1)`, right hip `(3)`, right knee `(1)`, right ankle `(3)`, left hip `(3)`, left knee `(1)`, and left ankle `(3)`.

Consequences:

- A motion that loads as a pickle can still be wrong for a character if `frames.shape[1] != 6 + dof_size` for that character.
- A GMR conversion preserves the incoming `dof_pos` tail length; the tiny verified fixture used two DoFs and produced shape `(2, 8)`.
- The bundled SMPL converter writes the SMPL humanoid layout with 69 joint DoFs plus six root values, so the verified tiny fixture produced shape `(2, 75)`.
- Quaternion, axis-angle, and exponential-map values are in radians. Quaternion inputs to the bundled converters use `(x, y, z, w)` order.

## Dataset YAML shape

A single `motion_file` can point directly to one motion pickle or to a YAML dataset manifest. A dataset manifest has this shape:

```yaml
motions:
  - file: "data/motions/example/example_motion.pkl"
    weight: 1.0
  - file: "data/motions/example/another_motion.pkl"
    weight: 2.0
```

Runtime behavior to account for:

- Each `motions` entry must provide `file` and nonnegative `weight`.
- Weights are normalized after all referenced motions load; avoid all-zero weights.
- Paths are consumed as written by the running MimicKit process; they are not rebased relative to the manifest file. Keep them relative to the intended checkout working directory or use explicit paths consistently.
- When MimicKit multiprocessing is enabled and the dataset has at least as many clips as workers, each worker receives a rank-specific contiguous subset before weight normalization.
- Checked source manifests in this repository include `dataset_go2_locomotion.yaml` (7 clips), `dataset_humanoid_locomotion.yaml` (56 clips), `dataset_humanoid_sword_shield.yaml` (82 clips), and `dataset_humanoid_sword_shield_locomotion.yaml` (16 clips).
- The listed motion files are external downloaded assets, not guaranteed to be present in a fresh checkout.

## Validation checklist

Before using a motion or dataset in `view_motion`, AMP/SMP, DeepMimic, or another workflow:

1. Open the pickle safely in a trusted environment and confirm keys `loop_mode`, `fps`, and `frames` exist.
2. Confirm `loop_mode` is `0` or `1`; map it back to `CLAMP` or `WRAP` explicitly in reports.
3. Confirm `fps > 0`, `frames` is 2D, finite, and has at least two frames for interpolation.
4. Confirm `frames.shape[1] == 6 + expected_character_dof_size` for the target `char_file`.
5. Inspect the first and last frame before choosing `WRAP`; cyclic root displacement should be intentional.
6. For a dataset YAML, confirm every `file` exists in the target checkout, every weight is nonnegative, and at least one weight is positive.
7. For viewer workflows, confirm the selected simulator backend, character asset, motion file, and optional key-body names all exist and match the character model.
8. For policy training, route to the relevant algorithm sub-skill after motion validation; this sub-skill does not decide reward or training hyperparameters.
