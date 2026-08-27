# Star representations, grids, and backend semantics

## Three representations

A label image uses background `0` and positive instance IDs. A star-distance
field stores one positive distance per ray at sampled foreground positions. A
rendered image rasterizes a sparse list of centers and distances back to a
requested spatial shape. Keep these separate: a probability map is not an
instance label image, and a dense distance tensor is not a sparse candidate
list.

## 2D alignment

`star_dist(labels,n_rays,grid=(gy,gx),mode='cpp')` samples `labels[::gy,::gx]`
and returns `(ceil(Y/gy),ceil(X/gx),R)`. Dense NMS receives that sampled tensor
and the equally sampled probability map; pass the same `grid` so its returned
points are full-image `(row,column)` coordinates. Do not multiply dense-NMS
points by grid again before `polygons_to_label`. Sparse NMS points are already
full-image coordinates and must likewise not be rescaled.

`dist_to_coord` takes sparse `(N,R)` distances and `(N,2)` centers. Its angular
convention uses row offset `distance*sin(phi)` and column offset
`distance*cos(phi)` for evenly spaced `phi` from zero through `2*pi` (endpoint
excluded). `scale_dist` changes coordinate units; use it consistently with
physical-pixel spacing. The legacy `_dist_to_coord_old` dense helper has a
different input layout and is only for compatibility/reproduction.

## 3D rays and anisotropy

A `Rays_*` object exposes `vertices` `(R,3)` in `(z,y,x)` and triangular
`faces` `(F,3)`. `Rays_GoldenSpiral(n,anisotropy=...)` needs `n >= 4`; other
factories include Cartesian, tetrahedral, octahedral, and explicit rays.
Anisotropy affects ray construction and must match the model/data configuration,
NMS, and rendering. `rays.copy(scale=(sz,sy,sx))` intentionally changes the
coordinate scale. `rays.volume(dist)` and `rays.surface(dist)` accept leading
batch/grid axes with last axis `R`.

`star_dist3D(labels,rays,grid,mode)`, 3D NMS, and `polyhedron_to_label` must use
the same ray vertices/faces. The grid affects only `(Z,Y,X)` sampling axes; it
never changes ray order. `dist_to_coord3D` returns `(N,R,3)` and keeps
`(z,y,x)` order. Reorder to `(x,y,z)` only at an explicitly documented export
boundary.

## Rendering and overlap

For 2D, `polygons_to_label` uses `prob > thr`, stable increasing-probability
rasterization, and consecutive output IDs. For 3D, `polyhedron_to_label` uses
`prob >= thr`, decreasing-probability ordering, native render modes
`full/kernel/hull/bbox/debug`, and direct explicit labels. Non-empty 3D native
output is `int32` while the empty fast path is `uint16`; this observed quirk is
why a caller should normalize dtype deliberately. A supplied `overlap_label`
marks multiply covered pixels/voxels.

Star conversion assumes an object is star-convex with respect to the selected
center. Concave objects, disconnected components with one ID, touching objects,
and boundary-clipped objects may not reconstruct exactly. Quantify the result
with matching rather than assuming equal area or exact pixel equality.

## CPU versus OpenCL

The required backend is Python plus the compiled C++ StarDist extensions. Do
not copy native source or private checkout paths into runtime skills. The Python
fallback is useful for a bounded diagnostic but 2D Python mode rejects non-unit
grid and the 3D fallback has a floor-division edge shape difference. OpenCL
requires separately installed `gputools`, package kernels, and a compatible
OpenCL device; CUDA/TensorFlow GPU visibility does not establish that. The
OpenCL parity tests in `tests/test_stardist2D.py` and `tests/test_stardist3D.py`
are optional and should be explicitly skipped when not prepared.
