# Surface Workflows

These recipes focus on preparing valid Nilearn surface objects and arrays. For
plot calls and figure settings, route to `../plotting-reporting/SKILL.md` after
creating the surface image or texture.

## Build a Tiny In-Memory Surface

Use this pattern for no-download tests, examples, or synthetic reproductions.

```python
import numpy as np
from nilearn.surface import InMemoryMesh, PolyMesh, SurfaceImage

left_mesh = InMemoryMesh(
    coordinates=np.asarray(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
    ),
    faces=np.asarray([[0, 1, 2]], dtype=np.int32),
)
right_mesh = InMemoryMesh(
    coordinates=np.asarray(
        [[2.0, 0.0, 0.0], [3.0, 0.0, 0.0], [2.0, 1.0, 0.0]]
    ),
    faces=np.asarray([[0, 1, 2]], dtype=np.int32),
)
mesh = PolyMesh(left=left_mesh, right=right_mesh)
img = SurfaceImage(
    mesh=mesh,
    data={
        "left": np.asarray([1.0, 2.0, 3.0]),
        "right": np.asarray([4.0, 5.0, 6.0]),
    },
)
```

Validate before handing off:

```python
assert img.data.parts["left"].shape[0] == img.mesh.parts["left"].n_vertices
assert img.data.parts["right"].shape[0] == img.mesh.parts["right"].n_vertices
```

## Project a Volume to a Surface

For one hemisphere texture:

```python
from nilearn.surface import vol_to_surf

texture = vol_to_surf(
    img=volume_img,
    surf_mesh=surface_mesh,
    radius=3.0,
    interpolation="linear",
    kind="auto",
)
```

For both hemispheres as a `SurfaceImage`:

```python
from nilearn.datasets import load_fsaverage
from nilearn.surface import SurfaceImage

fsaverage = load_fsaverage(mesh="fsaverage5")
surf_img = SurfaceImage.from_volume(
    mesh=fsaverage["pial"],
    volume_img=volume_img,
    inner_mesh=fsaverage["white_matter"],
    interpolation="linear",
)
```

Projection checklist:

- Confirm the volume and mesh are in the same coordinate space.
- Use `inner_mesh` when corresponding pial/white meshes are available; `auto`
  then uses depth sampling.
- For atlas labels, prefer `interpolation="nearest_most_frequent"`.
- For `kind="ball"`, do not pass `depth`; choose cached `n_samples` values
  `10`, `20`, `40`, `80`, or `160` for speed.
- Expect `numpy.nan` at vertices where all sample points fall outside the image
  or mask.

## Use fsaverage Safely

No-network default:

```python
from nilearn.datasets import load_fsaverage, load_fsaverage_data

fsaverage = load_fsaverage(mesh="fsaverage5")
sulcal = load_fsaverage_data(mesh="fsaverage5", data_type="sulcal")
```

`fsaverage5` is packaged with Nilearn. Higher or lower resolutions such as
`fsaverage3`, `fsaverage4`, `fsaverage6`, or `fsaverage7` may require dataset
fetching and a writable cache, so ask before using them in no-network or
reproducible tasks.

Typical mesh entries returned by `load_fsaverage`:

- `pial`: outer cortical surface.
- `white_matter`: inner white-matter surface.
- `inflated`: useful for visualization and neighborhood computations.
- `sphere`: spherical registration surface.
- `flat`: flattened surface.

## Transform with `SurfaceMasker`

Use `SurfaceMasker` for vertex-wise surface time series or maps.

```python
from nilearn.maskers import SurfaceMasker

masker = SurfaceMasker(standardize=False, reports=False)
signals = masker.fit_transform(surf_img)
roundtrip_img = masker.inverse_transform(signals)
```

Notes:

- `signals` is samples by selected vertices. For a single scalar map, use
  `np.atleast_2d` as needed before downstream estimators.
- A `mask_img` must be a `SurfaceImage` with matching mesh and boolean-like
  data per vertex.
- Keep `reports=False` when optional plotting dependencies are unavailable or
  when a no-plot smoke test is the goal.

## Transform with Surface Labels or Maps

Labels:

```python
from nilearn.maskers import SurfaceLabelsMasker

labels_masker = SurfaceLabelsMasker(
    labels_img=labels_img,
    background_label=0,
    strategy="mean",
    reports=False,
).fit()
region_signals = labels_masker.transform(surf_img)
```

Maps:

```python
from nilearn.maskers import SurfaceMapsMasker

maps_masker = SurfaceMapsMasker(
    maps_img=maps_img,
    allow_overlap=True,
    reports=False,
).fit()
map_signals = maps_masker.transform(surf_img)
```

Surface labels and maps are still `SurfaceImage` objects. The atlas image,
input image, and optional mask must share compatible meshes and matching
hemisphere keys.

## Hand Off to Plotting

After preparing a valid `SurfaceImage`, pass only the validated object and the
intended display goal to plotting/reporting guidance. Include these details in
the handoff:

- Surface object: scalar map, time series summary, labels, or maps.
- Hemisphere intent: `left`, `right`, or `both`.
- Mesh type: pial, inflated, flat, custom, or unknown.
- Background map availability, such as fsaverage sulcal data.
- Whether optional plotting dependencies are available or should be avoided.

For example, this sub-skill prepares `score_img = SurfaceImage(mesh=mesh,
data=scores)`. The plotting/reporting sub-skill chooses whether to use
`plot_surf`, `plot_surf_stat_map`, `view_surf`, thresholds, color maps, or
reports.
