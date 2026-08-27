---
name: rendering-cameras-lighting
description: "Operate Kaolin camera, ray generation, differentiable
  rasterization, easy PBR rendering, lighting, and material workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# rendering-cameras-lighting

Use this sub-skill when a Kaolin task starts with a **camera/ray** or ends with a **rendered image**: camera construction, coordinate changes, ray generation, DIB-R/rasterization, easy PBR mesh rendering, spherical lighting, PBR materials, backend choice, or rendering diagnostics.

## Read first

- [API reference](references/api-reference.md) for camera, ray, rasterization, easy render, lighting, material, and backend contracts.
- [Workflows](references/workflows.md) for copyable operating patterns from camera setup through `SurfaceMesh` rendering.
- [Troubleshooting](references/troubleshooting.md) for `_C`, CUDA, `nvdiffrast`, camera/device, texture/material, and blank-render failures.
- [Camera smoke](scripts/camera_smoke.py) for a CPU-safe camera/ray/lighting smoke check.
- [Render backend probe](scripts/render_backend_probe.py) for safe backend and optional tiny rasterization checks.

## Use when

- A task asks for `kaolin.render.camera`, `Camera`, `PinholeIntrinsics`, orthographic/pinhole camera setup, camera coordinate conventions, view/projection transforms, ray generation, or differentiable camera optimization.
- A task asks for `kaolin.render.mesh.rasterize`, `dibr_rasterization`, DIB-R-style soft masks, image-space feature interpolation, or choosing between `cuda`, `nvdiffrast`, and `nvdiffrast_fwd` rasterization paths.
- A task has an already available `SurfaceMesh` and wants an image or render passes using `kaolin.render.easy_render.render_mesh`, `default_camera`, `default_lighting`, `default_material`, `PBRMaterial`, or `SgLightingParameters`.
- A task needs diagnosis for missing Kaolin CUDA extension `_C`, unavailable `nvdiffrast`, camera/grid device mismatch, invalid render backend, all-background `face_idx`, or material/UV/texture issues.

## Route elsewhere

- Mesh loading, `SurfaceMesh` construction, OBJ/USD/GLTF/PLY details, datasets, or representation ownership: route to `geometry-io-representations`.
- Generic tensor packing, mesh/SPC/voxel/Gaussian conversions, metrics, quaternion math, or loss functions: route to `ops-metrics-conversions`.
- Timelapse logs, Jupyter widgets, Dash3D/browser UI, server lifecycle, or result presentation: route to `visualization-workflows`.
- Physics simulation setup or Simplicits renderable point outputs: route to `physics-simulation` before rendering them.

## Operating rules

1. Choose the smallest render layer: camera/ray helpers for camera-only tasks, `easy_render.render_mesh` for a full PBR image, and low-level `rasterize`/`dibr_rasterization` only when the user needs custom image-space features, gradients, or silhouette masks.
2. Keep camera, grids, mesh tensors, lighting, and material tensors on a consistent device and dtype. `Camera.from_args` rejects mixed-device constructor tensors unless `device=` resolves them; ray generators assert custom grids match `camera.device`.
3. Treat `nvdiffrast` as optional. `render_mesh(..., backend=None)` auto-picks `nvdiffrast` when installed and otherwise the bundled CUDA renderer; pin `backend="cuda"` to avoid the optional dependency.
4. Do not load meshes here. If the input is not already a valid `SurfaceMesh` with expected attributes, ask the geometry/IO owner to prepare it, then return to this sub-skill for camera/rendering.
5. Do not promise real rendering until backend readiness is known. Use `python scripts/render_backend_probe.py --json` for an import/backend summary and add `--probe-rasterize` only when a tiny CUDA/nvdiffrast rasterization check is appropriate.
6. For render-output diagnostics, inspect `RenderPass.face_idx` for coverage and `RenderPass.render.name` for the composited image; missing optional passes often mean the mesh lacks UVs, normals, tangents, features, or material assignments.

## Minimal decision flow

1. Identify intent: camera/ray setup, easy PBR rendering, low-level rasterization/DIB-R, lighting/material work, or backend troubleshooting.
2. Confirm the input ownership: render tasks consume an existing `SurfaceMesh`; loading/normalizing/importing it belongs elsewhere.
3. Build or validate a single camera for `render_mesh`; split or loop over batched cameras because high-level rendering is single-camera/single-mesh.
4. Select backend policy: auto, forced bundled CUDA, forced `nvdiffrast`, or low-level `nvdiffrast_fwd` for forward-only nvdiffrast with Kaolin CUDA backward.
5. Probe before CUDA-sensitive execution; record optional dependency gaps rather than silently falling back when the user requested a specific backend.
6. If optimizing camera or lighting, enable gradients explicitly and constrain parameters with `gradient_mask` or optimizer parameter groups.
