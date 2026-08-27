---
name: core-data-and-geometry
description: "Routes PhiFlow field, geometry, mesh, scene, and data-format workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Core Data and Geometry

Use this sub-skill for the core PhiFlow objects that most other workflows build
on: fields, grids, geometries, meshes, scenes, and field/scene I/O.

## Route here for

- `CenteredGrid`, `StaggeredGrid`, `PointCloud`, `Noise`, and `AngularVelocity`
- `Box`, `Sphere`, `Cuboid`, `Cylinder`, `UniformGrid`, `Mesh`, `Graph`,
  `Heightmap`, `SDFGrid`, and `SDF`
- `Scene.create()`, `Scene.at()`, `Scene.list()`, `Scene.write()`,
  `Scene.read()`, and scene cleanup helpers
- `field.read()`, `field.write()`, `field.resample()`, `field.sample()`, and
  `field.reduce_sample()`
- `Geometry` transformations and set operations such as `shift`, `rotate`,
  `union`, and `intersection`
- scene / field file formats and legacy compatibility issues

## Do not route here

- installation or backend setup -> `installation-and-backends`
- PDE stepping, fluids, waves, FLIP, or SPH -> `physics-and-simulation`
- gradients, Jacobians, or inverse design -> `optimization-and-learning`
- plotting, display, controls, or scalar logs -> `visualization-and-ui`

## Start with these imports

```python
from phi.flow import *
from phi import field, geom, math
from phiml.math import batch, channel, instance, spatial, vec
```

## Most common decisions

1. **Grid type:** use `CenteredGrid` for scalar quantities and `StaggeredGrid`
   for velocity-like vector fields.
2. **Sampling vs resampling:** use `field.sample()` when you need values at a
   `Geometry`; use `field.resample()` or `Field.at()` when you need compatible
   field representations.
3. **Scene I/O:** use `Scene.create()` for new scenes, `Scene.write()` to store
   fields, and `Scene.read()` to recover them. The scene format stores `sim_`
   folders with `*.npz` field files.
4. **Geometry syntax:** prefer keyword constructors such as `Box(x=1, y=1)` or
   the explicit slicing form `Box['x,y', 0:1, 0:1]`.
5. **Mesh / implicit geometry:** use `Mesh` for unstructured surfaces or
   volumes, and `SDFGrid` / `SDF` when you want implicit shapes.
6. **Legacy code:** treat `Domain` as compatibility-only. New workflows should
   construct grids directly with dictionaries and `extrapolation=` or
   `boundary=` values.

## Verified signatures to rely on

- `Scene.create(parent_directory, shape=(), name='sim', copy_calling_script=True, **dimensions)`
- `Scene.write(self, data=dict=None, frame=0, **kw_data)`
- `Scene.read(self, *names, frame=0, convert_to_backend=True)`
- `field.read(file, convert_to_backend=True)` / `field.write(field, file)`
- `field.resample(value, to, keep_boundary=False, **kwargs)`
- `field.sample(field, geometry, at='center', boundary=None, **kwargs)`
- `field.reduce_sample(field, geometry, **kwargs)`
- `Box(*args, **kwargs)` and `Box['x,y', ...]`
- `geom.Box`, `geom.Sphere`, `geom.Cylinder`, `geom.Mesh`, `geom.Graph`,
  `geom.Heightmap`, `geom.SDFGrid`, and `geom.SDF`

## Bundled references and helper

- Detailed workflows: [`references/workflows.md`](references/workflows.md)
- Failure handling: [`references/troubleshooting.md`](references/troubleshooting.md)
- Scene round-trip smoke: [`scripts/scene_roundtrip.py`](scripts/scene_roundtrip.py)

From this sub-skill directory, run the smoke helper when you want to verify the
field / scene I/O path:

```bash
python scripts/scene_roundtrip.py --resolution 16
```

The helper writes temporary scene data, reads it back through both the scene
API and `field.read()`, and cleans up afterwards.
