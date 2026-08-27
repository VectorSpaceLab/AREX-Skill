# API Reference

This sub-skill centers on the public geometry helpers in `utils/` and the render/feature helpers that sit on top of them.

## Reconstruction and ROI conversion

| API | Input | Output | Notes |
| --- | --- | --- | --- |
| `utils.ddfa.reconstruct_vertex(param, whitening=True, dense=False, transform=True)` | A 12-D pose block or a 62-D parameter vector. | Sparse vertices as `(3, 68)` or dense vertices as `(3, 53215)`. | If the input length is 12, the helper pads zeros to 62 values first. With `whitening=True`, it re-applies `param_mean` and `param_std` from `train.configs/param_whitening.pkl`. `transform=True` flips the y axis into image coordinates. |
| `utils.inference.parse_roi_box_from_landmark(pts)` | Landmark matrix with x/y rows. | `[sx, sy, ex, ey]` ROI box. | Builds a square ROI from landmark extent. |
| `utils.inference.parse_roi_box_from_bbox(bbox)` | `[left, top, right, bottom]`. | `[sx, sy, ex, ey]` ROI box. | Expands the face box to the standard 3DDFA crop. |
| `utils.inference.crop_img(img, roi_box)` | Image plus ROI box. | Cropped image. | Pads outside-image regions with zeros instead of failing. |
| `utils.inference.predict_68pts(param, roi_box)` | Model output plus ROI. | `(3, 68)` landmarks in original-image coordinates. | Uses the 120×120 crop convention and then rescales x/y back to the ROI. |
| `utils.inference.predict_dense(param, roi_box)` | Model output plus ROI. | `(3, 53215)` dense vertices in original-image coordinates. | z is scaled by the mean of the x/y ROI scales. |

## Serialization and color sampling

| API | Output | Notes |
| --- | --- | --- |
| `utils.inference.dump_to_ply(vertex, tri, wfp)` | ASCII PLY file. | Writes vertices first and then faces. The face indices are written zero-based, so the in-memory triangle matrix is decremented when needed for this format. |
| `utils.inference.dump_vertex(vertex, wfp)` | `.mat` file with a `vertex` key. | Used by the AFLW/Obama demos to save the dense mesh. |
| `utils.inference.get_colors(image, vertices)` | Per-vertex sampled colors. | Samples from the original RGB/BGR image using rounded projected coordinates. |
| `utils.inference.write_obj_with_colors(obj_name, vertices, triangles, colors)` | OBJ with per-vertex colors. | Writes `v` lines in `(y, x, z)` order and emits vertex colors as RGB. Keep `triangles` 1-based for OBJ face lines. |

## Pose

| API | Output | Notes |
| --- | --- | --- |
| `utils.estimate_pose.parse_pose(param)` | `(P, pose)` | `P` is the 3×4 affine camera matrix without scale; `pose` is `(yaw, pitch, roll)` in radians. |
| `utils.estimate_pose.P2sRt(P)` | `(s, R, t3d)` | Decomposes the camera block into scale, rotation, and translation. |
| `utils.estimate_pose.matrix2angle(R)` | Euler angles | Converts the rotation matrix into yaw/pitch/roll. |

## Render and feature helpers

| API | Output | Notes |
| --- | --- | --- |
| `utils.render.render_colors(vertices, colors, tri, h, w, c=3)` | Python z-buffer render. | Slow reference implementation. |
| `utils.render.crender_colors(vertices, triangles, colors, h, w, c=3, BG=None)` | Cython-backed render. | Operational path used by dense rendering. Requires contiguous arrays and the compiled extension. |
| `utils.render.get_depths_image(img, vertices_lst, tri)` | Depth map. | Python version of the depth renderer. |
| `utils.render.cget_depths_image(img, vertices_lst, tri)` | Depth map. | Accelerated depth renderer. |
| `utils.render.cpncc(img, vertices_lst, tri)` | PNCC image. | Accelerated PNCC renderer using the canonical PNCC code array. |
| `utils.render.cpncc_v2(img, vertices_lst, tri)` | PNCC image. | Normalizes vertex coordinates before rasterization. |
| `utils.paf.reconstruct_paf_anchor(param, whitening=True)` | `(2, n)` anchor coordinates. | Builds the PAF anchor from the simplified face basis. |
| `utils.paf.gen_img_paf(img_crop, param, kernel_size=3)` | PAF image. | Expects a 120×120 crop and a 62-D parameter vector. |
| `utils.lighting.RenderPipeline(**cfg)(vertices, triangles, background)` | Lit dense render. | Computes normals through the Cython extension, applies ambient/directional/specular lighting, and rasterizes the mesh. |

## Coordinate and index conventions

- Reconstructed geometry is returned in image-space coordinates after the internal y-axis flip.
- `predict_68pts` and `predict_dense` rescale x/y from the 120×120 crop back to the original image ROI.
- `visualize/tri.mat` stores 1-based triangle indices on disk; subtract 1 only for the Cython render helpers that expect zero-based indexing.
- `main.py` uses the same geometry helpers for PLY, OBJ, pose, depth, PNCC, and PAF outputs, so one param vector can drive all of them.
