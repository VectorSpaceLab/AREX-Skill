# Animation-data API reference

The repository is script-oriented rather than an installable distribution. The
names below are source APIs distilled from the inspected files; they require a
user-owned checkout with its documented working directory and dependencies.
The bundled validators do not import these modules.

## BVH loading and serialization

### `BVH.load`

`BVH.load(filename, start=None, end=None, order=None, world=False)` returns
`(anim, names, frametime)`.

- `anim` contains `rotations`, `positions`, `orients`, `offsets`, and integer
  `parents`.
- After Euler conversion, rotations are normally `(T, J, 4)` quaternions in
  scalar-first `(w, x, y, z)` order. `positions` is `(T, J, 3)`; root motion
  comes from root channels and child positions are normally derived from
  offsets.
- `names` is hierarchy order. `parents[0] == -1`; old global transforms
  require each parent index to precede its children.
- `frametime` is seconds per frame. `start`/`end` are source slicing controls,
  not time values.
- Common 3-, 6-, and 9-channel rows are recognized, but downstream model code
  normally expects a six-channel root and three rotation channels per child.

`BVH_mod.load(filename, ..., need_quater=False)` is the variant that handles
joint names containing a colon and can preserve Euler arrays when requested.
Do not mix loader variants without checking Euler order and whether rotations
are in degrees or quaternion form.

### `BVH.save`

`BVH.save(filename, anim, names=None, frametime=1/24, order='zyx',
positions=False, orients=True)` emits a hierarchy and motion section.
`positions=False` normally writes root position channels and child rotations;
`positions=True` writes position channels for every joint. The `order` string
controls the three emitted rotation channel names. Confirm the chosen order
before comparing poses: changing `xyz` to `zyx` can preserve topology but alter
orientation.

### `BVH_file`

`retargeting.datasets.bvh_parser.BVH_file(file_path=None, args=None,
dataset=None, new_root=None)` loads via the retargeting BVH utility, strips a
namespace prefix before `:`, recognizes a hard-coded skeleton family, and
constructs a simplified list.

| API | Contract |
| --- | --- |
| `names` | Simplified joint names in model order. |
| `topology` | Simplified parent tuple; root is `-1`. |
| `offset` | Simplified static offsets, shape `(J, 3)`. |
| `get_position()` | Loaded positions restricted to selected joints, `(T, J, 3)`. |
| `to_numpy(quater=False, edge=True)` | Flattened rotations plus root positions. Euler mode starts as `(T, J*3 + 3)`; quaternion mode uses `(T, J*4 + 3)`. Edge selection follows the selected skeleton. |
| `to_tensor(quater=False, edge=True)` | The same feature data converted to the retargeting channel/time tensor convention. |
| `get_ee_id()` | Five configured end-effector indices. The order depends on the skeleton family. |
| `get_height()` | Offset-chain estimate through the first foot and head end effectors; not a measured world-space height. |
| `get_ee_length()` | End-effector chain lengths normalized by the estimated height. |
| `write(path)` | Reconstructs the simplified motion with `BVH_writer`, Euler `xyz`, and a hard-coded `1/30` frame time. |

An unknown joint set raises `Unknown skeleton`; a partial name match should not
be forced into the nearest family. Add and verify a complete family mapping in
the downstream retargeting workflow for a new dataset.

### `write_bvh` and `BVH_writer`

`write_bvh(parent, offset, rotation, position, names, frametime, order, path,
endsite=None)` expects Euler rotations `(T, J, 3)` and root positions `(T, 3)`.
It writes a six-channel root, three-channel children, static offsets, recursive
children, `Frames`, `Frame Time`, and a zero-offset `End Site` for a leaf when
no explicit end-site record is supplied.

`BVH_writer(edges, names)` derives the parent tree and exposes:

```text
write(rotations, positions, order, path, frametime=1/30, offset=None, root_y=None)
write_raw(motion, order, path, frametime=1/30, root_y=None)
```

`write` accepts Euler `(T, J, 3)` or quaternion `(T, J, 4)` rotations. For
`order='quaternion'`, the source normalizes, converts to Euler, and emits
`xyz`; callers must not expect quaternion channels in the resulting BVH.
`write_raw` accepts a torch tensor in channel-by-time layout, transposes it,
and treats the final three channels as root positions. Validate dimensions and
quaternion norms before calling either method. Keep `raw.bvh` before cleanup.

## Style-transfer animation APIs

### `AnimationData`

`utils.animation_data.AnimationData(full, skel=None, frametime=1/30)` expects a
frame-major NumPy array:

```text
full: (T, J*4 + 8)
      [J*4 quaternion values | root xyz | root-facing pivot | 4 foot flags]
rotations:     (T, J, 4), scalar first and normalized
rt_pos:        (T, 3)
rt_rot:        (T, 1)
foot_contact:  (T, 4)
```

Key methods:

- `from_BVH(filename, downsample=4, skel=None, trim_scale=None)` loads BVH,
  samples every `downsample` frames, optionally trims to a multiple, and
  derives canonical root-facing rotation and contacts.
- `from_network_output(input)` accepts channel-by-time generated output,
  transposes it, and appends four zero contact channels.
- `from_rotations_and_root_positions(rotations, root_positions, skel=None,
  frametime=1/30)` normalizes rotations, computes world positions, contacts,
  and a facing pivot.
- `get_content_input()` returns `(J*4 + 4, T)` = rotations, root XYZ, pivot.
- `get_style3d_input()` returns `((J-1)*3 + 4, T)` from selected non-root
  world positions plus root parameters.
- `get_projections(view_angles, scales=None)` returns `(V, J*2, T)`.
- `get_global_positions(trim=True)` returns selected `(T, J_selected, 3)`;
  `trim=False` uses the full skeleton.
- `get_foot_contact(transpose=False)` returns `(T, 4)` or `(4, T)`.
- `get_BVH(forward=True)` returns `(anim, names, frametime)` and may rotate the
  root into the nearest cardinal forward direction.

The standard CMU YAML describes the complete topology, selected joints,
left/right foot indices, hips, shoulders, head, and visualization settings.
Always use the matching skeleton metadata rather than copying indices.

### `AnimationData2D`

`AnimationData2D.from_openpose_json(json_dir, scale=0.07, smooth=True)` returns
an input projection `(T, 21, 2)`. It reads `people[0]` from each OpenPose JSON,
concatenates body and two hand arrays, maps them to 21 style joints, flips the
image y axis, subtracts the first root, optionally applies Gaussian smoothing,
and scales the result. `get_projection()` returns `(T, 21, 2)`;
`get_style2d()` returns relative-joints-plus-root `(42, T)`;
`from_style2d()` reverses that layout.

`style_transfer.data_loader.process_single_bvh(filename, config,
norm_data_dir=None, downsample=4, skel=None, to_batch=False)` returns
normalized content/style3d, raw targets, and foot contact. Its JSON counterpart
`process_single_json(json_dir, config, norm_data_path=..., scale=0.07,
smooth=True, to_batch=False)` returns normalized 2D style input. Both require
normalization `.npz` and a configured device; they are not lightweight checks.

## Kinematics and cleanup touchpoints

- `style_transfer.kinematics.ForwardKinematics.forward_from_raw(rotation,
  world=True, quater=True)` accepts `(B, J*4, T)` and returns world positions
  `(B, T, J, 3)`. `forwardX` trims selected non-root features.
- `utils.animation_data.forward_rotations(skel, rotations, rtpos=None,
  trim=True)` accepts `(T, J, 4)` and composes rotations/offsets.
- `utils.Animation.positions_global(anim)` and `rotations_global(anim)` are
  legacy helpers dependent on incremental parent ordering and the old import
  chain.
- `style_transfer.remove_fs.nrot2anim(nrot)` reconstructs generated motion;
  `remove_fs(anim, foot, output_path, fid_l=(4,5), fid_r=(9,10),
  interp_length=5, force_on_floor=True)` holds contact intervals, interpolates
  short gaps, applies IK, and writes a corrected BVH. The source CLI batches
  tensors and writes several files, so it is intentionally not bundled.
- `retargeting.models.IK.fix_foot_contact(input_file, foot_file, output_file,
  ref_height)` is a separate cleanup path whose end-effector order is selected
  by names. Do not pass style-transfer contact channels to it without mapping.

A bundled structural parser passing does not prove PyTorch, SciPy, YAML, IK, or
Blender imports. Run the downstream workflow's dependency preflight separately.
