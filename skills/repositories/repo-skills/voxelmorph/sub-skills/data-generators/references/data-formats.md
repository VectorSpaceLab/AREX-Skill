# Data Formats

## Purpose

Read this when you need the exact file and tensor conventions that VoxelMorph data loaders expect.

## Volume containers

### Supported by `load_volfile`

| Extension | Behavior |
| --- | --- |
| `.nii` / `.nii.gz` | Loaded with nibabel, squeezed to remove singleton dimensions, affine available when requested. |
| `.mgz` | Loaded with nibabel the same way as NIfTI. |
| `.npy` | Loaded with `np.load()`; no affine metadata is returned. |
| `.npz` | Loaded by key lookup. Use `np_var='vol'` for standard multi-array files; if the archive contains exactly one array, that array is used. |

### Standard VoxelMorph `.npz` convention

- `vol` holds the image volume.
- `seg` is optional and holds a discrete segmentation map.
- `save_volfile()` stores compressed `.npz` files under the `vol` key.
- `volgen(..., segs=True)` expects both `vol` and `seg` to be present in the same `.npz` file.

## Array layout conventions

### Base loading

- `load_volfile(..., add_batch_axis=True)` prepends a batch dimension.
- `load_volfile(..., add_feat_axis=True)` appends a feature/channel dimension.
- Most generator outputs therefore use the shape pattern `(batch, *spatial, features)`.
- `resize(array, factor, batch_axis=False)` expects the trailing axis to be a feature axis.

### Typical shapes by workflow

| Workflow | Typical input shapes | Notes |
| --- | --- | --- |
| scan-to-scan / scan-to-atlas | `(batch, *spatial, 1)` | Volumes usually arrive with a singleton feature axis. |
| semisupervised | `(batch, *spatial, 1)` for images and `(batch, *spatial, n_labels)` for label probabilities | Discrete labels are converted to label stacks. |
| template creation | `(batch, *spatial, 1)` | Output uses the current implementation's cached zero-flow tensors. |
| surface semisupervised | `(batch, *spatial, 1)` plus surface arrays shaped `(batch, nb_surface_pts, ndim+1)` | Final surface column stores the label index. |
| SynthMorph | `(batch, *spatial, 1)` | The generator returns two label-map batches and a dummy target. |

## List and pair files

### `read_file_list`

- One entry per non-empty line.
- Optional `prefix` and `suffix` are string concatenations, not path joins.

### `read_pair_list`

- Each line is split by the requested delimiter, or whitespace when `delim=None`.
- Optional `prefix` and `suffix` are applied to both elements in each pair.

## Labels and segmentation

### `load_labels`

- Label maps must all have the same shape.
- Label maps must be integer typed.
- A folder, glob, single path, or list of these may be supplied.
- The function returns the sorted unique labels plus the loaded maps.

### `clean_seg` / `clean_seg_batch`

- Intended for binary masks derived from a single label.
- The smoothing step uses the requested standard deviation; zero or very small masks can fail the volume-preservation assertion.

### `filter_labels`

- Keeps only the requested labels and zeros everything else.
- Useful before signed-distance or surface extraction.

## Atlas and phenotype inputs

### `scan_to_atlas`

- `atlas` should already be a batch-shaped tensor/array compatible with the scan batch.
- The code repeats the atlas across the requested batch size.
- If `segs` is provided, the segmentation output becomes the supervised target.

### `conditional_template_creation`

- `atlas` is a batch-shaped reference volume.
- `attributes` must be a dictionary keyed by the exact volume names used in `vol_names`.
- Each attribute value must be a numeric vector that can be stacked into a batch matrix.

### `surf_semisupervised`

- `atlas_vol` and `atlas_seg` are plain arrays, not batches.
- `atlas_seg` is filtered to the requested labels before signed-distance transforms are built.
- `nb_labels_sample` controls per-batch label subsampling.

## README-derived assumptions

The repository README states the following data expectations for this branch:

- Training data may be NIfTI, MGZ, or `.npz`.
- For standard training, each `.npz` file should contain `vol`, and semisupervised workflows may also use `seg`.
- Shapes across the training list should be consistent unless you deliberately customize the generator.
- Images for registration should be affinely aligned before the registration script consumes them.
- SynthMorph-style examples use normalized images or synthesized label maps rather than downloading a special dataset inside the skill.

## Handy validator targets

Use the bundled validator when you want a quick schema check for local `.npz` files:

- missing `vol` key
- missing or mismatched `seg` key
- non-integer segmentation labels
- NaNs or infinities in the arrays
- shape inconsistency across a file list
- labels outside an expected allowed set
