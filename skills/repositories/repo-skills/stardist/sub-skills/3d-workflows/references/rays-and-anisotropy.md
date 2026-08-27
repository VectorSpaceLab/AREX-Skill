# 3D rays, anisotropy, and physical scaling

StarDist 3D represents each candidate object by a center point and one positive
boundary distance per ray. The ray object's vertices are unit-direction-like
vectors in `(Z,Y,X)` order and its triangular faces define a star-convex
polyhedron. The exact ray object is part of the model representation: the
number of distance channels, face connectivity, rendering, and NMS must agree.

## The invariant: ray count is one contract

Use one ray object throughout configuration, data generation, prediction, NMS,
and rendering:

```python
rays = Rays_GoldenSpiral(64, anisotropy=anisotropy)
conf = Config3D(rays=rays, anisotropy=anisotropy)
assert conf.n_rays == len(rays) == len(rays.vertices)
```

Do not write `Config3D(rays=64)` and later pass a 96-ray object to
`star_dist3D`, NMS, or `polyhedron_to_label`. The model's distance head has
`config.n_rays` channels, and the `dist` array must have that same last-axis
length. A mismatch raises an error or, worse, makes a hand-built representation
semantically invalid. When loading a saved model, use the ray object restored
from its serialized `config.json` (`rays_json`) rather than replacing it.

A useful preflight is:

```python
assert dist.ndim == 2 and dist.shape[-1] == len(details["rays"])
assert model.config.n_rays == len(details["rays"])
assert np.asarray(details["rays_vertices"]).shape == (len(details["rays"]), 3)
```

## Factory choices

All built-in factories expose `vertices`, `faces`, `to_json()`, `volume()`,
`surface()`, and `copy(scale=...)`. `faces` are triangle indices into
`vertices`; do not assume a rectangular or lat-long topology unless the chosen
factory provides it.

| Factory | Constructor | Selection guidance |
|---|---|---|
| `Rays_GoldenSpiral` | `Rays_GoldenSpiral(n=70, anisotropy=None)`; at least 4 rays | General-purpose 3D default. Samples a Fibonacci/golden-angle distribution and constructs a convex hull. Use for most objects and increase `n` only when shape detail and compute/memory justify it. It accepts anisotropy directly. |
| `Rays_Cartesian` | `Rays_Cartesian(n_rays_x=11, n_rays_z=5)` | Structured longitude/latitude-like sampling. Total vertices are `n_rays_x * n_rays_z`; the implementation perturbs pole positions slightly to avoid exact duplicates. Choose when a regular spherical grid is wanted and validate the resulting geometry. |
| `Rays_SubDivide` | `Rays_SubDivide(n_level=4)` | Base subdivision implementation; its `base_polyhedron()` is abstract. Select a concrete subclass rather than instantiating the base. Each split replaces every triangle with four and normalizes inserted edge midpoints, so ray count grows quickly. |
| `Rays_Tetra` / `Rays_Octo` | `Rays_Tetra(n_level=4)`, `Rays_Octo(n_level=3)` | Concrete `Rays_SubDivide` choices. Use a tetrahedral or octahedral topology when deterministic hierarchical refinement is useful. Remember that ray count is determined by level and must be read from `len(rays)`, not guessed. |
| `Rays_Explicit` | `Rays_Explicit(vertices0, faces0)` | Use only when a fixed custom spherical mesh is required. Vertices must be `(z,y,x)` triples and faces valid triples of vertex indices. Validate orientation, coverage, positivity, and reproducibility before training. |

`Rays_Base.__getitem__` returns a copy of a vertex; `vertices` and `faces` are
read-only copies. `to_json()` stores a class name plus constructor kwargs. The
model uses that serialization to recreate rays. A hand-edited or untrusted
`rays_json` should not be loaded: the package's `rays_from_json` resolves the
named class dynamically.

## Anisotropy: choose a convention once

For a volume ordered `ZYX`, write anisotropy as `(a_Z, a_Y, a_X)` in the same
order. It describes the relative physical scale/object elongation used by the
ray geometry and training distance probability. The 3D data notebook estimates
a starting value from object extents:

```python
extents = calculate_extents(Y)
anisotropy = tuple(np.max(extents) / extents)
rays = Rays_GoldenSpiral(96, anisotropy=anisotropy)
conf = Config3D(rays=rays, anisotropy=anisotropy)
```

This empirical ratio is only a starting point. If voxel spacing is known,
prefer a physically justified convention and document whether the tuple is
relative voxel spacing or a shape-extent correction. Do not silently reverse
it to `(X,Y,Z)`. A wrong Z factor makes polyhedra, distance targets, NMS, and
physical interpretation inconsistent even when array shapes look valid.

`Rays_GoldenSpiral` constructs its directions by dividing raw `(Z,Y,X)`
vertices by the supplied anisotropy and then normalizing them. `Config3D` also
stores `anisotropy` and compares it with the ray JSON. If a Golden Spiral ray
object has no anisotropy and the config has one, the config propagates it into
the serialized ray kwargs. If both are present but differ, a warning is issued;
treat that warning as a configuration error unless the difference is deliberate
and validated.

The rest of the pipeline must use the same ordering:

- `StarDistData3D` passes `anisotropy` into `edt_prob` and the ray object into
  `star_dist3D`.
- `star_dist3D` returns distances in the ray-object order.
- `StarDist3D._instances_from_prediction` reconstructs rays from `rays_json`
  and uses them in 3D NMS and `polyhedron_to_label`.
- `details["rays_vertices"]`, `points`, and `dist` remain model-facing data in
  `(Z,Y,X)` order.

## `dist_loss_weights`

Every ray object exposes:

```python
weights = rays.dist_loss_weights(anisotropy=(a_Z, a_Y, a_X))
```

It returns one anisotropy-corrected weight per ray, computed from the norm of
`rays.vertices * anisotropy`. Check that `weights.shape == (len(rays),)` and
that all values are finite/positive before using them in a custom loss or
analysis. In StarDist 0.9.2 the standard `Config3D`/`StarDistData3D` training
path does not automatically pass these weights into `train_loss_weights` or
compile a ray-weighted distance loss. `train_loss_weights=(prob,dist[,class])`
weights whole output heads, not individual rays. Do not claim that setting
`anisotropy` automatically enables per-ray loss weighting; use a tested custom
training modification if that is required.

## Physical rescaling at inference

`predict_instances(..., scale=...)` is image resampling, not a replacement for
ray anisotropy. The model first interpolates the input and then rescales
candidate points and ray vectors back. For a `ZYX` image, `scale=(s_Z,s_Y,s_X)`
means exactly that order. A scalar applies to all spatial axes. For a `ZYXC`
image, a four-entry scale follows `ZYXC`; keep the `C` value 1.

The model's internal rescale path uses `(1/s_Z, 1/s_Y, 1/s_X)` for points and
a copied ray object. Therefore compare scaled and unscaled runs in the same
coordinate convention, and inspect both `details["points"]` and
`details["rays_vertices"]`. A scale can change interpolation and detections;
matching coordinates alone does not establish equal segmentation quality.

For standalone geometry, `rays.copy(scale=(s_Z,s_Y,s_X))` returns a deep copy
with its vertices multiplied by those factors. Use it when rendering or
measuring a representation in a deliberately different coordinate system; do
not mutate a model's serialized ray definition casually.

## Ray/geometry checks

CPU-safe checks adapted from the repository evidence:

1. Construct each selected factory and assert faces index valid vertices.
2. Create a small positive distance array whose last dimension is
   `len(rays)`; verify `rays.volume(dist)` and `rays.surface(dist)` return finite
   values.
3. For a synthetic center and positive distances, render with
   `polyhedron_to_label` and verify the output shape is `(Z,Y,X)`.
4. Compare `star_dist3D(label, rays, grid=(1,1,1))` sliced by a grid with
   `star_dist3D(label, rays, grid=grid)`.
5. For anisotropic labels, compare reconstruction with and without anisotropy;
   expect the physically consistent ray choice to be the better representation,
   not necessarily identical voxel masks.

OpenCL parity (`mode="opencl"`) and `use_gpu=True` are optional. The CPU
compiled path (`mode="cpp"`, the normal baseline) must pass before attempting
any OpenCL comparison.
