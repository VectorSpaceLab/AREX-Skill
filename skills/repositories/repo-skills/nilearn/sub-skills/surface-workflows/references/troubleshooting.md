# Surface Troubleshooting

Use this matrix to diagnose common Nilearn surface workflow failures before
routing to plotting or broader data-preparation skills.

## Mesh and Data Mismatches

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Data and mesh do not have the same keys` | Mesh has `left` and `right`, but data has only one part or differently named keys. | Use matching `left`/`right` dictionaries for both mesh and data, or intentionally build a one-hemisphere `PolyMesh` and matching data. |
| `Data shape does not match number of vertices` | A data part's first axis does not equal the corresponding mesh vertex count. | Inspect `mesh.parts[hemi].n_vertices` and `data.parts[hemi].shape[0]`; regenerate or select the correct hemisphere data. |
| `Data arrays for keys 'left' and 'right' have incompatible shapes` | Both parts are 2D but the non-vertex dimension differs. | Ensure both hemispheres have the same number of time points, regions, or maps. |
| Dtype mismatch between left and right data | Left and right arrays have different dtypes. | Pass a common `dtype` to `PolyData` or `SurfaceImage`, or cast arrays explicitly. |
| `Cannot create an empty PolyMesh` or `Cannot create an empty PolyData` | Neither hemisphere was provided. | Provide at least `left` or `right`. |

Do not fix mismatch errors by swapping hemispheres unless there is strong
metadata evidence that the inputs were mislabeled. Surface data is vertex-order
specific.

## Projection Problems

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Mostly `nan` values from `vol_to_surf` | Mesh vertices or sample points are outside the volume or mask. | Confirm volume/mesh space alignment; reduce restrictive `mask_img`; inspect affine and mesh coordinates. |
| Error when using `kind="ball"` with `depth` | Ball sampling does not support `depth`. | Remove `depth`, or use `kind="line"`/`kind="depth"` as appropriate. |
| Unexpected label interpolation values | Continuous `linear` interpolation was used on atlas labels. | Use `interpolation="nearest_most_frequent"` for deterministic label images. |
| Slow ball projection | Uncached number of ball samples. | Use `n_samples` in `10`, `20`, `40`, `80`, or `160`; default is safe. |
| Anatomically implausible projection | Volume and surface are in different spaces. | Use a mesh coregistered to the subject anatomy or project normalized MNI-like data to an appropriate fsaverage mesh. |
| Depth sampling fails or looks wrong | `inner_mesh` and outer mesh vertices do not correspond one-to-one. | Use paired pial/white meshes from the same source and resolution; avoid mixing custom and fsaverage meshes. |

## fsaverage and Dataset Cache Concerns

| Scenario | Guidance |
| --- | --- |
| No-network example or smoke test | Use `load_fsaverage(mesh="fsaverage5")` or construct `InMemoryMesh`; `fsaverage5` is shipped with Nilearn. |
| User requests `fsaverage3`, `fsaverage4`, `fsaverage6`, or `fsaverage7` | Explain that these may fetch data into the dataset cache and require network/cache permissions. |
| Cache path questions | Let Nilearn manage `data_dir` unless the user explicitly provides one; do not bake local cache paths into generated content. |
| Vertex-order concerns for older local fsaverage3/4 caches | Reload through current Nilearn helpers so their vertex-order sanitization can run when needed. |

## Surface Masker Failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `Parameter 'imgs' must be provided` in `SurfaceMasker.fit()` | No `mask_img` was supplied and no image was provided for mask computation. | Call `fit(imgs)` or construct `SurfaceMasker(mask_img=mask_img)`. |
| Input image rejected as too many dimensions | Surface image data parts have more than 2 dimensions. | Reshape to `(n_vertices,)` or `(n_vertices, n_samples)` before creating `SurfaceImage`. |
| `SurfaceMapsMasker` asks for `maps_img` | Constructor lacked maps. | Create a 2D per-hemisphere maps `SurfaceImage` and pass it as `maps_img`. |
| `maps_img contains no map` or no map after mask | Maps are all zero, or mask removes every nonzero map vertex. | Inspect nonzero values before and after applying `mask_img`. |
| Overlap error with `allow_overlap=False` | Multiple maps are nonzero at the same vertex. | Allow overlap when scientifically intended, or fix maps to be mutually exclusive. |
| Labels have unexpected region names | `labels`, `lut`, and values in `labels_img` are inconsistent. | Align the lookup table or labels list with actual label values and `background_label`. |

## Plotting and Reports

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Import or runtime errors involving Matplotlib, Plotly, or Kaleido | Optional plotting dependencies are not installed. | Route to `../plotting-reporting/SKILL.md`; install or avoid plotting extras depending on the task. |
| Masker report generation fails in minimal environment | `reports=True` triggers plotting/report dependencies. | Use `reports=False` for tests or nonvisual extraction. |
| Valid `SurfaceImage` but wrong display appearance | View, hemisphere, mesh type, background map, threshold, or engine choice is a plotting decision. | Hand off the validated object and display intent to plotting/reporting guidance. |

## Minimal Debug Printout

Ask future agents to print only portable metadata:

```python
print(img.shape)
print({part: mesh.n_vertices for part, mesh in img.mesh.parts.items()})
print({part: data.shape for part, data in img.data.parts.items()})
```

Avoid printing local dataset cache paths, environment prefixes, or absolute
checkout paths in public-facing reports or generated skill content.
