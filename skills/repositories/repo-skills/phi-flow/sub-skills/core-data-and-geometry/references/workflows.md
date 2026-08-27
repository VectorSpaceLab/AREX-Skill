# Core Data and Geometry Workflows

## Public surface map

PhiFlow's core data model is built from `Field`, `Geometry`, and `Scene`.
The most common user-facing types are:

- `CenteredGrid` and `StaggeredGrid` for sampled fields on regular grids
- `PointCloud` for particle collections
- `Noise` and `AngularVelocity` for common field initializers
- `Box`, `Sphere`, `Cuboid`, `Cylinder`, `UniformGrid`, `Mesh`, `Graph`,
  `Heightmap`, `SDFGrid`, and `SDF` for geometry and mesh workflows
- `Scene` for persistent scene-backed simulation data

## Fields and grids

| Need | API | Safe default | Notes |
| --- | --- | --- | --- |
| Scalar field on a grid | `CenteredGrid(value, extrapolation, **domain)` | `extrapolation.BOUNDARY` or `ZERO` | Best for smoke, density, pressure, and scalar data. |
| Vector / staggered field | `StaggeredGrid(value, extrapolation, **domain)` | `extrapolation.ZERO` or `BOUNDARY` | Matches MAC-style fluid velocities and similar vector fields. |
| Particle set | `PointCloud(geometry, values=None)` | Start from a `Sphere` or `Box` geometry | Use when the elements are discrete points or particles. |
| Procedural field | `Noise(...)` | Small resolutions first | Great for smoke, masks, or synthetic examples. |
| Vortex-like field | `AngularVelocity(...)` | Explicit center / strength | Useful for rotating obstacle or point-field workflows. |

The current field layer also exposes `field.resample()`, `field.sample()`,
`field.reduce_sample()`, and `Field.at()` / `@` to move between compatible
representations.

## Geometry workflows

### Constructors and transformations

- `Box(x=..., y=..., z=...)` for axis-aligned boxes with keyword dimensions.
- `Box['x,y', 0:1, 0:1]` for the explicit slicing constructor.
- `Sphere(center=..., radius=...)`, `Cuboid(...)`, and `Cylinder(...)` for
  common primitives.
- `geom.union(...)` and `geom.intersection(...)` for set operations.
- `geometry.shift(delta)` and `geometry.rotate(angle)` for transforms.

### Mesh and implicit geometry

- `Mesh` represents unstructured geometry with vertices, elements, and boundary
  metadata.
- `Graph` represents graph-based neighborhood information.
- `Heightmap`, `SDFGrid`, and `SDF` are useful when the shape is implicit or
  surface-like rather than explicitly meshed.
- `mesh_from_numpy()` and related helpers are available for mesh construction
  workflows that start from raw arrays or triangle data.

## Scene and field I/O

PhiFlow stores scene data in `sim_000000`-style directories.
Inside a scene, field arrays are saved as compressed `*.npz` files, typically
one file per field name and frame. `Scene` also keeps small metadata files such
as `description.json` and optional log files.

### Recommended round-trip pattern

```python
import tempfile

scene = Scene.create(tempfile.mkdtemp(prefix="phiflow-scenes-"))
scene.write(smoke=smoke, velocity=velocity)
smoke2 = scene.read("smoke")
velocity2 = scene.read("velocity")
field.assert_close(smoke, smoke2)
field.assert_close(velocity, velocity2)
```

### When to use `field.read()` / `field.write()`

Use the field-level helpers for a single stored grid file when you already know
its path. Use `Scene` when you want the scene directory, metadata, or batched
scene handling.

## Useful validation steps

- Compare field values with `field.assert_close()` after sampling or resampling.
- Check `Scene.fieldnames`, `Scene.frames`, and `Scene.complete_frames` when
  debugging saved data.
- Prefer tiny grids for smoke tests; the goal is shape and format correctness,
  not performance.
