# fastMRI Data Formats

Use this reference to validate local `.h5` files before constructing datasets or transforms.

## Directory and Split Pattern

fastMRI loaders expect a split directory containing one HDF5 file per acquisition/volume. Common parent layouts are:

- Knee data: `singlecoil_train`, `singlecoil_val`, `singlecoil_test`, `singlecoil_challenge`, `multicoil_train`, `multicoil_val`, `multicoil_test`, `multicoil_challenge`.
- Brain data: usually `multicoil_train`, `multicoil_val`, `multicoil_test`, `multicoil_challenge`.

Pass the split directory itself to `SliceDataset(root=...)`. For Lightning data modules, the data root is the parent directory and split directories are derived as `<challenge>_<split>`.

## HDF5 Keys by Split

Every file should contain `kspace`:

- Single-coil knee `kspace`: `(slices, height, width)`.
- Multicoil knee/brain `kspace`: `(slices, coils, height, width)`.

Training and validation files normally include targets:

- Single-coil: `reconstruction_esc` is the target used by `SliceDataset` when `challenge="singlecoil"`; `reconstruction_rss` may also be present in source data documentation.
- Multicoil: `reconstruction_rss` is the target used by `SliceDataset` when `challenge="multicoil"`.
- `attrs["max"]` is expected by U-Net and VarNet transforms when target data is present.

Test and challenge files commonly omit target reconstructions and include:

- `mask`: Cartesian sampling mask with one element per k-space width column.
- `target=None` from `SliceDataset.__getitem__` when the reconstruction key is absent.

Write transforms so targetless test/challenge files are legal. `UnetDataTransform` returns a zero target tensor when target is missing, and `VarNetDataTransform` returns `target=torch.tensor(0)` and `max_value=0.0` when target is missing.

## Required Metadata

`SliceDataset` reads `ismrmrd_header` XML from every file during metadata indexing. The header must include:

- `encoding/encodedSpace/matrixSize/{x,y,z}` for encoded dimensions.
- `encoding/reconSpace/matrixSize/{x,y,z}` for reconstruction crop size.
- `encoding/encodingLimits/kspace_encoding_step_1/{center,maximum}` for acquisition padding.

From these fields the loader computes `padding_left`, `padding_right`, `encoding_size`, and `recon_size`, then merges HDF5 attrs into the per-slice attrs dict.

If a tiny local fixture intentionally omits real scanner metadata, use this sub-skill's `scripts/create_tiny_fastmri_h5.py`, which writes a minimal compatible `ismrmrd_header`.

## Dataset Return Contract

Without a transform, `SliceDataset[i]` returns:

```python
(kspace, mask, target, attrs, fname, slice_num)
```

- `kspace` is one slice from the file.
- `mask` is a NumPy array if the file has a `mask` key, else `None`.
- `target` is one target slice if the expected reconstruction key exists, else `None`.
- `attrs` combines HDF5 attrs and parsed metadata.
- `fname` is only the file name, not the full path.
- `slice_num` is the integer slice index.

With a transform, the dataset returns the transform's output directly.

## Layout Checks Before Loading

Run the bundled inspector from this sub-skill's `scripts/` directory on representative files before creating a dataset:

```bash
python scripts/inspect_fastmri_h5.py /path/to/split --max-files 3
```

If the skill has been imported into a central skills directory, first locate `fastmri/sub-skills/data-loading/`, then run the script from that directory or pass the script path explicitly. Check for:

- `kspace` exists and has expected singlecoil or multicoil rank.
- Train/val files include the expected target key for the chosen challenge.
- Test/challenge transforms do not assume a target key exists.
- `ismrmrd_header` parses and reports encoded/recon matrix sizes.
- `mask` width matches the final k-space width for test/challenge data.

## `fetch_dir` Behavior

`fastmri.data.mri_data.fetch_dir(key, data_config_file="fastmri_dirs.yaml")` reads a YAML file containing `knee_path`, `brain_path`, and `log_path`. If the config file is missing, it creates a template with placeholder paths and warns. Prefer explicit paths in agent-written examples; use `fetch_dir` only when the user already uses this config convention.
