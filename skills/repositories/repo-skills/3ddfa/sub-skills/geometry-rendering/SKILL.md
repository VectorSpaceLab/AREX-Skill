---
name: geometry-rendering
description: "Reconstruct 3DMM vertices, serialize mesh outputs, and manage
  3DDFA rendering helpers."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# geometry-rendering

Use this sub-skill for the geometry side of 3DDFA: parameter reconstruction, ROI-to-image conversion, sparse and dense vertices, mesh serialization, pose matrices, depth/PNCC/PAF outputs, and the Cython-backed render path.

## Use when
- you have a 62-D parameter vector or cropped ROI and need 68 landmarks or dense vertices;
- you need PLY, OBJ, `.mat`, depth, PNCC, PAF, or pose artifacts;
- you need to build or troubleshoot `utils.cython`;
- you need dense render or video assembly helpers.

## Start here
- [API reference](references/api-reference.md)
- [Output formats](references/output-formats.md)
- [Rendering and Cython](references/rendering-and-cython.md)
- [Data artifacts](references/data-artifacts.md)
- [Troubleshooting](references/troubleshooting.md)

## Bundled helpers
- [scripts/smoke_geometry.py](scripts/smoke_geometry.py)
- [scripts/images_to_video.py](scripts/images_to_video.py)

## Route elsewhere
- Full detector/model inference and CLI flags belong in the sibling inference sub-skill.
- Training losses, benchmark scripts, and dataset preparation belong in the training sub-skill.
- ONNX export and the C++ port belong in the C++ sub-skill.

## Working facts
- `utils.ddfa.reconstruct_vertex` is the canonical 3DMM reconstruction entry point.
- The verified smoke for a zero 62-D vector returns sparse `(3, 68)` and dense `(3, 53215)` vertices.
- `visualize/tri.mat` provides the triangle indices used by the renderer paths.
- `utils.render` and `utils.lighting` depend on the compiled `mesh_core_cython` extension.
