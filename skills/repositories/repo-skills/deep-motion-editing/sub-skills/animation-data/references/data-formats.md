# Animation data formats

## BVH interchange

BVH is the repository's central interchange format for motion retargeting, 3D style transfer, and Blender visualization. It is plain text and has two sections:

```text
HIERARCHY
ROOT Hips
{
    OFFSET 0 0 0
    CHANNELS 6 Xposition Yposition Zposition Xrotation Yrotation Zrotation
    JOINT Knee
    {
        OFFSET 0 -1 0
        CHANNELS 3 Xrotation Yrotation Zrotation
        End Site
        {
            OFFSET 0 -1 0
        }
    }
}
MOTION
Frames: 2
Frame Time: 0.03333333
0 0 0  0 0 0  0 0 0
...
```

The hierarchy order is the data order. A joint's `OFFSET` is a static rest-pose vector from its parent; it is not a per-frame position. The root normally has six channels (translation then rotation), and every non-root joint has three rotation channels. Some loaders recognize 6-channel joints or 9-channel position/rotation/scale variants, but the model workflows are built around the conventional layout. `End Site` is a terminal marker and has no motion channels; the repository's standard writer emits a zero-offset marker for a leaf. The Blender loader notes that repository BVH uses Y as the height axis while Blender scenes use Z as height and may swap axes at the visualization boundary.

`Frame Time` is seconds per frame. FPS is `1 / frame_time`; do not confuse `0.033333` with 0.033333 FPS. A source file may be 60/120 FPS while the style-transfer pipeline downsamples it (`from_BVH(..., downsample=4)` multiplies the stored frame time by four). The retargeting `BVH_file.write()` emits `1/30` explicitly, so a round-trip through that model adapter can intentionally change temporal sampling.

### Structural invariants

For a conventional file:

- exactly one root is expected;
- each `JOINT` has one parent and unique name in the practical downstream contract;
- the root parent is `-1`, and every parent index is less than its child index in the legacy global routines;
- each joint has three numeric offset values;
- each joint has rotation channels in a declared order, with the root additionally carrying three position channels;
- each motion row has exactly the total number of declared channels;
- the declared `Frames` equals the number of motion rows;
- `Frame Time` is positive and finite;
- offsets and motion values are finite numbers.

The bundled `inspect_bvh.py` checks these structural invariants without importing the legacy `Animation` class. Its parser accepts common whitespace and scientific notation and records `End Site` blocks, but it deliberately does not evaluate every vendor-specific BVH extension.

## Rotations, positions, and topology

The old utility `Animation` stores:

| Field | Shape | Meaning |
| --- | --- | --- |
| `rotations` | `(T, J)` quaternion wrapper or Euler array | Local joint rotations per frame. Quaternion arrays are `(T, J, 4)`. |
| `positions` | `(T, J, 3)` | Animated joint positions; standard BVH has meaningful root translation and derives child positions from offsets. |
| `orients` | `(J,)` quaternions | Optional static local orientations. |
| `offsets` | `(J, 3)` | Rest-pose parent-to-child vectors. Root offset is usually zero. |
| `parents` | `(J,)` integer | Parent index, root `-1`. |

The repository's quaternion wrappers are scalar-first `(w, x, y, z)`, not the `(x, y, z, w)` order used by some graphics packages. Normalize each quaternion before treating it as a rotation. `q` and `-q` represent the same orientation, so direct elementwise equality is not a valid rotation comparison; compare normalized rotation matrices or an absolute quaternion dot product instead.

Kinematics computes a local rotation matrix for every joint, multiplies a child local matrix by its parent's world matrix, rotates the child's static offset, and adds the parent's world position. With root position `p_root`, the common world recurrence is:

```text
world[root] = p_root
world[j] = world[parent[j]] + world_rotation[parent[j]] @ offset[j]
world_rotation[j] = world_rotation[parent[j]] @ local_rotation[j]
```

The PyTorch implementations expose `ForwardKinematics.forward_from_raw`, `forward`, and `transform_from_quaternion`; the NumPy style-transfer path exposes `forward_rotations`. The chosen-joint CMU configuration has 31 full joints and 21 model joints; use the supplied skeleton metadata rather than assuming an arbitrary joint count.

## Retargeting feature layout

`retargeting.datasets.bvh_parser.BVH_file` recognizes one of several hard-coded name lists such as CMU, Mixamo, monkey, or three-arm variants. It simplifies the input to the configured `corps_names` order, maps original joint indices to simplified indices, and identifies five end effectors. `to_numpy(quater=False)` flattens Euler rotations plus root position; `to_numpy(quater=True)` flattens normalized quaternion rotations plus root position. The exact edge subset depends on the selected skeleton's topology. A topology/name mismatch is a model-input error, not a cosmetic warning.

`retargeting.datasets.bvh_writer.BVH_writer` rebuilds a full hierarchy from edges/names. `write()` takes rotations `(T, J, 3)` or `(T, J, 4)`, root positions `(T, 3)`, an order such as `xyz`, and a positive frame time. `write_raw()` takes a torch tensor in `(channels, T)` after the source's transpose convention, with final three channels as root position. It writes a fresh hierarchy; it does not preserve arbitrary source channel order or vendor metadata.

## Style-transfer canonical arrays

For `AnimationData`, the frame-major row is:

```text
[J * 4 rotation values, root_x, root_y, root_z, root_facing, foot_L0, foot_L1, foot_R0, foot_R1]
```

The object reshapes the first `J*4` values into `(T, J, 4)`, normalizes them, and exposes:

- content: `(J*4 + 4, T)` = rotations + root XYZ + root-facing pivot;
- style3d: `((J-1)*3 + 4, T)` = selected non-root global positions + root XYZ + pivot;
- style2d: `(21*2, T) = (42, T)` = 21 projected joints, relative joints followed by root;
- foot contact: `(T, 4)` or `(4, T)` depending on the caller.

The four foot flags are derived from per-frame squared displacement under a fixed velocity threshold in the source helper. They are binary contact hints and may be padded at the first frame. Style transfer uses them to constrain foot-skate correction; they are not included in BVH motion rows.

## OpenPose JSON directory

Each file is expected to resemble:

```json
{
  "people": [
    {
      "pose_keypoints_2d": [x, y, confidence, ...],
      "hand_left_keypoints_2d": [x, y, confidence, ...],
      "hand_right_keypoints_2d": [x, y, confidence, ...]
    }
  ]
}
```

The source loader takes `people[0]`; if it is empty after motion has started, it repeats the previous frame, and then performs a backward fill for remaining zeros. It concatenates body, left-hand, and right-hand arrays, maps selected OpenPose indices to 21 style joints, synthesizes midpoints for missing spine/hand-root joints, flips the image y-axis, subtracts the first root, optionally applies Gaussian smoothing with sigma 2, and scales by 0.07. `validate_openpose_json.py` only validates and reports these preconditions; it does not mutate missing detections or perform smoothing.

Frame order is a practical hazard. The legacy code uses `sorted(os.listdir(json_dir))`, then truncates to `len(files)//4*4`; non-JSON files can therefore be misread and non-contiguous names can silently alter temporal order. The validator accepts JSON files only, extracts a numeric frame token where possible, reports gaps/duplicates, and reports the effective multiple-of-four prefix. Rename or regenerate a contiguous, zero-padded sequence before inference.

## Result artifacts

Style-transfer test output convention:

```text
<output directory>/raw.bvh    # direct generated motion
<output directory>/fixed.bvh  # after foot-contact / IK cleanup
```

Retargeting demos use their own output names and may call an IK fix separately. Treat `raw.bvh` as the reproducible network serialization and `fixed.bvh` as a postprocessed derivative. Compare the same skeleton, frame time, and frame count before attributing differences to the model. Neither file embeds contact flags; retain the model-side contact tensor alongside outputs if you need to reproduce cleanup.
