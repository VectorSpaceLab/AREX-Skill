# Kaolin API overview

Read this when a task needs orientation across the Kaolin package before choosing a focused sub-skill.

## Package map

| Area | Modules | Sub-skill owner |
|---|---|---|
| Geometry containers and I/O | `kaolin.rep`, `kaolin.io`, `kaolin.io.usd`, `kaolin.io.materials` | `geometry-io-representations` |
| Tensor operations and conversions | `kaolin.ops.batch`, `ops.mesh`, `ops.pointcloud`, `ops.voxelgrid`, `ops.conversions`, `ops.spc`, `ops.gaussians` | `ops-metrics-conversions` |
| Metrics/math | `kaolin.metrics`, `kaolin.math.quat` | `ops-metrics-conversions` |
| Rendering | `kaolin.render.camera`, `render.mesh`, `render.easy_render`, `render.lighting`, `render.materials`, `render.spc` | `rendering-cameras-lighting` |
| Physics | `kaolin.physics.simplicits`, `physics.materials`, `physics.common`, `physics.utils`, `kaolin.experimental.newton` | `physics-simulation` |
| Visualization | `kaolin.visualize`, `kaolin.experimental.dash3d` | `visualization-workflows` |
| Utilities | `kaolin.utils`, `kaolin.utils.testing`, `kaolin.utils.env_vars` | Root troubleshooting or nearest owner |

## Cross-skill handoff pattern

1. **Geometry owner** loads/constructs containers and records tensor shapes, attributes, file format, and optional dependencies.
2. **Ops owner** transforms, converts, samples, packs, or measures tensors; it records layout, backend, and randomness.
3. **Rendering or physics owner** consumes validated geometry/tensors and probes backend-specific execution.
4. **Visualization owner** logs, displays, or serves outputs, without owning the geometry/render/simulation algorithm.

## Backend-sensitive surfaces

- Kaolin `_C` compiled extension: required for many high-performance operations.
- CUDA: required for full Kaolin functionality, especially SPC, rasterization/DIB-R, many conversions, and simulation flows.
- USD/`pxr`: optional but needed for USD import/export and rich Timelapse outputs.
- `nvdiffrast`: optional rendering backend.
- Warp/Newton: optional physics/experimental backend.
- Jupyter widgets, Flask/Tornado, browser/WebGL: optional visualization frontends.

Always probe the exact surface before executing a backend-specific workflow.

## Version/source drift rule

Kaolin source and installed wheels can differ, especially on unreleased branches. If an API is in source but missing from the installed package, record the drift and either install a compatible source/wheel build or avoid claiming that the installed package supports that API. This matters for current-source Gaussian splat modules and other new functionality.
