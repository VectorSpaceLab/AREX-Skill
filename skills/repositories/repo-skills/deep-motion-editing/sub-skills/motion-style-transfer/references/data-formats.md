# Style-transfer data formats

## BVH and canonical motion

Style transfer uses the shared `AnimationData` and a CMU-derived skeleton. The
checked-in `skeleton_CMU.yml` describes a 31-joint topology, a 21-joint
`chosen_joints` subset, parent arrays, four foot joints, hips, shoulders, and a
head. Its `BVH: rest.bvh` entry points to the matching rest skeleton. Use the
adjacent animation-data skill for complete BVH grammar and safe inspection;
this page states the style model's channel contract.

A canonical full row is:

```text
31 joints * 4 quaternion values + 3 root-position values
+ 1 root-facing pivot + 4 foot-contact values = 132 values
```

`AnimationData` normalizes quaternions on load. Root position is three values,
root rotation/pivot is one, and foot contact is four channels. The source uses
30-FPS-like data after downsample 4; `from_BVH` multiplies input frame time by
that downsample factor.

The model's pre-batch `[C,T]` views are:

| View | Construction | Channels |
|---|---|---:|
| Content | 31 quaternion joints plus root position and pivot | 128 |
| 3D style | 20 non-root chosen-joint positions plus root position and pivot | 64 |
| 2D style | 21 projected joints with x/y coordinates | 42 |

`get_style3d_input` runs forward kinematics, removes the root from the 21
chosen joints, flattens 20 positions, and appends root position/pivot.
`get_projections` projects 21 joints; the 2D representation stores relative
joints and root in the source's channel order. The decoder emits `31*4=124`
rotation channels; forward kinematics supplies positions and the saved root
channels are merged before BVH output.

This is not a skeleton converter. Mismatched joint count, topology, rest
skeleton, quaternion convention, axis, or scale can cause import errors or
plausible-looking incorrect motion. Retarget first when the input skeleton is
not compatible.

## OpenPose JSON directory

`AnimationData2D.from_openpose_json` sorts every directory entry, keeps the
largest prefix whose length is a multiple of four, and opens those entries. It
does not filter names by `.json`; unrelated files can fail. Each selected file
must contain a `people` list. The first person is used and must have these
flattened arrays:

- `pose_keypoints_2d`: repeating body `x,y,confidence` triples;
- `hand_left_keypoints_2d`: repeating left-hand triples;
- `hand_right_keypoints_2d`: repeating right-hand triples.

Confidence is discarded. Body, left-hand, and right-hand x/y coordinates are
concatenated. The evidenced target mapping has 21 joints: mapped body points
include root and limbs; targets 12, 16, and 20 are synthesized from body/hand
indices, and targets 9 and 11 are midpoint joints. In particular the source
uses concatenated indices 35 for target 16 and 56 for target 20. Do not claim
that arbitrary body-only OpenPose output, another keypoint order, or a custom
multi-person schema is supported.

Initial empty `people` frames are skipped. Once a person has appeared, an empty
frame repeats the previous frame. Zero coordinates in later frames are filled
from the previous frame, then a reverse pass fills earlier zeros from the next
frame. The sequence is vertically flipped, translated so the first root is
zero, optionally smoothed by `scipy.ndimage.gaussian_filter1d(sigma=2,
axis=0)`, and multiplied by `scale=0.07`. There is no camera calibration, FPS
conversion, confidence output, or multi-person selection.

`get_style2d()` returns `[42,T]`: relative coordinates for 20 target joints and
the root coordinates. `process_single_json` normalizes it with a stored 42-
channel mean/std archive.

## Training archive

`export_train.py` uses `AnimationData.from_BVH(..., downsample=4)`, computes full
motion plus a temporary phase column, divides windows, then stores motion
without phase. Each `.npz` has object-valued `train`, `test`, and `trainfull`
entries. Each subset conceptually contains:

```python
{
  "motion": [array(T, 132), ...],
  "style": [integer_class, ...],
  "meta": {"style": [...], "content": [...], "phase": [...]}
}
```

Xia uses style/content/phase metadata; BFA uses style and phase metadata in the
shared conversion. The `.info` sidecar is YAML with subset counts and label
distributions; Xia also lists `test_files`. NPZ object arrays require
`allow_pickle=True` when loaded by the source.

`xia_dataset.yml` requires `style_names`, `content_full_names`,
`content_names`, and `content_test_cnt`. Xia filenames are
`<style>_<content-index>_<suffix>.bvh`; its checked-in style labels are
`angry`, `childlike`, `depressed`, `neutral`, `old`, `proud`, `sexy`, and
`strutting`. `bfa_dataset.yml` requires `style_names`; BFA filenames are
`<style>_<suffix>.bvh`, with 16 checked-in labels: Angry, Depressed, Drunk,
FemaleModel, Happy, Heavy, Hurried, Lazy, Neutral, Old, Proud, Robot, Sneaky,
Soldier, Strutting, Zombie. Labels are case-sensitive.

## Window and split rules

The source shell passes `window=32`, `window_step=8`; the exporter parser
itself defaults to `window=48`, `window_step=8`. Xia divided windows start at
`-(window//4)` and advance by `window_step`, stopping when fewer than three
quarters of a window remain. BFA starts at zero with the ordinary range. For
non-divided clips the source rounds to a multiple of four, enforces a minimum
of 12 frames, and reflection-pads short clips. Active generation downsample is
4 and is not an exporter CLI option. Changing temporal rate requires regenerating
archives and norms together.

## Normalization and output artifacts

Training `NormData` computes channel-wise means/stds from raw data, writes
`<prefix>_<key>.npz`, and changes exact zero std to `1e-9`. Required archives
contain `mean` and `std`; default test/trainfull config reuses `train_*` files.
Inference 3D requires `train_content.npz` and `train_style3d.npz`. 2D style
uses the source-relative `test2d.npz` and has 42 channels.

`raw.bvh` is saved from network output using `AnimationData.from_network_output`
and the shared BVH writer. `fixed.bvh` uses the same motion plus content foot
contact after floor estimation, contact pinning/interpolation, and Jacobian IK.
They are not aliases. Validate both file existence and skeleton compatibility;
use `raw.bvh` for model diagnosis and `fixed.bvh` for cleanup/rendering.
