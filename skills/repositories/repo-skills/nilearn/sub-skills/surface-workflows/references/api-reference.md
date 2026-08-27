# Surface API Reference

This reference covers the Nilearn surface APIs most often needed before
plotting or analysis. It assumes a source-checkout or development install of
Nilearn with Python 3.10 or newer.

## Core Object Model

| Object | Signature | Purpose | Key contract |
| --- | --- | --- | --- |
| `InMemoryMesh` | `InMemoryMesh(coordinates, faces)` | Stores one hemisphere mesh as NumPy arrays. | `coordinates` is `(n_vertices, 3)`; `faces` is `(n_faces, 3)` integer vertex indices. |
| `FileMesh` | `FileMesh(file_path)` | Lazily wraps a GIFTI or FreeSurfer surface mesh file. | Loads through `load_surf_mesh`; use `.loaded()` to get `InMemoryMesh`. |
| `PolyMesh` | `PolyMesh(left=None, right=None)` | Groups one or both hemisphere meshes. | At least one hemisphere is required; keys are `left` and/or `right`. |
| `PolyData` | `PolyData(left=None, right=None, dtype=None)` | Groups one or both hemisphere data arrays or files. | At least one hemisphere is required; all present parts must have compatible dimensionality and dtype. |
| `SurfaceImage` | `SurfaceImage(mesh, data, dtype=None)` | Couples a `PolyMesh` with matching `PolyData`. | Mesh and data keys must match, and every data part's first axis must equal that hemisphere's vertex count. |

`SurfaceImage.shape` is delegated to `PolyData.shape`. With both hemispheres,
the first dimension is the sum of left and right vertices. For 2D data, the
second dimension is the common number of samples, time points, labels, or maps.

## Loading Helpers

| Function | Signature | Accepts | Returns |
| --- | --- | --- | --- |
| `load_surf_mesh` | `load_surf_mesh(surf_mesh)` | `.gii`, `.gii.gz`, FreeSurfer mesh files such as `.orig`, `.pial`, `.sphere`, `.white`, `.inflated`; `(coordinates, faces)` arrays; mesh-like objects with `coordinates` and `faces`. | `InMemoryMesh`. |
| `load_surf_data` | `load_surf_data(surf_data)` | NumPy arrays; `.gii`, `.gii.gz`, `.mgz`, `.nii`, `.nii.gz`; FreeSurfer data files such as `.thickness`, `.curv`, `.sulc`, `.annot`, `.label`; lists/globs of compatible files. | Squeezed NumPy array. |

When passing multiple data files, their vertex axis must match so they can be
concatenated into a 2D array. Object-dtype data is not a useful surface dtype;
Nilearn casts it to numeric dtype with a warning in surface containers.

## Volume Projection

```python
vol_to_surf(
    img,
    surf_mesh,
    radius=3.0,
    interpolation="linear",
    kind="auto",
    n_samples=None,
    mask_img=None,
    inner_mesh=None,
    depth=None,
)
```

`vol_to_surf` samples a 3D or 4D Niimg-like volume around each surface vertex.
For a 3D image it returns `(n_vertices,)`; for a 4D image it returns
`(n_vertices, n_scans)`.

Sampling strategy:

- `kind="auto"` chooses `depth` if `inner_mesh` is provided, otherwise `line`.
- `kind="depth"` samples between corresponding outer and inner mesh vertices;
  use when pial and white surfaces are available and aligned.
- `kind="line"` samples along vertex normals over a segment controlled by
  `radius` or explicit `depth` fractions.
- `kind="ball"` samples a ball around each vertex. Do not pass `depth` with
  `kind="ball"`; prefer cached `n_samples` values `10`, `20`, `40`, `80`, or
  `160` for performance.
- `interpolation="linear"` is the default for continuous data.
- `interpolation="nearest_most_frequent"` is useful for deterministic atlas or
  label images.

`SurfaceImage.from_volume(mesh, volume_img, inner_mesh=None,
**vol_to_surf_kwargs)` projects a volume for each hemisphere in a `PolyMesh` and
returns a `SurfaceImage`.

## fsaverage Helpers

| Helper | Signature | Returns | No-network note |
| --- | --- | --- | --- |
| `fetch_surf_fsaverage` | `fetch_surf_fsaverage(mesh="fsaverage5", data_dir=None)` | Bunch of mesh and data file paths. | `fsaverage5` is shipped with Nilearn; other resolutions may fetch into a dataset cache. |
| `load_fsaverage` | `load_fsaverage(mesh="fsaverage5", data_dir=None)` | Bunch with `PolyMesh` entries: `pial`, `white_matter`, `inflated`, `sphere`, `flat`. | Same fetch behavior as `fetch_surf_fsaverage`. |
| `load_fsaverage_data` | `load_fsaverage_data(mesh="fsaverage5", mesh_type="pial", data_type="sulcal", data_dir=None)` | `SurfaceImage` containing fsaverage data such as sulcal depth. | Uses fsaverage helper and data cache behavior. |

Common fsaverage data keys include `area`, `curv`, `sulc`, and `thick` in raw
fetch results. `load_fsaverage_data` exposes `data_type` values `area`,
`curvature`, `sulcal`, and `thickness`.

## Surface Maskers

| Masker | Typical constructor | Input image contract | Output contract |
| --- | --- | --- | --- |
| `SurfaceMasker` | `SurfaceMasker(mask_img=None, standardize=False, detrend=False, low_pass=None, high_pass=None, t_r=None, reports=True, ...)` | `SurfaceImage` or list of `SurfaceImage`; optional boolean-like surface mask. | `fit_transform` returns samples by selected vertices; `inverse_transform` returns a `SurfaceImage`. |
| `SurfaceLabelsMasker` | `SurfaceLabelsMasker(labels_img, labels=None, lut=None, background_label=0, mask_img=None, strategy="mean", ...)` | Label `SurfaceImage` with integer/float region ids per vertex; optional mask. | Region signals by sample; inverse transform paints region signals back to surface vertices. |
| `SurfaceMapsMasker` | `SurfaceMapsMasker(maps_img, mask_img=None, allow_overlap=True, ...)` | Maps `SurfaceImage` with 2D data `(n_vertices, n_regions)` for each part. | Region/map signals; `allow_overlap=False` rejects overlapping nonzero maps. |

Surface maskers mirror NIfTI masker patterns but operate on `SurfaceImage`
objects. Keep `reports=False` in minimal or no-plot smoke checks if optional
plotting dependencies are not part of the task.
