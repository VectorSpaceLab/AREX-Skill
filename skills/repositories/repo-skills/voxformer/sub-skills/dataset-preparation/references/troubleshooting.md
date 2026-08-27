# Dataset troubleshooting

## Missing or unexpectedly empty files

- **No `dataset/` under the supplied root:** pass the parent that contains
  `dataset/`, not a sequence directory and not the repository's `preprocess/`
  directory. Confirm the resolved path before any command.
- **No stage-1 `.pseudo` files:** check the exact
  `sequences_<depthmodel>_sweep<nsweep>/<seq>/voxels/` name. The standard
  configs use `sequences_msnet3d_sweep10`; changing either config parameter
  changes the lookup path.
- **No stage-2 queries:** the loader searches `queries/*.<query_tag>`. A
  generic `000000.query` does not satisfy the standard tag. Query proposals are
  separate from voxelized pseudo-LiDAR and are not produced by
  `lidar2voxel.py`.
- **No labels:** train/validation runtime samples require the configured
  target under `dataset/labels/<seq>`. Stage 1 needs `_1_2.npy`; stage 2 needs
  `_1_1.npy`. Test-mode placeholders are not ground truth.
- **Missing `velodyne/`:** it is a source-data warning when already-prepared
  pseudo files are being consumed, but it blocks a fresh depth/pseudo-LiDAR
  conversion. Missing raw `voxels/*.label` or `*.invalid` blocks label
  conversion.

Run the checker with `--sequence <seq> --stage stage1|stage2|both` to get
frame-specific errors. Do not silence missing-file errors by changing the
query tag unless the model config and artifact producer use that same tag.

## Shape, size, or frame-name mismatch

- Images and generated artifacts must use six-digit IDs such as `000005`, not
  integer names such as `5` or a depth predictor's alternate prefix.
- `_1_1.npy` is expected to load as `(256,256,32)`; `_1_2.npy` is expected to
  load as `(128,128,16)`. A successful `np.load` alone does not establish that
  the array corresponds to the same frame.
- Packed `.pseudo` and query occupancy files are unpacked eight values per
  byte. The checked-in `(256,256,32)` map implies `262144` bytes. A short file
  usually means interrupted generation; a different complete format must be
  proven against the consumer before use.
- The checker can inspect NumPy shape and byte count, but cannot establish
  semantic class correctness, point ordering, depth scale, or query quality.

## Calibration and pose errors

- `calib.txt` must have parseable `P2:` and `Tr:` rows with 12 numeric values
  each. The repository reshapes these to 3x4; missing keys or extra/malformed
  fields cause projection failures.
- `poses.txt` must have 12 numeric values per non-empty row. Stage 2 indexes the
  pose list with frame IDs and uses inverse transforms for temporal references;
  a file with fewer rows than the image/query IDs is invalid.
- Check that `P2` and `Tr` came from the same sequence and that copied pose and
  calibration files were not mixed across sequence IDs. Numeric parseability is
  not calibration correctness.
- A zero-length or truncated calibration/pose file should be treated as a
  source failure, not repaired by inventing identity matrices.

## Label conversion and invalid values

`label_preprocess.py` uses the checked-in SemanticKITTI learning map. It reads
raw `.label` values as `uint16`, unpacks `.invalid`, remaps to the 20-class
space, marks invalid voxels as `255`, and writes both scales. Verify that the
`.label` and `.invalid` lists are sorted and paired by frame before an approved
conversion. Do not hand-edit `.npy` labels to make the checker pass. If a
custom label mapping is desired, route the change through model/configuration
and document the new class contract; it is not a dataset-layout fix.

## Permissions, links, and partial generation

- The checker is read-only, but it may follow symlinks while testing existence.
  Ensure the user owns the target and that a symlink does not redirect output
  into an unrelated experiment.
- `mkdir -p`, output saves, and the wrapper's symlink creation are mutating
  operations. Review destinations and free space before running them.
- If a job stopped halfway, preserve the partial output for diagnosis. Re-run
  only after checking which frames are complete and whether the producer skips
  existing files or overwrites them. Do not delete real data as a repair step.

## Optional image-to-depth backend

The repository's preparation notes describe MobileStereoNet in a separate old
runtime (Python 3.6, PyTorch 1.4.0, torchvision 0.5.0, CUDA 10.0). It requires
a GPU, checkpoint, filename lists, and substantial image/output storage. The
main CPU utilities importing successfully does not make this backend available,
and there is no claimed CPU substitute. Route installation, CUDA, checkpoint,
and ABI issues to `../environment-and-installation/`; report the backend as
optional/unverified rather than silently substituting a different depth model.

## CLI misuse and safe recovery

- Run `validate_dataset_layout.py --help` first. `--root` is the user data root;
  `--sequence` may be repeated; `--stage` controls the contract being checked.
- Use `--require-raw-voxels` only when raw label/occupancy inputs are expected;
  it is not needed for a supplied runtime-ready artifact bundle.
- A nonzero checker exit means the requested contract is not proven. It does
  not authorize generation, download, or deletion. Fix the reported path or
  route to the owner sub-skill, then rerun the same deterministic check.
