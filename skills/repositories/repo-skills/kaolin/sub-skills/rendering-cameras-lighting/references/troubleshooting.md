# Troubleshooting: Kaolin rendering, cameras, lighting

Start with safe probes before running expensive rendering:

```bash
python scripts/camera_smoke.py --json
python scripts/render_backend_probe.py --json
```

Add `--probe-rasterize` only when you need to verify a tiny CUDA/nvdiffrast rasterization path.

## Camera and ray-generation failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `Camera construction failed due to ambiguous parameters` | `Camera.from_args` received incompatible or incomplete constructor hints. | Supply one extrinsics set (`eye`/`at`/`up`, `view_matrix`, or `cam_pos`/`cam_dir`) and one intrinsics set (`fov`, `focal_x`, or `fov_distance`) plus `width` and `height`. |
| `Camera construction with tensors args on different devices is not allowed...` | Some constructor tensors are on CPU and others on CUDA, with no explicit device. | Move inputs to one device or pass `device="cuda"` / `device="cpu"` explicitly. |
| `Camera extrinsics and intrinsics use different devices` or different dtypes | Only one camera component was moved or cast. | Use `camera = camera.to(device)` / `.cuda()` / `.float()` on the full `Camera`, or rebuild from consistent components. |
| `CameraExtrinsics of device ... cannot transform vectors of device ...` | Vectors, mesh vertices, or rays are not on the same device as the camera. | Move tensors with `.to(camera.device, camera.dtype)` before `transform`, `inv_transform_rays`, or rendering. |
| `generate_pinhole_rays() supports only camera input of batch size 1` | Batched camera passed to single-camera ray generation. | Iterate over the camera batch or index with `camera[i]`. |
| `Expected camera and coords_grid[...] to be on the same device` | Custom ray grid tensors were built on a different device. | Create grids with `device=camera.device` or move both grid tensors to `camera.device`. |
| Rays or projections point the wrong way | Coordinate-system mismatch or wrong view matrix convention. | Confirm Kaolin's default right-handed world, column-major world-to-camera view matrix, and left-handed NDC depth convention. Use `change_coordinate_system(blender_coords())` only for axis basis changes. |

Safe camera check:

```bash
python scripts/camera_smoke.py --resolution 32 --device cpu --json
```

If the intended render uses CUDA, repeat with `--device cuda` only after confirming CUDA is available.

## Easy-render failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `Render is only implemented for single unbatched camera` | `render_mesh` received a camera batch. | Loop over cameras or pass `camera[0]`. |
| `Render is only implemented for mesh of length 1` | `render_mesh` received a batched `SurfaceMesh`. | Slice or prepare one mesh at a time. Mesh batching decisions belong to the geometry/IO owner. |
| `Unsupported backend ...` | `render_mesh` only accepts `"cuda"`, `"nvdiffrast"`, or `None`. | Use `backend=None` for auto, `backend="cuda"` for bundled CUDA, or `backend="nvdiffrast"` for optional nvdiffrast. Low-level `rasterize` also supports `"nvdiffrast_fwd"`. |
| Output image is all black/empty and `face_idx` is all `-1` | Camera does not frame the mesh, mesh not normalized for the default camera, near/far planes exclude it, or axes are mismatched. | Inspect `result[RenderPass.face_idx]`, camera pose, near/far, and coordinate basis. Ask geometry/IO or ops owner to normalize/center mesh if needed. |
| `features` pass is missing | Mesh lacks `face_features`. | This is expected unless features are present or computed. Check `result.keys()` before indexing. |
| `uvs`, textured albedo, or normal maps are missing | Mesh lacks UVs, `face_uvs_idx`, tangents, or material texture fields. | Verify mesh attributes before rendering; fallback to `default_material` or constant material if UVs are unavailable. |
| Warning about mesh transform being applied | Mesh has a `transform` attribute. | `render_mesh` transforms it to world space for the render. For repeated renders, ask the geometry owner to bake the transform once. |

Remember the mixed output-key convention:

```python
image = result[RenderPass.render.name]  # string key "render"
face_idx = result[RenderPass.face_idx]  # enum key
```

Do not assume `alpha` or `roughness` is returned; check `result.keys()`.

## CUDA extension `_C` problems

| Symptom | Meaning | Fix / probe |
|---|---|---|
| Import error mentioning `_C` | Kaolin's compiled extension is missing or incompatible with the current PyTorch/CUDA/Python combination. | Install a matching Kaolin wheel or rebuild in a CUDA toolkit environment. Use `python scripts/render_backend_probe.py --json` to record `_C` presence. |
| Bundled `cuda` rasterization fails before any render output | CUDA kernels are unavailable, GPU is not visible, or tensors are not CUDA tensors. | Check `torch.cuda.is_available()`, selected device, and `_C` fields in `render_backend_probe.py`. Then try `--probe-rasterize --backend cuda`. |
| CPU-only environment but user requests DIB-R/easy-render CUDA | CPU camera math is possible, but rasterization kernels are not. | Report a backend gate. Do not claim full render verification; offer camera/ray smoke only. |

Use this command for a tiny kernel check after confirming a CUDA environment is expected:

```bash
python scripts/render_backend_probe.py --probe-rasterize --backend cuda --json
```

## `nvdiffrast` problems

| Symptom | Meaning | Fix / probe |
|---|---|---|
| `nvdiffrast must be installed to be used as backend` | `backend="nvdiffrast"` was forced but `nvdiffrast.torch` could not import. | Install the optional package or use `backend="cuda"` if fallback is allowed. |
| Auto backend unexpectedly uses CUDA | `nvdiffrast` is not importable. | This is the expected `backend=None` fallback. If the user explicitly requires nvdiffrast, report the missing optional dependency. |
| Context creation fails | `nvdiffrast` exists but CUDA/context setup failed. | Run `python scripts/render_backend_probe.py --probe-nvdiffrast-context --json`; check CUDA visibility and driver/toolkit compatibility. |
| nvdiffrast test or probe fails on `torch.double` tensors | nvdiffrast paths are float32-oriented in Kaolin tests. | Use float32 tensors for nvdiffrast or switch to bundled `cuda` backend when double precision is required. |
| Rasterization shape/resolution issue | nvdiffrast CUDA context has resolution constraints. | Try height/width multiples of 8, or use `backend="cuda"` for the bundled rasterizer. |

Probe optional backend explicitly:

```bash
python scripts/render_backend_probe.py --probe-nvdiffrast-context --probe-rasterize --backend nvdiffrast --json
```

## Material and texture issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Texture map has no visible effect | Missing UVs or no material assignment reaches the visible faces. | Check `mesh.uvs`, `mesh.face_uvs_idx`, `mesh.face_uvs`, and `mesh.material_assignments`; use `face_idx` to confirm the intended faces are visible. |
| Material tensors on CPU while camera/mesh are CUDA | `PBRMaterial` was not moved with the render tensors. | Use `material = material.to(camera.device)` or `.cuda()`. |
| Shape assertion while constructing `PBRMaterial` | Color/scalar values or textures have wrong rank. | RGB color values are `(3,)`; scalar values are `(1,)`; texture attributes are 3D tensors. |
| Diffuse/specular texture appears transposed or incorrectly sampled | HWC/CHW layout mismatch or UV convention mismatch. | Use `material.chw()` / `material.hwc()` to inspect layout. Manual `texture_mapping` expects texture maps as `(B, C, H, W)` and UVs in `[0, 1]`. |
| Metallic/specular behavior seems wrong | `is_specular_workflow` does not match the material fields. | `is_specular_workflow=True` uses specular fields. If false, metallic fields drive the specular albedo and specular fields may be ignored. |
| Renderer logs missing UV map | Textures cannot be sampled without UVs. | Provide UV attributes via the geometry/IO owner or fall back to constant diffuse/specular values. |

For a controlled fallback, render with a default material:

```python
from kaolin.render.easy_render import default_material
material = default_material(diffuse_color=(0.8, 0.2, 0.2)).to(camera.device)
result = render_mesh(camera, mesh, custom_materials=[material], backend="cuda")
```

## Lighting issues

| Symptom | Likely cause | Fix |
|---|---|---|
| Lighting tensors on wrong device | `default_lighting()` returns CPU tensors. | Use `lighting = default_lighting().to(camera.device)` or `.cuda()`. |
| Custom SG lighting shape error | `amplitude`, `direction`, and `sharpness` do not have compatible SG counts. | Use `(num_sg, 3)` for amplitude and direction and `(num_sg,)` for sharpness; scalar values are expanded by `SgLightingParameters`. |
| Shading too dim/bright | SG amplitude/sharpness or material albedo/specular values are out of expected range. | Inspect material values and SG amplitudes; `render_mesh` output is not clamped. |
| Lighting direction seems rotated | Coordinate basis mismatch. | Generate directions in the same y-up convention as the camera/mesh, or apply coordinate-system changes consistently. |

## Low-level DIB-R/rasterization issues

| Symptom | Likely cause | Fix |
|---|---|---|
| `rasterize` shape error | `face_vertices_z`, `face_vertices_image`, or `face_features` not batched correctly. | Use `(B, F, 3)`, `(B, F, 3, 2)`, and `(B, F, 3, C)`; lists/tuples are allowed for multiple feature groups. |
| Backward gradients vanish or explode | Rasterization `eps`, triangle scale, or DIB-R `sigmainv`/`boxlen` not appropriate. | Tune `eps`, `multiplier`, `sigmainv`, `boxlen`, and `knum`; keep triangles in normalized image coordinates. |
| Soft mask misses boundary faces | `boxlen` or `knum` too small for the chosen `sigmainv`. | Increase `boxlen` or `knum` cautiously. |
| Low-level path works but easy render fails | Material, normals, UVs, single-camera/single-mesh constraint, or backend auto-selection issue. | Use `render_backend_probe.py`, check mesh attributes, then compare `rasterize` output with `render_mesh` inputs. |

## Escalation checklist

Before escalating outside this sub-skill, record:

1. Which path was attempted: camera/raygen, `render_mesh`, `rasterize`, or `dibr_rasterization`.
2. Camera length, resolution, dtype, device, lens type, and coordinate-system assumption.
3. Mesh batch length and whether UVs, normals, materials, and material assignments exist.
4. Backend requested, backend actually chosen, `_C` presence, CUDA availability, and `nvdiffrast` availability.
5. Output keys and whether `face_idx` contains any non-background pixels.
