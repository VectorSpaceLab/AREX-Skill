# API reference: rendering, cameras, lighting

This reference is intentionally self-contained. It names Kaolin modules and contracts but does not require reopening repository sources or examples at runtime.

## Core conventions

- Kaolin cameras combine batched `CameraExtrinsics` and `CameraIntrinsics` objects. The two components must have the same batch length, dtype, and device.
- Default world coordinates are right-handed Cartesian with `Y` up and `Z` pointing out of the screen. Camera NDC uses a left-handed depth direction, and the default NDC range is `[-1, 1]`.
- View matrices are column-major world-to-camera matrices. The inverse view matrix is camera-to-world.
- `Camera.transform(points)` maps world coordinates to NDC and broadcasts over camera batches. Low-level rasterization consumes already projected face vertices in image/NDC coordinates.
- `render.easy_render.render_mesh` is high-level and currently handles **one unbatched camera and one unbatched `SurfaceMesh`**. Loop or slice when inputs are batched.
- Rendering backends that execute kernels require a CUDA-capable Kaolin package. `nvdiffrast` is optional and independent from Kaolin's bundled CUDA extension.

## Camera construction and transforms

| API | Use it for | Contract and cautions |
|---|---|---|
| `Camera(extrinsics, intrinsics)` | Compose a camera from prebuilt components. | `len(extrinsics) == len(intrinsics)` and devices must match. Prefer `Camera.from_args` unless you need explicit component control. |
| `Camera.from_args(**kwargs)` | Flexible camera construction. | Give exactly one extrinsics description such as `eye`/`at`/`up`, `view_matrix`, or `cam_pos`/`cam_dir`, and one intrinsics description such as `fov`, `focal_x`, or `fov_distance`; include `width` and `height`. Mixed-device tensor kwargs require an explicit `device=`. |
| `Camera.as_dict()` / `Camera.from_dict(d)` | Serialize one camera for JSON/YAML-like configs. | `as_dict()` only supports a single camera, not a camera batch. |
| `Camera.to(...)`, `.cpu()`, `.cuda()`, `.float()`, `.double()`, `.half()` | Move or cast complete cameras. | Use these instead of moving only intrinsics or extrinsics when rendering. |
| `Camera.transform(vectors)` | World-space points to NDC. | Accepts `(B, 3)` or `(C, B, 3)`; a single camera preserves input shape, while batches broadcast to `(C, B, 3)`. |
| `Camera.view_projection_matrix()` | Matrix-based world-to-clip/NDC workflows. | Only defined for linear projection lenses such as pinhole and orthographic cameras. |
| `Camera.generate_rays(coords_grid=None)` | Lens-aware ray generation. | Delegates to pinhole or orthographic ray generation; still expects a single unbatched camera for ray generation. |
| `Camera.cat(cameras)` and `camera[i]` | Build and index camera batches. | Keep widths, heights, near/far planes, and intrinsics type compatible. High-level rendering still needs one camera at a time. |
| `Camera.requires_grad_(True)` and `Camera.gradient_mask(...)` | Camera optimization. | Enabling gradients also moves extrinsics to a differentiable backend unless a backend was manually pinned. Use masks such as `gradient_mask('t', 'focal_x', 'focal_y')` to constrain optimization. |
| `camera.change_coordinate_system(basis)` / `reset_coordinate_system()` | Match Blender/OpenGL-style axes. | Built-in helpers include `blender_coords()` and `opengl_coords()`. This changes extrinsic axes, not mesh vertices. |

## Extrinsics helpers

| API | Notes |
|---|---|
| `CameraExtrinsics.from_lookat(eye, at, up, dtype=None, device=None, requires_grad=False, backend=None)` | Common look-at construction. Uses OpenGL-style right-handed camera conventions by default. |
| `CameraExtrinsics.from_camera_pose(cam_pos, cam_dir, ...)` | Build from camera center and orientation in world coordinates. |
| `CameraExtrinsics.from_view_matrix(view_matrix, ...)` | Build from a world-to-camera view matrix of shape `(C, 4, 4)` or `(4, 4)`. |
| `extrinsics.view_matrix()` / `inv_view_matrix()` | World-to-camera and camera-to-world matrices. |
| `extrinsics.transform(vectors)` | World points to camera space. Dtype and device must match the extrinsics. |
| `extrinsics.inv_transform_rays(ray_orig, ray_dir)` | Camera-space rays to world-space rays. Dtype and device must match both ray tensors. |
| `translate`, `rotate`, `move_forward`, `move_right`, `move_up`, `cam_pos`, `cam_right`, `cam_up`, `cam_forward` | Camera motion and world-axis queries. Use tensors on the same device/dtype for tensor-valued moves. |
| `switch_backend(name)`, `backend_name`, `available_backends()` | Advanced extrinsics representation control. The built-in backends are tuned for either speed or differentiable rigid transforms. |

## Intrinsics and ray generation

| API | Contract |
|---|---|
| `PinholeIntrinsics(width, height, params, near=1e-2, far=1e2)` | Direct pinhole constructor; `params` stores `x0`, `y0`, `focal_x`, `focal_y` for each camera. |
| `PinholeIntrinsics.from_focal(width, height, focal_x, focal_y=None, x0=0, y0=0, near=..., far=..., num_cameras=1, device=None, dtype=...)` | Construct pinhole intrinsics from focal lengths in pixels. |
| `PinholeIntrinsics.from_fov(width, height, fov, fov_direction=CameraFOV.VERTICAL, x0=0, y0=0, ...)` | Construct pinhole intrinsics from field of view in radians. |
| `PinholeIntrinsics.project(vectors)` | Project camera-space vectors to homogeneous clip coordinates `(C, B, 4)`. |
| `PinholeIntrinsics.transform(vectors)` | Project camera-space vectors to NDC `(C, B, 3)` by perspective division. |
| `focal_x`, `focal_y`, `x0`, `y0`, `cx`, `cy`, `fov_x`, `fov_y`, `zoom(amount)` | Lens properties. Changing `width` or `height` keeps FOV invariant and adjusts focal length. |
| `OrthographicIntrinsics.from_frustum(width, height, fov_distance=1.0, near=..., far=..., ...)` | Orthographic camera intrinsics. `fov_distance` acts as zoom scale. |
| `generate_default_grid(width, height, device=None)` | Pixel index grid `(pixel_y, pixel_x)` with integer pixel coordinates. |
| `generate_centered_pixel_coords(width, height, device=None)` | Pixel centers for a full-resolution ray grid. |
| `generate_centered_custom_resolution_pixel_coords(img_width, img_height, res_x=None, res_y=None, device=None)` | Downsampled or custom-resolution pixel centers on the original camera image plane. |
| `generate_pinhole_rays(camera, coords_grid=None)` | Returns `(ray_origins, ray_dirs)` shaped `(H*W, 3)` for one pinhole camera. Custom grid tensors must be on `camera.device`. |
| `generate_ortho_rays(camera, coords_grid=None)` | Orthographic version with parallel directions and per-pixel origins. |
| `generate_rays(camera, coords_grid=None)` | Dispatches to pinhole or orthographic ray generation based on `camera.lens_type`. |

## Easy PBR rendering

| API | Use it for | Contract and output |
|---|---|---|
| `default_camera(resolution=512)` | Quick pinhole camera for a centered, normalized scene. | Returns a CPU camera looking from `(1, 1, 1)` toward the origin with square resolution. Move it with `.to(device)` or `.cuda()` before CUDA rendering. |
| `default_lighting()` | Quick spherical-Gaussian light. | Returns one `SgLightingParameters` instance. Move it to the camera/render device. |
| `default_material(diffuse_color=None)` | Fallback `PBRMaterial`. | Defaults to a green diffuse color and specular workflow. Useful when imported materials are absent or unsuitable. |
| `render_mesh(camera, mesh, lighting=None, custom_materials=None, custom_material_assignments=None, backend=None, nvdiffrast_context=None)` | Full easy PBR render from one `SurfaceMesh`. | Requires one camera and one mesh. `backend=None` chooses `nvdiffrast` if available, else `cuda`; explicit backends are `"nvdiffrast"` and `"cuda"`. Returns a dict of render passes; output is not clamped. |
| `RenderPass` | Stable pass names/keys. | Use `result[RenderPass.face_idx]` for face indices and `result[RenderPass.render.name]` for the composited RGB image. Other current string keys include `albedo`, `normals`, `diffuse`, `specular`, `uvs`, and `features` when available. Do not assume `alpha` or `roughness` is populated without checking the result dict. |
| `mesh_rasterize_interpolate_cuda(mesh, camera, ...)` | High-level internal rasterize/interpolate helper using bundled CUDA. | Returns `(face_idx, im_normals, im_tangents, im_uvs, im_features)`. Use only when you need more control than `render_mesh`. |
| `mesh_rasterize_interpolate_nvdiffrast(mesh, camera, context, ...)` | High-level internal helper using `nvdiffrast`. | Requires an `nvdiffrast` CUDA context. |
| `texture_sample_materials(...)` | Convert rasterized UVs/materials to albedo, specular albedo, world normals, and roughness maps. | Uses `PBRMaterial.hwc()` with `nvdiffrast` texture sampling and `PBRMaterial.chw()` with Kaolin CUDA texture mapping. |
| `sg_shade(...)` | Apply partial PBR SG diffuse/specular shading to image-space material maps. | Used by `render_mesh`; expects all inputs on one device. |

## Low-level rasterization and DIB-R

| API | Contract |
|---|---|
| `rasterize(height, width, face_vertices_z, face_vertices_image, face_features, valid_faces=None, multiplier=None, eps=None, backend='cuda')` | Fully differentiable feature rasterization. `face_vertices_z`: `(B, F, 3)`. `face_vertices_image`: `(B, F, 3, 2)` in normalized image coordinates. `face_features`: `(B, F, 3, C)` or a list of such tensors. Returns `(image_features, face_idx)`. Backends: `cuda`, `nvdiffrast`, `nvdiffrast_fwd`. |
| `dibr_soft_mask(face_vertices_image, selected_face_idx, sigmainv=7000, boxlen=0.02, knum=30, multiplier=1000.)` | DIB-R soft silhouette mask for a previously rasterized face-index map. |
| `dibr_rasterization(height, width, face_vertices_z, face_vertices_image, face_features, face_normals_z, sigmainv=7000, boxlen=0.02, knum=30, multiplier=None, eps=None, rast_backend='cuda')` | Wraps `rasterize` with visibility gating by `face_normals_z >= 0` and computes a soft mask. Returns `(interpolated_features, soft_mask, face_idx)`. |
| `nvdiffrast_is_available()` | True when optional `nvdiffrast.torch` imported successfully. |
| `default_nvdiffrast_context(device, raise_error=False)` | Get or create a cached `nvdiffrast` CUDA context for a device. With `raise_error=True`, missing `nvdiffrast` raises a clear `ValueError`. |

Backend notes:

- Low-level `cuda` rasterization uses Kaolin's compiled CUDA extension `_C`; it cannot work in CPU-only or extension-missing environments.
- `nvdiffrast` and `nvdiffrast_fwd` require the optional `nvdiffrast` package and CUDA. In tests, double precision is skipped for nvdiffrast paths.
- The low-level rasterizer notes that height and width should be multiples of 8 with the nvdiffrast CUDA context.

## Lighting APIs

| API | Contract |
|---|---|
| `SgLightingParameters(amplitude=3., direction=(1, 0., 0.), sharpness=5.)` | Encapsulates spherical Gaussian lighting. Scalars are expanded; `amplitude` becomes `(num_sg, 3)`, `direction` becomes normalized `(num_sg, 3)`, and `sharpness` becomes `(num_sg,)`. |
| `SgLightingParameters.from_sun(direction, strength=3.0, angle=pi*0.25, color=None)` | Build SG parameters approximating one or more suns. |
| `.to(device)`, `.cuda()`, `.cpu()` | Move lighting tensors. Use the same device as the camera/render tensors. |
| `sg_direction_from_azimuth_elevation(azimuth, elevation)` | Convert angles in radians to a y-up direction vector. |
| `sg_diffuse_inner_product`, `sg_warp_specular_term`, `sg_irradiance_*`, `sg_distribution_term`, `fresnel` | Low-level SG diffuse/specular/PBR pieces. Use when building custom shaders. |
| `project_onto_sh9(directions)`, `sh9_irradiance(lights, normals)`, `sh9_diffuse(directions, normals, albedo)` | Spherical-harmonic diffuse helpers. `sh9_diffuse` expects one light direction `(3,)`, normals `(N, 3)`, and albedo `(N, 3)`. |

## Material and texture APIs

| API | Contract |
|---|---|
| `PBRMaterial(...)` | Stores diffuse, roughness, metallic, clearcoat, opacity, IOR, specular, displacement, transmittance, normal, and texture attributes plus colorspace metadata. Value colors are `(3,)`; scalar values are `(1,)`; texture attributes are 3D tensors. |
| `PBRMaterial.supported_texture_attributes()` / `supported_tensor_attributes()` | Enumerate material attributes that may contain tensors. |
| `PBRMaterial.to(device)`, `.cuda()`, `.cpu()`, `.contiguous()` | Return shallow copies with tensor attributes converted. Non-tensor metadata is preserved. |
| `PBRMaterial.hwc()` / `.chw()` | Convert texture tensor layouts between HWC and CHW conventions. The easy renderer selects the appropriate layout internally per backend. |
| `PBRMaterial.get_attributes(only_tensors=False)`, `to_string(print_stats=False, detailed=False)` | Inspect present attributes and tensor summaries for diagnostics. |
| `PBRMaterial.as_dict()` / `PBRMaterial.from_dict(d)` and `Material.from_dict(d)` | Serialize/deserialize PBR materials. The dict classname is `pbr`. |
| `texture_mapping(texture_coordinates, texture_maps, mode='nearest')` | Manual texture sampling helper. UV coordinates are expected in `[0, 1]`; texture maps are `(B, C, H, W)`; output is HWC-like `(B, ..., C)`. |

Material workflow notes:

- `is_specular_workflow=True` uses specular color/texture. When it is false, the renderer uses metallic workflow and combines metallic values with albedo to compute specular albedo.
- If no materials are passed and the mesh has none, easy render uses `default_material()`.
- If material assignments are absent, all visible pixels use material index 0.
- Texture rendering needs UVs. Missing UV maps do not necessarily crash, but texture maps cannot be sampled and the output may fall back to constant material colors.
