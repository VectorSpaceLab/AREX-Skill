# Output Formats

This sub-skill covers the geometry and render artifacts emitted by the Python pipeline and the Obama dense-render helper.

## Core geometry outputs

| Artifact | Typical name | Shape / type | Writer | Important convention |
| --- | --- | --- | --- | --- |
| Sparse landmarks | `*_0.txt` | `(3, 68)` float values | `np.savetxt` in `main.py` | These are image-space 3D landmarks, not 2D-only points. |
| Dense vertices | `*_0.mat` | `vertex` key with `(3, 53215)` float values | `dump_vertex` / `sio.savemat` | Dense vertices follow the same image-space convention as sparse landmarks. |
| PLY mesh | `*_0.ply` | ASCII PLY | `dump_to_ply` | Faces are written zero-based in the file. |
| Colored OBJ | `*_0.obj` | OBJ with vertex colors | `write_obj_with_colors` | Vertex positions are written as `(y, x, z)` and colors are emitted as RGB. |
| Pose visualization | `*_pose.jpg` | Image | `plot_pose_box` | Draws the camera/pose box over the original image. |
| Depth image | `*_depth.png` | Grayscale image | `cget_depths_image` | Rendered at 0–255 intensity after depth normalization. |
| PNCC image | `*_pncc.png` | 3-channel image | `cpncc` | Saved with channel reversal before `cv2.imwrite`. |
| PAF image | `*_paf.jpg` plus `*_crop.jpg` | 3-channel image pair | `gen_img_paf` | `*_crop.jpg` is the resized 120×120 face crop used to build the PAF. |
| Landmarks visualization | `*_3DDFA.jpg` | Image | `draw_landmarks` | This is the standard 68-landmark overlay. |

## Dense render helper outputs

| Artifact | Typical name | Source |
| --- | --- | --- |
| Dense render frames | `obama_res@dense_py/*.jpg` | `demo@obama/rendering.py` |
| Dense render video | `obama_res@dense_py.mp4` | `scripts/images_to_video.py` |

## Triangle and mesh conventions

- `visualize/tri.mat` is the canonical triangle matrix used by the main Python pipeline.
- The matrix is 1-based on disk and has shape `(3, 105840)` with values spanning the 68-landmark mesh and the dense 53,215-vertex mesh.
- For Cython depth/PNCC rendering, the pipeline passes `tri - 1` because the rasterizer expects zero-based indices.
- For OBJ writing, keep the triangle indices 1-based.
- For PLY writing, the helper subtracts 1 when writing face indices.

## Main pipeline name pattern

The default `main.py` flow emits one numbered file per detected face, using the face index suffix:

- `image_0.ply`, `image_0.obj`, `image_0.txt`, `image_0.mat`
- `image_pose.jpg`, `image_depth.png`, `image_pncc.png`, `image_paf.jpg`

This helps distinguish multiple detections on the same source image.
