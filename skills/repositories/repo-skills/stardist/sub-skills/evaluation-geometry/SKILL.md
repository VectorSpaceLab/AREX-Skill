---
name: "evaluation-geometry"
description: "Route StarDist label validation, star-distance representations,
  polygon/polyhedron rendering, NMS, matching metrics, patch sampling, and
  visualization/error overlays."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Evaluation and geometry

Use this sub-skill for standalone label/data work: star distances, polygon or
polyhedron conversion, dense/sparse non-maximum suppression, instance matching,
temporal label grouping, patch centers, threshold concepts, and 2D diagnostic
overlays. Keep neural model construction/training and model prediction in
[2d-workflows](../2d-workflows/SKILL.md) or
[3d-workflows](../3d-workflows/SKILL.md). Keep file CLIs and optional
BioImage.IO, ImageJ/ROI, OBJ, and QuPath integration in
[deployment-integration](../deployment-integration/SKILL.md).

## Route

1. Validate integer, non-negative labels; shape/rank; grid powers of two; and
   3D `Rays_*` alignment before native calls.
2. Read [api-reference.md](references/api-reference.md) for exact signatures,
   shapes, dtypes, tuples, and threshold inclusivity. Use
   [representations.md](references/representations.md) to keep `(Y,X)` versus
   `(Z,Y,X)`, grid, rays, and physical scales aligned.
3. Use CPU `mode="cpp"` and compiled C++ extensions for the required baseline;
   use `mode="python"` only as a bounded fallback. OpenCL is optional and must
   be explicitly probed, never inferred from CUDA visibility.
4. Evaluate with [evaluation.md](references/evaluation.md), visualize with
   [visualization.md](references/visualization.md), and recover failures with
   [troubleshooting.md](references/troubleshooting.md).
5. Run `scripts/smoke_geometry.py` after the installed package and compiled CPU
   extensions are available. It is tiny, deterministic, CPU-only, and has no
   network or source-checkout dependency.

## Core invariants

`star_dist(a,n_rays,grid,mode)` takes a 2D label image and returns `float32`
`(ceil(Y/gy),ceil(X/gx),R)` on the native path. `star_dist3D(lbl,rays,grid,mode)`
takes a label image plus a `Rays_*` object and returns `float32`
`(ceil(Z/gz),ceil(Y/gy),ceil(X/gx),len(rays))`. `dist_to_coord` returns
`(N,2,R)` and `dist_to_coord3D` returns `(N,R,3)`, both in row/column or
`(z,y,x)` coordinates respectively. Dense NMS returns `(points,prob,dist)`;
sparse NMS adds `original_indices`. `matching` returns a metrics named tuple
and optionally match details.

`polygons_to_label` returns a 2D `int32` image. In this baseline a non-empty
native `polyhedron_to_label` result is `int32`, while its empty-point fast path
is `uint16`; normalize explicitly if a downstream format requires one dtype.
