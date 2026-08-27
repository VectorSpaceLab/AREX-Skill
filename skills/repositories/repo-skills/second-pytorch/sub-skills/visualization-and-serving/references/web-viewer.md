# Web viewer workflow reference

Read this reference when operating the browser UI, translating a browser action
to backend state, or explaining why a viewer request is not a valid detector
verification. The facts below are distilled from the Flask backend, its
JavaScript client, the HTML controls, and the public web-viewer instructions.
No source checkout file is required to use this reference.

## Deployment contract

The historical web viewer is two separate local processes:

| Process | Default | Responsibility |
|---|---:|---|
| Flask backend | `127.0.0.1:16666` | Reads dataset/checkpoint paths on the backend host and answers `/api/*` JSON requests. |
| Static frontend server | `127.0.0.1:8000` in the README example | Serves `index.html`, JavaScript, CSS, and browser-side Three.js UI. |

The backend is created as a Flask application and applies `CORS(app)`. The
frontend is not served by Flask. Use a narrow directory containing the web UI
as the static-server root; do not serve a dataset, model directory, or home
directory. The browser's `backend` setting is a URL, while `rootPath`,
`infoPath`, `detPath`, `checkpointPath`, and `configPath` are interpreted by
the backend process. Consequently, a path that exists only on the browser
machine will fail on the backend.

The HTML page uses external CDN assets for Bootstrap, jQuery, Three.js,
dat.GUI, math.js, jsPanel, and js-cookie, with some local fallback scripts.
A browser without network access must have equivalent assets available from the
frontend asset bundle; the Flask API itself does not provide those assets.

## Browser controls and ordering

The UI exposes these viewer properties and actions:

- `datasetClassName`: dataset registry name; `KittiDataset` is the normal KITTI
  value. Other registered classes must be present in the backend import graph.
- `backend`: base URL. The client prepends `http://` if the value has no
  `http://` or `https://` scheme. A trailing slash is harmless for the shown
  URL construction but avoid duplicating path components.
- `rootPath`: dataset root readable by the backend.
- `infoPath`: pickled dataset-info file readable by the backend.
- `load`: calls `/api/readinfo`; it must succeed before plotting, detection
  loading, or inference.
- `detPath` and `loadDet`: optional serialized or KITTI-format detections.
- `drawDet`: asks the browser to draw detection boxes when the response has the
  expected fields; it is not proof that `loadDet` data was attached.
- `checkpointPath`, `configPath`, `buildNet`, and `inference`: guarded legacy
  model route; load first, build second, infer third.
- `enableInt16` and `int16Factor`: default UI values are `true` and `100`.
  They control the raw point buffer encoding/decoding, not the physical dataset
  units.
- image index field, previous, and next: select an index returned by
  `/api/readinfo`. The initial displayed value is `1`, but index `1` is not
  guaranteed to exist.
- `screenshot`: saves the main Three.js canvas as a JPEG through the browser;
  it does not save backend data or a reproducible annotation file.

The UI stores most path and URL fields in browser cookies. A stale cookie can
silently override a newly typed default, so inspect the current GUI values and
clear the viewer cookies when a URL or path appears to revert.

## State machine

`SecondBackend` holds process-global mutable state: `root_path`,
`image_idxes`, `dt_annos`, `dataset`, `net`, `device`, and (after build) the
parsed config. This is a single-user, stateful viewer protocol, not a
multi-tenant serving API.

1. **Read info.** POST `/api/readinfo` with `root_path`, `info_path`, and
   `dataset_class_name`. The backend constructs the selected dataset, sets
   `image_idxes = [0, ..., len(dataset)-1]`, and returns those indexes in
   `results[0].image_indexes`. Construction can fail if the pickle, referenced
   point files, class name, or required imports are invalid.
2. **Load detections (optional).** POST `/api/read_detection` with `det_path`
   after a root has been set. If `det_path` is a file it is unpickled; otherwise
   the backend parses it using its KITTI label reader. It stores the result as
   `dt_annos` and returns a normal status. In this source revision the later
   `/api/get_pointcloud` implementation does not read `dt_annos` when composing
   its response, so do not promise that `loadDet` will draw results.
3. **Fetch a sample.** The browser calls `/api/get_pointcloud` and
   `/api/get_image` concurrently for a selected `image_idx`. The first returns
   raw point bytes and optional ground-truth boxes; the second returns a data
   URL or an empty image string. The backend source banner says it now supports
   lidar only, so image display is a legacy best-effort path rather than a
   camera-support guarantee.
4. **Build a network (optional and guarded).** POST `/api/build_network` with
   `checkpoint_path` and `config_path`. It parses the text protobuf, chooses
   CUDA when available otherwise CPU, builds the configured SECOND model,
   loads the checkpoint, replaces the backend dataset with the configured eval
   dataset, and stores `net`, `config`, and `device`.
5. **Infer a sample (optional and guarded).** POST `/api/inference_by_idx` with
   `image_idx` after a successful build. The backend prepares the selected
   example, pads the coordinate batch index, adds the anchor batch dimension,
   calls the network, and returns predicted boxes, labels, and scores.

## Visualization formats

### Browser point cloud

`get_pointcloud` returns `results[0]` with:

- `pointcloud`: base64 of a contiguous raw NumPy byte buffer containing only
  `points[:, :3]`; the backend reports `num_features: 3` even when the source
  dataset stores four features.
- `num_features`: currently `3`.
- `locs`, `dims`, `rots`, and `labels` when annotations are present. These are
  JSON lists. `locs` and `dims` are per-box arrays; `rots` is generated as
  `[0, 0, -yaw]` for each box; `labels` contains annotation names.

When `enable_int16` is true, the backend multiplies the selected XYZ array by
`int16_factor`, casts to `int16`, and base64-encodes it. The browser decodes an
`Int16Array` and divides coordinates by the same factor. When false, it decodes
`Float32Array`. A mismatched flag or factor produces a visually corrupted
cloud even if the HTTP response is successful. The client caps rendering at
`500000` points.

### Point-to-BEV helpers

The source's CPU-safe `simplevis` helpers are separate from the browser API:

- `points_to_bev(points, voxel_size, coors_range, with_reflectivity=False,
  density_norm_num=16, max_voxels=40000)` returns `[C, H, W]`. The final channel
  is a point-count map, not a normalized density map. With reflectivity, the
  preceding channel is intensity.
- `point_to_vis_bev` returns a grayscale-height map converted to RGB. Its
  default range is `[-50, -50, -3, 50, 50, 1]`; it mutates the Z voxel size to
  span the full range.
- `kitti_vis` uses range `[0, -30, -3, 64, 30, 1]` and green boxes; `nuscene_vis`
  uses `[-50, -50, -5, 50, 50, 3]` and green boxes.
- `draw_box_in_bev` expects center-format boxes with columns
  `[x, y, z, w, l, h, yaw]`. A nine-column box is treated as carrying a
  two-component velocity and receives an arrow. Labels are drawn at the
  computed stand-up-box center.

These functions require the OpenCV/Numba path and may hit the same historical
Numba/API compatibility boundary; they are useful format guidance, not a claim
that every helper is executable in a modern environment.

### Image, boxes, and screenshot

`get_image` returns `image_b64` as a browser data URL of the form
`data:image/<datatype>;base64,<bytes>` when the dataset supplies camera bytes,
or `""` otherwise. The frontend draws it into a canvas. Browser 3D boxes are
constructed from `locs`, `dims`, and `rots`; detection labels are rendered as
`score=<value>` strings. The screenshot action calls `toDataURL` on the main
WebGL canvas and downloads `pc_<image_index>.jpg`.

### `bbox_plot` formats and boundaries

The historical `bbox_plot` module provides several non-browser drawing APIs:

- `FORMAT` names `Center`, `Corner`, and `Length` representations. The default
  `draw_bbox_in_ax(..., fmt=FORMAT.Corner)` converts corner boxes through
  `corner_to_length`; supplied rotations are radians and are converted to
  degrees for Matplotlib rectangles.
- `cv2_draw_bbox_with_label` draws 2D `[x1, y1, x2, y2]` rectangles and text;
  `cv2_draw_3d_bbox` draws the twelve edges of an `[N, 8, 2]` projected box;
  `draw_2d_bbox_in_ax` can add an orientation arrow; and
  `draw_3d_bbox_in_ax`/`draw_3d_bbox_in_3dax` draw projected or 3D Matplotlib
  boxes. `GLColor` and `get_cv2_color` provide the historical color mapping.
- `draw_3d_bboxlines_in_pyqt`, `draw_bboxlines_in_pyqt`,
  `draw_3d_bbox_meshes_in_pyqt`, `GLTextItem`, and `GLLabelItem` depend on
  PyQt/pyqtgraph/OpenGL. They are desktop-only evidence and are intentionally
  not bundled or routed here.

Use [geometry-and-evaluation](../../geometry-and-evaluation/SKILL.md) for
coordinate-frame and box-convention decisions. These APIs use box shapes and
axis conventions; they do not repair a mismatched KITTI camera/lidar frame.
