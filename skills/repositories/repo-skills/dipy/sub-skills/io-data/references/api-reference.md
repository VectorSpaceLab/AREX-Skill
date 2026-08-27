# Dipy IO API Reference

This reference covers the API surface owned by `io-data`. Use it to load inputs, validate metadata, and prepare objects before routing to reconstruction, tracking, segmentation, or registration.

## Image IO

| API | Installed signature | Use | Key gotchas |
| --- | --- | --- | --- |
| `dipy.io.image.load_nifti` | `load_nifti(fname, *, return_img=False, return_voxsize=False, return_coords=False, as_ndarray=True)` | Load NIfTI data and affine, optionally returning the nibabel image, voxel sizes, and axis codes. | With `as_ndarray=False`, data remains a nibabel proxy. Request `return_img=True` when a derivative should reuse the source header. |
| `dipy.io.image.load_nifti_data` | `load_nifti_data(fname, *, as_ndarray=True)` | Load only the NIfTI data array/proxy. | Use only when affine/header are irrelevant; most diffusion workflows need the affine. |
| `dipy.io.image.save_nifti` | `save_nifti(fname, data, affine, *, hdr=None, dtype=None)` | Save an array with a 4x4 affine and optional header/dtype. | Nibabel 4+ rejects default saves of `int64`/`uint64` arrays unless a safe `dtype`, header, or cast is supplied. |

Typical pattern:

```python
from dipy.io.image import load_nifti, save_nifti

data, affine, img = load_nifti("dwi.nii.gz", return_img=True)
save_nifti("derived.nii.gz", derived, affine, hdr=img.header, dtype=derived.dtype)
```

## Gradient IO

| API | Installed signature | Use | Key gotchas |
| --- | --- | --- | --- |
| `dipy.io.gradients.read_bvals_bvecs` | `read_bvals_bvecs(fbvals, fbvecs)` | Read b-values and b-vectors from disk. | Expects path strings/`Path` objects, not arrays. Either argument may be `None` or empty when reading only one sidecar. |
| `dipy.core.gradients.gradient_table` | `gradient_table(bvals, *, bvecs=None, big_delta=None, small_delta=None, b0_threshold=50, atol=0.01, btens=None)` | Build a `GradientTable` from bvals/bvecs, paths, or a combined b-table. | B-vectors are transposed from `(3, N)` when needed; non-b0 b-vectors must be unit length within `atol`. |
| `dipy.core.gradients.GradientTable` | `GradientTable(gradients, *, big_delta=None, small_delta=None, b0_threshold=50, btens=None)` | Lower-level immutable gradient metadata class. | Prefer `gradient_table` for normal file/array inputs. |

Validation checklist:

- For DWI modeling, require `data.ndim == 4` and `data.shape[-1] == len(bvals) == bvecs.shape[0]`.
- Confirm `bvecs.shape == (N, 3)` after reading or constructing the table.
- Check `np.linalg.norm(gtab.bvecs[~gtab.b0s_mask], axis=1)` is close to `1` at the chosen `atol`.
- Record non-default `b0_threshold`, `big_delta`, `small_delta`, or `btens` because they change downstream interpretation.
- `btens` may be one tensor type label (`LTE`, `PTE`, `STE`, `CTE`), per-volume labels, or an `(N, 3, 3)` array.

## Tractogram And StatefulTractogram IO

| API | Installed signature | Use | Key gotchas |
| --- | --- | --- | --- |
| `dipy.io.stateful_tractogram.StatefulTractogram` | `StatefulTractogram(streamlines, reference, space, *, origin=NIFTI, data_per_point=None, data_per_streamline=None)` | Wrap streamlines with spatial reference, current space/origin, and optional metadata. | `space` must be a `Space` enum; `origin` must be an `Origin` enum. The reference supplies affine, dimensions, voxel sizes, and voxel order. |
| `dipy.io.streamline.load_tractogram` | `load_tractogram(filename, reference, *, to_space=RASMM, to_origin=NIFTI, bbox_valid_check=True, from_space=None, from_origin=None, trk_header_check=True)` | Load `.trx`, `.trk`, `.tck`, `.vtk`, `.vtp`, `.fib`, or `.dpy` into an SFT. | `reference="same"` works for `.trk` and `.trx`; other formats need an external image/header/reference. Header compatibility is checked for `.trk` by default. |
| `dipy.io.streamline.save_tractogram` | `save_tractogram(sft, filename, *, bbox_valid_check=True, to_space=RASMM, to_origin=NIFTI)` | Save an SFT to `.trx`, `.trk`, `.tck`, `.vtk`, `.vtp`, `.fib`, or `.dpy`. | Unsupported extensions raise. With bbox checks enabled, invalid coordinates fail before save. `.trk`, `.tck`, and `.trx` save in RASMM/NIfTI defaults. |

Accepted references include NIfTI filenames, TRK filenames/headers, nibabel NIfTI images, nibabel TRK files, NIfTI headers, TRK header dicts, `(affine, dimensions, voxel_sizes, voxel_order)` tuples, and another `StatefulTractogram` for spatial attributes.

Important state operations:

- `sft.to_rasmm()`, `sft.to_voxmm()`, `sft.to_vox()` convert coordinate space.
- `sft.to_center()` and `sft.to_corner()` convert origin convention.
- `sft.is_bbox_in_vox_valid()` checks whether streamlines are within reference voxel bounds.
- `sft.remove_invalid_streamlines()` removes invalid streamlines after deliberate loose loading.
- `StatefulTractogram.from_sft(...)` creates a new SFT that inherits state from an existing SFT after filtering or replacement.
- `StatefulTractogram.are_compatible(a, b)` checks header, space, origin, and data-key compatibility before merging.

## PAM5 And Peaks IO

| API/workflow | Use | Required or important fields |
| --- | --- | --- |
| `dipy.io.peaks.load_pam(fname, *, verbose=False)` | Load a `.pam5` HDF5 file into `PeaksAndMetrics`. | File suffix must be `.pam5`; version must match Dipy's PAM5 version. |
| `dipy.io.peaks.save_pam(fname, pam, *, affine=None, verbose=False)` | Save a `PeaksAndMetrics` object as `.pam5`. | Requires ndarray `peak_dirs`, `peak_values`, and `peak_indices`; stores optional `affine`, SH, sphere, B, GFA, QA, and ODF fields when present. |
| `dipy.io.peaks.pam_to_niftis(...)` | Save peak directions, values, indices, SH/GFA/B/QA, and sphere outputs from a PAM object. | Optional fields are skipped when absent. `reshape_dirs=True` reshapes peak directions for visualization-style outputs. |
| `dipy.io.peaks.niftis_to_pam(...)` | Build a PAM object from NIfTI-like arrays and optional sphere/metric fields. | Peak direction/value/index shapes must agree spatially and share the same affine. |
| `dipy.io.peaks.tensor_to_pam(...)` | Convert tensor eigenvectors/eigenvalues into PAM-like peak fields. | Reconstruction ownership belongs to `../../reconstruction-models/`; IO ownership begins at conversion/persistence. |

The correct peaks import for generating peaks is `dipy.direction.peaks.peaks_from_model`, not `dipy.reconst.peaks`.

## Dataset Fetch And Listing

| API/command | Use | Operational caveat |
| --- | --- | --- |
| `dipy.workflows.io.FetchFlow.get_fetcher_datanames()` | Programmatically list available dataset fetcher names. | Safe discovery; no download. |
| `dipy_fetch list` | CLI dataset discovery. | Safe discovery; no download. |
| `dipy_fetch <dataset> --out_dir <dir>` | Download/cache one or more datasets. | Networked and writes files; use only with user intent. |
| `dipy.data.fetch_*` functions | Programmatic dataset downloads and cache population. | Default cache is the DIPY data home unless an explicit output option exists. |

Fetchers validate checksums, may retry downloads, and may fall back to mirrors for supported hosts. Treat checksum mismatch as a data integrity problem, not a modeling failure.

## IO Workflow Classes And Commands

| Command | Workflow class | Owned behavior |
| --- | --- | --- |
| `dipy_info` | `IoInfoFlow` | Inspect image, gradient, tractogram, and PAM files. |
| `dipy_fetch` | `FetchFlow` | List or fetch bundled datasets. |
| `dipy_split` | `SplitFlow` | Split image volumes. |
| `dipy_extract_b0` | `ExtractB0Flow` | Extract b0 volumes using bvals/bvecs and threshold rules. |
| `dipy_extract_shell` | `ExtractShellFlow` | Extract one or more diffusion shells and matching gradient sidecars. |
| `dipy_extract_volume` | `ExtractVolumeFlow` | Extract specific volume indices. |
| `dipy_math` | `MathFlow` | Perform image-array math with output writes. |
| `dipy_concatenate_tractograms` | `ConcatenateTractogramFlow` | Merge compatible tractograms. |
| `dipy_convert_tractogram` | `ConvertTractogramFlow` | Convert streamline formats with reference/space/origin options. |
| `dipy_convert_tensors` | `ConvertTensorsFlow` | Convert tensor image conventions. |
| `dipy_convert_sh` | `ConvertSHFlow` | Convert SH basis/order conventions. |
| `dipy_sh_convert_mrtrix` | `ConvertSHFlow` | Compatibility entry point; prefer `dipy_convert_sh` for new work. |
| `dipy_nifti2pam` | `NiftisToPamFlow` | Convert NIfTI peak fields into PAM5. |
| `dipy_pam2nifti` | `PamToNiftisFlow` | Export PAM5 peak fields as NIfTI/text outputs. |
| `dipy_tensor2pam` | `TensorToPamFlow` | Convert tensor eigen data to PAM5-like peak representation. |
