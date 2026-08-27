# Dipy IO Data Formats

Use this reference to choose loaders/converters and to validate shape, orientation, reference, and metadata assumptions before scientific processing.

## NIfTI Images

Dipy image IO is nibabel-backed and normally targets `.nii` or `.nii.gz` files.

| Component | Expected shape/content | Practical guidance |
| --- | --- | --- |
| 3D scalar image | `(X, Y, Z)` | Masks, scalar maps, b0 outputs, extracted volumes, GFA/FA/MD, and many registration inputs. |
| 4D DWI image | `(X, Y, Z, N)` | `N` must match bvals/bvecs before reconstruction, b0 extraction, shell extraction, or denoising that depends on gradients. |
| Affine | `(4, 4)` | Preserve from `load_nifti`; pass to `save_nifti` for derivatives in the same spatial frame. |
| Header | nibabel NIfTI header | Pass `hdr=img.header` for direct derivatives that should keep voxel sizes and metadata. |
| Voxel size/axis codes | Returned by `load_nifti(..., return_voxsize=True, return_coords=True)` | Useful when orientation or spacing is unclear; never infer orientation from array shape alone. |

Safe save rules:

- Save to a new path or temporary directory unless the user explicitly wants to overwrite.
- Preserve affine and often header for derivatives created in the same space.
- Set `dtype` or cast before saving `int64`/`uint64` arrays.
- Validate output dimensionality before writing, especially after volume extraction, splitting, or broadcasting.

## bvals And bvecs

`read_bvals_bvecs` accepts text and NumPy sidecars and returns arrays suitable for `gradient_table`.

| Data | Accepted forms | Output |
| --- | --- | --- |
| b-values | `.bval`, `.bvals`, `.txt`, `.npy`, or empty suffix; a single vector/row of `N` values. | `bvals` shaped `(N,)`. |
| b-vectors | `.bvec`, `.bvecs`, `.txt`, `.eddy_rotated_bvecs`, `.npy`, or empty suffix; `(3, N)` or `(N, 3)`. | `bvecs` shaped `(N, 3)`. |
| Combined b-table | Array/path shaped `(N, 4)` or `(4, N)` passed as `gradient_table(bvals, bvecs=None)`. | First value per row/column is b-value, remaining three are b-vector components. |

Common parser errors and meanings:

- `File type ... is not recognized`: unsupported extension; convert to text/NumPy or use a supported suffix.
- `bvec file should have three rows`: neither dimension has length `3`.
- `bval file should have one row`: bvals are not a single vector.
- `b-values and b-vectors shapes do not correspond`: number of measurements differs.
- Unit-vector failures in `gradient_table`: normalize or fix non-b0 b-vectors; do not normalize b0 rows to arbitrary directions.

## GradientTable Objects

A `GradientTable` carries immutable acquisition metadata for models and tracking.

| Attribute | Meaning |
| --- | --- |
| `gtab.bvals` | Length-`N` b-values. |
| `gtab.bvecs` | `(N, 3)` direction vectors; non-b0 rows should be unit length. |
| `gtab.b0s_mask` | Boolean mask where `bvals <= b0_threshold`. |
| `gtab.gradients` | Combined gradient representation. |
| `gtab.btens` | Optional b-tensor encodings. |
| `gtab.big_delta`, `gtab.small_delta` | Optional acquisition timing. |

Before modeling, check `len(gtab.bvals) == data.shape[-1]`, the b0 count is plausible, and the selected `b0_threshold` matches the scanner/protocol convention.

## Tractogram Formats

Dipy high-level streamline IO supports `.trk`, `.tck`, `.trx`, `.vtk`, `.vtp`, `.fib`, and `.dpy`.

| Format | Reference behavior | Notes |
| --- | --- | --- |
| `.trk` | `reference="same"` can use the TRK header; external references are checked by default. | Preserves data-per-point and data-per-streamline through Dipy IO. |
| `.trx` | `reference="same"` can use the TRX file; metadata is handled through `trx-python`. | Useful for rich tractogram data and concatenation. |
| `.tck` | Requires an external reference for spatial attributes when loading. | Does not carry all TRK-like reference metadata. |
| `.vtk`, `.vtp`, `.fib` | Require an external reference and may involve legacy LPS assumptions. | Use explicit `from_space=Space.LPSMM` for older files when evidence indicates LPSMM coordinates. |
| `.dpy` | Requires an external reference. | Dipy-specific streamlines container. |

Spatial state terms:

- `Space.RASMM`: world coordinates in RAS millimeters; Dipy's default load/save target.
- `Space.VOXMM`: voxel-scaled millimeter space.
- `Space.VOX`: voxel index space for grid operations.
- `Origin.NIFTI`: voxel-center origin; Dipy's default.
- `Origin.TRACKVIS`: voxel-corner origin for TrackVis-style conventions.

Bounding-box validation verifies streamline coordinates against the reference in voxel space. Keep `bbox_valid_check=True` for normal loads/saves. For repair work, load with checks disabled, inspect `sft.is_bbox_in_vox_valid()`, remove invalid streamlines, then save with checks enabled.

## PAM5 Peak Files

PAM5 files are HDF5 files with suffix `.pam5` and a `pam/` group storing `PeaksAndMetrics` fields.

| Field | Shape pattern | Required |
| --- | --- | --- |
| `peak_dirs` | `(X, Y, Z, P, 3)` | Yes |
| `peak_values` | `(X, Y, Z, P)` | Yes |
| `peak_indices` | `(X, Y, Z, P)` | Yes |
| `affine` | `(4, 4)` | Strongly recommended |
| `sphere_vertices` | `(M, 3)` | Needed to interpret sphere-indexed directions. |
| `shm_coeff`, `B`, `gfa`, `qa`, `odf` | Model-dependent | Optional |

Use `../../reconstruction-models/` to generate peaks, then use this sub-skill to save, inspect, convert, or move PAM data. When converting PAM to NIfTI or back, ensure all peak arrays share spatial shape and affine.

## Dataset Cache Behavior

Dipy's dataset utilities use a user-writable data home by default and `dipy_fetch` can write to an explicit output directory. Listing dataset names is safe; fetching can use network, create directories, validate MD5 checksums, and retry through mirrors. In automated workflows, separate discovery from download and obtain user intent before cache mutation.

## IO CLI File Families

| Command | Primary inputs/outputs |
| --- | --- |
| `dipy_info` | NIfTI, bval/bvec, tractogram, and PAM5 inspection. |
| `dipy_split`, `dipy_extract_b0`, `dipy_extract_shell`, `dipy_extract_volume` | NIfTI volume subsets plus shell-specific sidecars. |
| `dipy_math` | NIfTI arrays with compatible shapes or intended broadcasting. |
| `dipy_convert_tractogram`, `dipy_concatenate_tractograms` | Streamline formats and reference images/headers. |
| `dipy_convert_tensors` | Tensor NIfTI convention changes among supported tool conventions. |
| `dipy_convert_sh`, `dipy_sh_convert_mrtrix` | Spherical-harmonic convention conversion. |
| `dipy_nifti2pam`, `dipy_pam2nifti`, `dipy_tensor2pam` | PAM5, peak NIfTIs, tensor eigen files, sphere files, and related metrics. |
