# ImageJ ROI and 3D OBJ contracts

## ImageJ/Fiji ROI ZIP (2D)

`stardist.utils.export_imagej_rois` consumes polygon coordinates from a 2D
prediction, not its label image:

```python
from stardist import export_imagej_rois
labels, polys = model.predict_instances(image, axes="YX")
export_imagej_rois("results/sample_rois.zip", polys["coord"])
```

`polys['coord']` is a polygon array per object in StarDist row/Y, column/X
coordinate order. The helper also accepts an iterable of polygon arrays for
multiple positions/frames. With `set_position=True` (default), ZIP members get
1-based position metadata. `subpixel=True` preserves floating vertices; false
rounds to pixel coordinates. The helper appends `.zip` when passed a stem and
writes one ImageJ `.roi` member per polygon. The implementation applies the
ImageJ half-pixel coordinate convention; use ImageJ/Fiji ROI Manager to consume
it, not a generic polygon reader.

Check the archive explicitly:

```python
from zipfile import ZipFile
with ZipFile("results/sample_rois.zip") as z:
    members = [n for n in z.namelist() if n.endswith(".roi")]
assert members  # zero members means an empty prediction
```

The output is detections, not a label mask. Save `labels` separately as an
integer TIFF when a training/evaluation mask is required. This helper is 2D;
do not pass 3D polyhedra. Native evidence is
`tests/test_model2D.py::test_imagej_rois_export`, which checks creation with a
local model. A stronger check inspects member count and rejects overwrite.

## OBJ mesh (3D)

`stardist.geometry.geom3d.export_to_obj_file3D` consumes the complete polygon
dictionary returned by `StarDist3D.predict_instances`:

```text
dist           (N, R) distances
points         (N, 3) centers in Z,Y,X
rays_vertices  (R, 3) directions in Z,Y,X
rays_faces     (F, 3) triangular face indices
```

```python
from stardist.geometry import export_to_obj_file3D
labels, polys = model.predict_instances(volume, axes="ZYX")
export_to_obj_file3D(
    polys, "results/objects.obj", scale=(voxel_z, voxel_y, voxel_x),
    single_mesh=True, uv_map=False, name="cell",
)
```

`scale` is applied in Z/Y/X before vertices are written in OBJ X/Y/Z order.
Use `(1,1,1)` for voxel coordinates. For physical meshes use `(z,y,x)`
spacing and keep it in a sidecar because OBJ has no reliable microscope
calibration field. `single_mesh=False` creates an object per polyhedron;
`uv_map=True` writes texture coordinates but no MTL/texture file. The output
is plain text with `o`, `v`, and triangular 1-based `f` records and does not
carry labels, probabilities, class IDs, or overlap metadata.

```python
from pathlib import Path
text = Path("results/objects.obj").read_text(encoding="utf-8")
assert any(line.startswith("v ") for line in text.splitlines())
assert any(line.startswith("f ") for line in text.splitlines())
```

Missing keys, inconsistent shapes, non-positive distances, or invalid faces
are API errors. A no-instance result may produce no usable mesh and must be
reported as empty, not as successful geometry. The native candidate is
`tests/test_model3D.py::test_mesh_export`; model prediction still needs the
compiled CPU extension even though writing OBJ is text generation.

## Handoff types

| Artifact | Required contract |
|---|---|
| Label TIFF | Integer dtype; spatial shape equals input without `C`; background 0. |
| ROI ZIP | `.roi` member per polygon, optional 1-based position; empty archive means no detections. |
| OBJ | `v`/`f` text, documented Z/Y/X-to-X/Y/Z transform and scale; no automatic calibration. |
