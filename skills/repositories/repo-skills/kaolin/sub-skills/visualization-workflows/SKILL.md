---
name: visualization-workflows
description: "Operate Kaolin visualization workflows for Timelapse USD
  checkpoints, Jupyter visualizers, Dash3D, GLTF inspection, and visualization
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# visualization-workflows

Use this sub-skill when the task is about **showing, logging, inspecting, or troubleshooting Kaolin visualization outputs** rather than creating the geometry or rendering algorithm itself.

## Scope

Use this sub-skill for:

- Writing and validating `kaolin.visualize.Timelapse` checkpoint log directories.
- Reading Timelapse layout metadata with `TimelapseParser`.
- Starting or planning `kaolin-dash3d` / `kaolin.experimental.dash3d` safely.
- Building Jupyter/IPython visualization cells with `quick_viz`, `IpyTurntableVisualizer`, `IpyFirstPersonVisualizer`, `ipycanvas`, `ipyevents`, and `ipywidgets`.
- Composing GLTF interactive visualization notebooks after geometry loading and rendering functions already exist.
- Diagnosing missing USD/OpenUSD `pxr`, browser, Jupyter, `ipycanvas`, `ipyevents`, Flask, Tornado, or Matplotlib dependencies.

Route elsewhere when the request is primarily about:

- Mesh/point cloud/GLTF/USD data loading or representation conversion: use the geometry/IO sub-skill.
- Tensor operations, sampling, voxel/SPC conversion, metrics, or losses: use the ops/metrics sub-skill.
- Camera math, lighting, rasterization, differentiable rendering, nvdiffrast, or shader behavior: use the rendering/cameras/lighting sub-skill.
- Physics simulation loops or Simplicits output generation: use the physics sub-skill.

## First steps for a visualization task

1. Identify the requested surface:
   - Timelapse log writer/parser
   - Dash3D web visualizer
   - Jupyter/IPython viewer
   - GLTF interactive notebook composition
   - dependency/server/browser troubleshooting
2. Check whether the input data already exists. Do **not** generate new geometry or implement rendering algorithms here; ask the appropriate owner to produce tensors, meshes, point clouds, cameras, or render functions.
3. Load only the smallest relevant bundled reference:
   - [API reference](references/api-reference.md) for signatures and supported types.
   - [Workflows](references/workflows.md) for copyable task patterns.
   - [Troubleshooting](references/troubleshooting.md) for dependency and runtime failures.
4. Prefer safe probes and dry-run planning before launching UI/server code. `run_main()` and `kaolin-dash3d` start a long-lived server loop.

## Safe bundled helper

Use [scripts/kaolin_dash3d_help.py](scripts/kaolin_dash3d_help.py) when an automation needs to inspect Dash3D command arguments, check a Timelapse-style directory, or produce a launch command without starting an endless server.

Typical safe commands:

```bash
python scripts/kaolin_dash3d_help.py --help
python scripts/kaolin_dash3d_help.py --logdir ./viz --inspect-logdir
python scripts/kaolin_dash3d_help.py --check-imports
```

The helper intentionally does **not** start Dash3D. Start the real server only when a human or bounded supervisor is ready to stop it:

```bash
kaolin-dash3d --logdir=./timelapse-logdir --port=8080 --log_level=20
```

## Verification guidance

Native verification candidates for this sub-skill are Timelapse writer/parser tests and Dash3D argument/help/parser checks. Notebook and browser UI cases are useful but optional and should not be run by default in headless automation.

Hard synthetic cases to keep supported:

- Verify a Timelapse log directory and produce the Dash3D launch command without starting a persistent server.
- Diagnose missing `ipycanvas`, `ipyevents`, Jupyter/browser, Matplotlib, Flask/Tornado, or `pxr` dependencies from symptoms and safe import probes.
