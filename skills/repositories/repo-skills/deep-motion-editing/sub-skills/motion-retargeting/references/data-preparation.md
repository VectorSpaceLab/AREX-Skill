# Retargeting data preparation

## Expected Mixamo-style tree

Place source FBX/BVH characters below a user-owned dataset root, normally
`retargeting/datasets/Mixamo/`:

```text
Mixamo/
  Aj/
    motion one.bvh
    motion two.bvh
  BigVegas/
    motion one.bvh
  ...
  std_bvhs/
    Aj.bvh
    BigVegas.bvh
  mean_var/
    Aj_mean.npy
    Aj_var.npy
    BigVegas_mean.npy
    BigVegas_var.npy
  train_list.txt
  test_list.txt
```

`datasets/__init__.py` hard-codes the training and test character groups. The
runtime `--dataset` option is not a general registry: training's `MotionData`
uses it for a `.npy` filename, but `MixedData` still receives the hard-coded
character names. A custom dataset therefore requires source-level updates to
the character list and skeleton definitions, plus matching standard and
statistics artifacts.

Each character's files should use a common T-pose convention and compatible
frame rate/conventions. The source downsamples motion by `motion[::2]` and the
README's original Mixamo workflow assumes 60 FPS input downsampled to 30 FPS.
The parser/writer uses a 30 FPS-style default (`Frame Time: 1/30`) when writing.
Do not mix skeletons merely because they have the same number of joints;
`BVH_file` matches names, hierarchy, offsets, and five end-effectors.

Use the bundled validator before preprocessing:

```bash
python .../validate_retargeting_data.py --dataset-root <Mixamo>
python .../validate_retargeting_data.py --bvh <Mixamo/Aj/motion.bvh>
```

## Source preprocessing sequence

The README's order is:

1. **Acquire data manually** from Mixamo or use a supplied preprocessed
   archive. The repository's `datasets/download_test.sh` downloads an external
   Google Drive archive with `wget`, extracts it, and deletes the archive. It
   is reference-only here: this skill never downloads or deletes files.
2. **Convert FBX to BVH** with Blender from `retargeting/datasets`, using
   `blender -b -P fbx2bvh.py`. The source script bulk-walks `./Mixamo/<char>`
   and exports with `root_transform_only=True`; this is an external Blender
   operation and belongs to
   [`../blender-visualization/SKILL.md`](../../blender-visualization/SKILL.md).
   Skip it if BVH files already exist.
3. **Optionally split joints** with `python datasets/split_joint.py`. The
   source finds every dataset directory, detects only skeleton type 1, and
   writes a new `<character>_m` directory. It splits `Spine1`,
   `LeftShoulder`, and `RightShoulder`, halves offsets, inserts identity
   rotations, and changes the `Spine1` offsets to a three-part average. It
   rewrites files; make a copy and inspect the result before using it.
4. **Preprocess** with `python datasets/preprocess.py` from `retargeting`.
   For every character directory except `std_bvhs` and `mean_var`, it loads
   all `.bvh` files, calls `BVH_file.to_tensor().permute((1, 0))`, saves a
   character `.npy`, copies the first BVH to `std_bvhs/<character>.bvh`, and
   computes `<character>_mean.npy` and `<character>_var.npy` by constructing a
   `MotionData` instance with augmentation disabled. Ensure every character
   has at least one valid BVH; the original uses shell `cp` and assumes the
   directories already exist.
5. **Train** only after the validator finds list files, character data,
   standard BVHs, and mean/var files. Preprocessing and training can be long
   and should be explicitly run by the user.

The bundled `validate_retargeting_data.py` intentionally does not reimplement
preprocess or mutate data. It catches malformed hierarchy/frames and reports
missing generated directories, but it does not know every custom skeleton name
or guarantee `BVH_file` classification.

## Standard BVHs, statistics, and para.txt

A standard BVH is one representative static-offset reference per character;
`get_std_bvh()` resolves it as `./datasets/Mixamo/std_bvhs/<dataset>.bvh`.
`mean_var/<character>_mean.npy` and `_var.npy` must match the flattened tensor
channel order produced by the simplified parser. The source replaces standard
deviations below `1e-5` with one at load time, but mismatched shapes still
fail. The training output's `para.txt` records the exact command line and is
needed by later evaluation to reconstruct architecture options.

## Tiny preprocessing fixture

For a bounded smoke check, create a temporary character directory containing a
small valid BVH with at least the joint names required by one supported
skeleton definition and a few frames, then run only the standalone validator.
A one- or two-joint generic BVH proves textual parsing but is expected to fail
source skeleton classification; do not call that a successful model fixture.
A useful synthetic test should include two character directories and a motion
filename with spaces, then verify validator output and command construction
without invoking `preprocess.py` or a checkpoint loader.
