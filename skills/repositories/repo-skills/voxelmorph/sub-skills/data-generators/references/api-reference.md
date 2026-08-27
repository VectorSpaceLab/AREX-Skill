# API Reference

## Purpose

Use this reference when you need concrete signatures, return shapes, and data-flow details for `voxelmorph.py.utils` and `voxelmorph.py.generators`.

## Verified module surface

### `voxelmorph.py.utils`

| Function | Signature | Use |
| --- | --- | --- |
| `read_file_list` | `read_file_list(filename, prefix=None, suffix=None)` | Read newline-separated paths and apply optional prefix/suffix. |
| `read_pair_list` | `read_pair_list(filename, delim=None, prefix=None, suffix=None)` | Read line-separated source/target pairs. |
| `load_volfile` | `load_volfile(filename, np_var='vol', add_batch_axis=False, add_feat_axis=False, pad_shape=None, resize_factor=1, ret_affine=False)` | Load `.nii`, `.nii.gz`, `.mgz`, `.npz`, or `.npy`; optionally add batch/feature axes, pad, resize, or return affine. |
| `save_volfile` | `save_volfile(array, filename, affine=None)` | Save to NIfTI or compressed `.npz`. |
| `load_labels` | `load_labels(arg, ext=('.nii.gz', '.nii', '.mgz', '.npy', '.npz'))` | Load one or more integer label maps, return unique labels plus the maps. |
| `load_pheno_csv` | `load_pheno_csv(filename, training_files=None)` | Read phenotype CSV into a path→feature dictionary. |
| `pad` | `pad(array, shape)` | Center-pad an array and return both padded array and slice object. |
| `resize` | `resize(array, factor, batch_axis=False)` | Resample an array by an isotropic factor using nearest-neighbor interpolation order 0. |
| `dice` | `dice(array1, array2, labels=None, include_zero=False)` | Per-label Dice overlap. |
| `affine_shift_to_matrix` | `affine_shift_to_matrix(trf, resize=None, unshift_shape=None)` | Convert a 3D affine shift field to a homogeneous matrix. |
| `extract_largest_vol` | `extract_largest_vol(bw, connectivity=1)` | Keep the largest connected component. |
| `clean_seg` | `clean_seg(x, std=1)` | Largest-component cleanup, hole fill, and Gaussian smoothing for a binary mask. |
| `clean_seg_batch` | `clean_seg_batch(X_label, std=1)` | Batch wrapper for `clean_seg`. |
| `filter_labels` | `filter_labels(atlas_vol, labels)` | Zero-out voxels whose labels are not in the allowed set. |
| `dist_trf` | `dist_trf(bwvol)` | Positive distance transform from a binary mask. |
| `signed_dist_trf` | `signed_dist_trf(bwvol)` | Signed distance transform around the mask boundary. |
| `vol_to_sdt` | `vol_to_sdt(X_label, sdt=True, sdt_vol_resize=1)` | Signed-distance transform for one label volume, with optional resize. |
| `vol_to_sdt_batch` | `vol_to_sdt_batch(X_label, sdt=True, sdt_vol_resize=1)` | Batch wrapper for signed-distance transforms. |
| `get_surface_pts_per_label` | `get_surface_pts_per_label(total_nb_surface_pts, layer_edge_ratios)` | Allocate surface-point counts across labels. |
| `edge_to_surface_pts` | `edge_to_surface_pts(X_edges, nb_surface_pts=None)` | Convert a binary edge image into surface points. |
| `sdt_to_surface_pts` | `sdt_to_surface_pts(X_sdt, nb_surface_pts, surface_pts_upsample_factor=2, thr=0.50001, resize_fn=None)` | Convert a signed-distance transform into surface points. |
| `jacobian_determinant` | `jacobian_determinant(disp)` | Determinant of a 2D or 3D displacement field Jacobian. |

### `voxelmorph.py.generators`

| Generator | Signature | Emits |
| --- | --- | --- |
| `volgen` | `volgen(vol_names, batch_size=1, segs=None, np_var='vol', pad_shape=None, resize_factor=1, add_feat_axis=True)` | A tuple of loaded image batches, and optionally segmentation batches. |
| `scan_to_scan` | `scan_to_scan(vol_names, bidir=False, batch_size=1, prob_same=0, no_warp=False, **kwargs)` | `(invols, outvols)` for scan-to-scan registration. |
| `scan_to_atlas` | `scan_to_atlas(vol_names, atlas, bidir=False, batch_size=1, no_warp=False, segs=None, **kwargs)` | `(invols, outvols)` for atlas registration, with optional supervised seg output. |
| `semisupervised` | `semisupervised(vol_names, seg_names, labels, atlas_file=None, downsize=2)` | Source/target images plus discrete-seg probability maps and dummy flow. |
| `template_creation` | `template_creation(vol_names, bidir=False, batch_size=1, **kwargs)` | Unconditional template-training inputs and zero-filled auxiliary outputs. |
| `conditional_template_creation` | `conditional_template_creation(vol_names, atlas, attributes, batch_size=1, np_var='vol', pad_shape=None, add_feat_axis=True)` | Phenotype vector, atlas, and scan batch inputs. |
| `surf_semisupervised` | `surf_semisupervised(vol_names, atlas_vol, atlas_seg, nb_surface_pts, labels=None, batch_size=1, surf_bidir=True, surface_pts_upsample_factor=2, smooth_seg_std=1, nb_labels_sample=None, sdt_vol_resize=1, align_segs=False, add_feat_axis=True)` | Scan/atlas inputs plus signed-distance fields and surface-point clouds. |
| `synthmorph` | `synthmorph(label_maps, batch_size=1, same_subj=False, flip=False)` | `(source, target)` label maps plus a dummy unsupervised target. |

## Behavior notes

### `load_volfile`

- Accepts a path or a preloaded object.
- File handling:
  - `.nii`, `.nii.gz`, `.mgz` → nibabel load, `np.squeeze(img.dataobj)`, affine available when requested.
  - `.npy` → `np.load()` with no affine.
  - `.npz` → key lookup by `np_var`; if only one key exists, that array is used.
- `add_feat_axis=True` appends a trailing singleton channel.
- `add_batch_axis=True` prepends a leading singleton batch dimension.
- `pad_shape` and `resize_factor` apply after loading and before batch expansion.

### `save_volfile`

- Saves NIfTI or `.npz` only.
- `.npz` output is stored under the key `vol`.
- If no affine is provided for 3D NIfTI output, the function writes an internal LIA-style affine.

### `load_labels`

- The maps must be integer typed and have identical shape.
- Accepts a folder, glob, file, or list of these.
- Returned label values are the unique values across all loaded maps.
- Practical note: the current implementation is safest when you pass an explicit `training_files` list to `load_pheno_csv()` and explicit label-map paths to `load_labels()`.

## Generator yield structures

### `volgen`

- Typical output: `tuple(vols)`.
- With `batch_size=2` and `add_feat_axis=True`, a loaded volume batch has shape `(2, *spatial, 1)`.
- If `segs=True`, the generator expects the same `.npz` files to hold both `vol` and `seg` arrays.
- If `segs` is a list, it must match the volume list length.

### `scan_to_scan`

- Input list: `[scan1, scan2]`.
- Output list:
  - `[scan2]` when `bidir=False` and `no_warp=True`.
  - `[scan2, scan1]` when `bidir=True` and `no_warp=True`.
  - Append a zero-flow tensor shaped `(batch, *spatial, ndim)` unless `no_warp=True`.
- `prob_same` can force a source/target pair to be identical with the requested probability.

### `scan_to_atlas`

- Input list: `[scan, atlas]`.
- If `segs` is absent, the output target is the atlas image; if `segs` is present, the output target becomes the corresponding segmentation.
- The cached zero-flow tensor uses the atlas spatial shape.

### `semisupervised`

- Input list: `[src_vol, trg_vol, src_seg_prob]`.
- Output list: `[trg_vol, zeros, trg_seg_prob]`.
- Discrete segmentations are converted to one-hot-like probability volumes over `labels` and downsampled by `downsize`.
- The current implementation is 3D-oriented because it downsamples with three explicit spatial slices.

### `template_creation`

- Input list: `[scan]`.
- Output list: `[scan, zeros, zeros]` or `[scan, zeros, zeros, zeros]` when `bidir=True`.
- The cached zeros use a batch dimension of 1 in the current implementation; keep this in mind if you adapt the generator for larger batches.

### `conditional_template_creation`

- Input list: `[pheno, atlas, vols]`.
- `attributes` must map each volume name to a numeric feature vector.
- The feature vectors are stacked into a `(batch, attr_dim)` phenotype matrix.

### `surf_semisupervised`

- Input list when `surf_bidir=True`:
  - `[X_ret, atlas_ret, X_sdt_k, atl_dt_k, subj_surface_pts, atlas_surface_pts]`
- Input list when `surf_bidir=False`:
  - `[X_ret, atlas_ret, X_sdt_k, atlas_surface_pts]`
- Requirements and limits:
  - `nb_surface_pts > 0`.
  - `batch_size == 1`.
  - `align_segs=True` is only implemented for a single label.
  - Labels are selected from the atlas segmentation and may be sampled per batch.

### `synthmorph`

- Returns `((source, target), np.zeros(0))`.
- `same_subj=True` duplicates the first half of the batch into the second half.
- `flip=True` applies the same random axis flips to both source and target label maps.

## Practical routing advice

- Use `volgen` when you already know the downstream model and only need a clean loader for volumes and optional segmentations.
- Use `scan_to_scan` for pairwise registration without a fixed atlas.
- Use `scan_to_atlas` when a reference atlas is already available.
- Use `semisupervised` when discrete labels should contribute a supervised branch.
- Use `template_creation` or `conditional_template_creation` for atlas/template learning.
- Use `surf_semisupervised` when the training target is surface points rather than voxel overlap.
- Use `synthmorph` when the source images are synthesized label maps and the task ignores real scan loading.
