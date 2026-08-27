---
name: kaolin
description: "Route NVIDIA Kaolin repository workflows for 3D deep learning
  geometry I/O, operations, rendering, physics, visualization, installation, and
  backend troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Kaolin repo skill

Use this repo skill when a task involves **NVIDIA Kaolin**, the PyTorch library for 3D deep-learning research: geometry containers and I/O, tensor operations and conversions, differentiable rendering, Simplicits physics, Gaussian splats, SPC octrees, visualization, or Kaolin-specific installation/backend failures.

## Read first

- [Repository provenance](references/repo-provenance.md) before deciding whether this skill matches a checkout or installed package.
- [Installation and backends](references/installation-and-backends.md) for PyTorch/CUDA/Kaolin wheel/source install guidance, optional dependencies, and environment variables.
- [API overview](references/api-overview.md) for the package/module map and cross-skill handoff conventions.
- [Troubleshooting](references/troubleshooting.md) for cross-cutting import, `_C`, CUDA, optional dependency, source-shadowing, and version-drift failures.
- [Environment checker](scripts/check_kaolin_environment.py) for a safe import/backend/optional-dependency diagnostic.

## Route map

| User intent | Read |
|---|---|
| Load/export meshes, Gaussian splats, USD/OBJ/GLTF/PLY/OFF files, `SurfaceMesh`, `Spc`, materials, datasets, or data-layout validation | [geometry-io-representations](sub-skills/geometry-io-representations/SKILL.md) |
| Run Kaolin tensor ops, packed/padded utilities, mesh/point/voxel/SPC/Gaussian conversions, quaternion math, or metrics | [ops-metrics-conversions](sub-skills/ops-metrics-conversions/SKILL.md) |
| Configure cameras, rays, differentiable rasterization, DIB-R, easy PBR rendering, lighting, materials, or render backend probes | [rendering-cameras-lighting](sub-skills/rendering-cameras-lighting/SKILL.md) |
| Use Simplicits, physics materials, Warp/CUDA simulation checks, point/mesh/Gaussian physics planning, or experimental Newton coupling | [physics-simulation](sub-skills/physics-simulation/SKILL.md) |
| Write/read Timelapse logs, Jupyter/IPython visualizers, Dash3D/web UI, GLTF visualization, or browser/notebook troubleshooting | [visualization-workflows](sub-skills/visualization-workflows/SKILL.md) |

## Installation baseline

Kaolin is a PyTorch extension package. For broad functionality, prefer a CUDA-capable environment with a supported PyTorch/Kaolin wheel pair, then verify:

```bash
python -c "import torch, kaolin; print(torch.__version__, torch.cuda.is_available(), getattr(kaolin, '__version__', None))"
python scripts/check_kaolin_environment.py --json
```

CPU-only installs can validate pure Python and many tensor/data tasks, but they do **not** prove CUDA-extension workflows such as SPC kernels, differentiable rasterization, several conversions, and full simulation paths.

## Operating rules

1. Do not treat a successful `import kaolin` as proof that `_C`, CUDA, USD, nvdiffrast, Warp, notebook widgets, or browser visualization workflows are ready. Probe the backend that the user actually needs.
2. Keep source-checkout and installed-wheel drift explicit. Current source may include APIs not re-exported by an older installed wheel; verify the exact import path before promising a workflow.
3. Use sibling sub-skills in sequence for multi-stage tasks: geometry I/O → ops/conversions → rendering/physics → visualization/export.
4. Do not run notebooks, long simulations, browser servers, dataset downloads, benchmarks, or destructive export overwrites unless the user explicitly authorizes them.
5. Avoid absolute local paths in advice. Ask the user for their asset paths, dataset roots, output paths, and backend constraints.

## Common task starts

- “Load this OBJ/GLTF/USD and render it” → geometry first, then rendering.
- “Convert points/mesh/voxel/SPC/Gaussians or compute Chamfer/F-score” → ops/metrics.
- “My `kaolin._C`/SPC/rasterize op fails” → root troubleshooting plus ops/rendering probe.
- “Use Simplicits or Newton with a mesh or Gaussian scene” → geometry/ops for data prep, then physics.
- “Show training outputs in Dash3D or a notebook” → visualization, with root backend check if imports fail.
