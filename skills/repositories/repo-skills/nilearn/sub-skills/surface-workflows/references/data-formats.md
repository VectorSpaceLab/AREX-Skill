# Surface Data Formats

Nilearn surface workflows combine geometry and vertex data. Most mistakes come
from mixing hemisphere keys, vertex counts, or array orientation.

## Mesh Geometry

A single-hemisphere mesh is a face-vertex mesh:

- `coordinates`: NumPy array shaped `(n_vertices, 3)` with x, y, z coordinates.
- `faces`: integer NumPy array shaped `(n_faces, 3)` where each row indexes
  three rows of `coordinates`.
- Face indices must be valid vertex indices. If a face references a missing
  vertex, `InMemoryMesh` validation fails.

Use `InMemoryMesh(coordinates, faces)` for synthetic or already-loaded arrays.
Use `FileMesh(file_path)` or `load_surf_mesh(file_path)` for supported surface
mesh files.

## Hemisphere Containers

`PolyMesh` and `PolyData` are shallow containers with `parts` dictionaries.
Valid keys are only:

- `left`
- `right`

At least one key must be present. Left-only workflows are valid, right-only
workflows are valid, and both-hemisphere workflows are valid. `SurfaceImage`
requires mesh keys and data keys to match exactly.

## Surface Data Arrays

Per-hemisphere data is vertex-major:

| Shape | Meaning | Typical use |
| --- | --- | --- |
| `(n_vertices,)` | One scalar value per vertex. | Statistical map, labels, curvature-like values, boolean mask. |
| `(n_vertices, n_samples)` | One time series or feature vector per vertex. | Surface fMRI time series and `SurfaceMasker` input. |
| `(n_vertices, n_regions)` | One label/map column per region. | `SurfaceMapsMasker` maps; some atlas-like data. |

For both hemispheres, the non-vertex dimensions must be compatible. For example,
left `(10242, 120)` and right `(10242, 120)` are compatible time series;
left `(10242, 120)` and right `(10242, 119)` are not.

## `SurfaceImage` Constraints

A valid `SurfaceImage(mesh, data)` satisfies all of these:

1. `mesh` is a `PolyMesh` or a dict accepted by `PolyMesh(**mesh)`.
2. `data` is a `PolyData` or a dict accepted by `PolyData(**data)`.
3. The set of mesh hemisphere keys equals the set of data hemisphere keys.
4. For every part, `data.parts[part].shape[0] == mesh.parts[part].n_vertices`.
5. If both hemispheres are present with 2D arrays, the second dimension matches
   across parts.
6. If both hemispheres are present, dtypes match unless a common `dtype` is
   supplied to cast them.

Do not swap data parts between hemispheres to "make shape errors disappear";
that produces biologically wrong vertex-to-mesh alignment even if counts happen
to match.

## File Inputs

`load_surf_mesh` accepts:

- GIFTI mesh files: `.gii`, `.gii.gz`.
- FreeSurfer mesh files such as `.orig`, `.pial`, `.sphere`, `.white`, and
  `.inflated`.
- Two-array mesh-like inputs: `(coordinates, faces)` or objects exposing
  `.coordinates` and `.faces`.

`load_surf_data` accepts:

- NumPy arrays.
- GIFTI data files: `.gii`, `.gii.gz`.
- Volume-like files containing surface-shaped data: `.mgz`, `.nii`, `.nii.gz`.
- FreeSurfer data files such as `.thickness`, `.curv`, `.sulc`, `.annot`, and
  `.label`.
- Lists or glob patterns of compatible data files, concatenated along the
  sample/column axis.

Saving through `PolyMesh.to_filename()` or `PolyData.to_filename()` writes GIFTI
files. If no hemisphere marker is present, Nilearn appends separate `_hemi-L`
and `_hemi-R` files for both parts.

## Projection Output Contracts

`vol_to_surf` returns a NumPy array for one mesh:

- 3D volume input -> `(n_vertices,)`.
- 4D volume input -> `(n_vertices, n_scans)`.

`SurfaceImage.from_volume` projects each hemisphere in a `PolyMesh` and returns
one `SurfaceImage`; its left/right data arrays keep the vertex-major convention.

For anatomically meaningful projection, the volume and mesh must be in the same
space. Standard fsaverage projection can be appropriate for normalized MNI-like
volumes, but subject-specific meshes need volumes coregistered to the anatomy
that generated those meshes.

## Masker Data Contracts

- `SurfaceMasker` expects input data to be 1D or 2D per hemisphere after
  surface image construction. It can compute a finite, nonzero mask from input
  data when `mask_img` is not provided.
- `SurfaceLabelsMasker` expects `labels_img` to contain label values at
  vertices, usually 1D per hemisphere. `background_label` defaults to `0`.
- `SurfaceMapsMasker` expects `maps_img` to be 2D per hemisphere with
  `(n_vertices, n_regions)` columns. It can reject overlaps when
  `allow_overlap=False`.
- Boolean mask images are `SurfaceImage` objects with one boolean-like value per
  vertex and the same mesh as the image or maps being masked.
