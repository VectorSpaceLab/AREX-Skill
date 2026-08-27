# Dipy IO Troubleshooting

Use this guide when IO, shape, metadata, reference, or conversion failures block downstream Dipy workflows.

## DWI Shape Does Not Match bvals/bvecs

Symptoms:

- `data.shape[-1]` differs from `len(bvals)` or `bvecs.shape[0]`.
- `read_bvals_bvecs` raises `b-values and b-vectors shapes do not correspond`.
- Reconstruction raises later with unclear shape errors.

Diagnosis:

1. Load with `load_nifti(..., return_img=True)` and print `data.shape`.
2. Parse sidecars with `read_bvals_bvecs`; do not use raw text shape as final truth because Dipy transposes `(3, N)` bvecs.
3. Confirm the image is a 4D DWI, not a 3D scalar map or already-extracted shell.
4. Check whether preprocessing removed volumes without updating sidecars.
5. Build `gradient_table` only after the counts match and b-vector norms are valid.

Safe recovery:

- Re-associate the correct sidecars when possible.
- If volumes were intentionally removed, write new sidecars from an explicit keep-index list.
- Never silently trim the last gradient row or duplicate a row just to make counts match.

## bvec Parsing Or Unit-Vector Failure

Symptoms:

- `bvec file should have three rows`.
- `bval file should have one row`.
- `gradient_table` rejects non-unit b-vectors.

Diagnosis and fixes:

- Ensure the file suffix is supported or convert to `.bvec`, `.txt`, or `.npy`.
- Ensure bvals are a single vector of length `N`.
- Ensure bvecs are `(3, N)` or `(N, 3)`; Dipy will transpose when needed.
- Normalize only diffusion-weighted b-vectors, not b0 rows.
- Use the same `atol` in validation and `gradient_table` construction.

## NIfTI Save Fails Or Produces Bad Metadata

Symptoms:

- `save_nifti` rejects `int64` or `uint64` data.
- Output has unexpected voxel size, orientation, or dtype.
- Downstream tools misinterpret a derivative image.

Diagnosis and fixes:

- Cast labels/masks/scalars to explicit compatible dtypes such as `uint8`, `int16`, or `float32`.
- Pass the original affine and, for direct derivatives, the original NIfTI header.
- Use `load_nifti(..., return_voxsize=True, return_coords=True)` to inspect spacing and axis codes.
- Do not reuse a header if the output dimensionality or meaning changed in a way that makes metadata misleading.

## Tractogram Reference Or Header Failure

Symptoms:

- `load_tractogram` returns `False`.
- Header compatibility check fails for `.trk`.
- `reference="same"` fails for `.tck`, `.vtk`, `.vtp`, `.fib`, or `.dpy`.

Diagnosis and fixes:

- Use `reference="same"` only for `.trk` or `.trx` files with usable embedded reference information.
- For `.tck` and legacy formats, provide the native diffusion NIfTI or an equivalent reference header.
- If a TRK file is intentionally being converted to a new reference, verify spatial compatibility before disabling `trk_header_check`.
- Confirm the output extension is one of `.trx`, `.trk`, `.tck`, `.vtk`, `.vtp`, `.fib`, or `.dpy`.

## Bounding Box Validation Failure

Symptoms:

- Error says bounding box is not valid in voxel space.
- Negative voxel coordinates or coordinates beyond image dimensions appear after conversion.

Diagnosis and fixes:

1. Confirm the reference image/header matches the tractogram's native space.
2. Check the declared `Space` and `Origin`; wrong declarations can make valid streamlines appear outside bounds.
3. For known dirty data, load with `bbox_valid_check=False`, inspect `sft.is_bbox_in_vox_valid()`, then run `sft.remove_invalid_streamlines()`.
4. Save final outputs with bbox validation enabled.

Do not disable bbox validation for final deliverables unless the user explicitly needs a nonstandard file and understands the risk.

## Space And Origin Confusion

Symptoms:

- Streamlines appear shifted by half a voxel.
- Converted files look mirrored or offset in external viewers.
- Density maps or ROI operations produce empty results.

Diagnosis and fixes:

- Use `Space.VOX` plus corner origin for grid-index style operations only when that is the intended convention.
- Use `Space.RASMM` and `Origin.NIFTI` for Dipy's default interoperable save/load path.
- For older VTK/FIB workflows, consider explicit `from_space=Space.LPSMM` when source evidence indicates LPS coordinates.
- Recreate an SFT with `StatefulTractogram.from_sft(...)` after filtering rather than manually copying streamlines without state.

## PAM5 Save Or Conversion Failure

Symptoms:

- `save_pam` raises that required fields are missing.
- `.pam5` load rejects suffix or version.
- PAM-to-NIfTI output misses expected optional files.

Diagnosis and fixes:

- Ensure `peak_dirs`, `peak_values`, and `peak_indices` exist and are NumPy arrays.
- Ensure the filename suffix is `.pam5`.
- Set or pass an affine when writing a PAM object intended for spatial use.
- Optional fields such as `shm_coeff`, `B`, `gfa`, `qa`, and `odf` are saved/exported only when present.
- Route peak generation errors to `../../reconstruction-models/`; this sub-skill handles persistence and conversion.

## Dataset Fetch Failure

Symptoms:

- Unknown dataset name.
- Network timeout, HTTP error, permission error, or checksum mismatch.
- Data appears in an unexpected cache directory.

Diagnosis and fixes:

- Run `dipy_fetch list` or `FetchFlow.get_fetcher_datanames()` to verify the installed dataset name.
- Use an explicit `--out_dir` when location matters.
- Treat checksum mismatch as a corrupted or changed upstream file; retry cleanly or ask before accepting altered data.
- Check write permissions for the target directory or cache.
- Do not fetch during a no-network or read-only task; use synthetic arrays or already-provided files instead.

## IO CLI Conversion Produces Unexpected Outputs

Symptoms:

- Output names differ from expectations.
- Shell extraction writes sidecars that do not match selected volumes.
- Tensor or SH conversion output is numerically unexpected.

Diagnosis and fixes:

- Inspect the command help and flow-specific defaults before running a broad conversion.
- For shell extraction, validate selected b-values and output sidecars immediately after writing.
- For tensor/SH conversion, record source and target conventions and route scientific interpretation to `../../reconstruction-models/`.
- For CLI dispatch, entry-point inventory, and parser details, use `../../cli-workflows/`.
