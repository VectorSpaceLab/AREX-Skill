# Viewer troubleshooting

Use this page for diagnosis before changing dependencies, paths, or API order.
The web viewer is a legacy, stateful local application. Do not turn a
troubleshooting attempt into a server exposure, dataset rewrite, checkpoint
conversion, or detector verification.

## Install and import failures

### `ModuleNotFoundError: flask`, `flask_cors`, `skimage`, or `fire`

**Symptom:** the dependency checker reports a missing component, or the backend
fails before its CLI help appears.

**Cause:** the web backend imports Flask, Flask-CORS, scikit-image, and Fire at
module import time. The historical checkout has no setup metadata, so there is
no reliable package-level install command to infer.

**Recovery:** run the bundled probe again with `--json`; install only the
missing, user-approved web dependency in the caller-managed environment, then
repeat the import/help diagnostic. Do not launch a service while imports are
being repaired. The frontend's CDN libraries are a separate browser concern.

### `ModuleNotFoundError` or missing symbols from `second`

**Symptom:** `python -m second.kittiviewer.backend.main --help` fails while
loading model or data modules.

**Cause:** the backend imports detector builders at top level, so even info-only
viewer use can encounter detector dependencies. A working Flask import is not
enough.

**Recovery:** inspect the checker output and route model compatibility to
[training-and-inference](../../training-and-inference/SKILL.md). Do not copy
modern model code into this historical viewer or silently downgrade the
verification claim.

### Modern spconv appears installed but legacy names are absent

**Symptom:** the checker reports `spconv` or modern convolution classes but
fails `spconv.utils.VoxelGeneratorV2` or
`spconv.utils.non_max_suppression`; `buildNet` fails during import/build.

**Cause:** this repository's model path uses legacy spconv and Numba APIs.
Current spconv 2.x is not proven compatible with the source. A CUDA smoke test
or a successful `import torch` does not establish compatibility.

**Recovery:** keep the web data/static route separate from checkpoint inference.
Use a deliberately prepared legacy-compatible environment only if the user
accepts that effort and rerun targeted checks. Until then, document the
checkpoint route as blocked/unverified. Do not claim the A100/CUDA path, modern
spconv, or a successful dependency probe verifies detector execution.

### Optional desktop imports fail

**Symptom:** `PyQt5`, `pyqtgraph`, `OpenGL`, or Qt Matplotlib imports are absent.

**Cause:** those belong to the deprecated desktop viewer and its helpers, not
the supported web route.

**Recovery:** do not install or launch the desktop application merely to fix a
web request. Use the web protocol. Recommend OpenPCDet or MMDetection3D for
new work.

## Frontend, URL, CORS, and service failures

### Browser says network error, connection refused, or `ERR_CONNECTION_REFUSED`

Check independently:

1. The backend process is actually running on the requested port.
2. The browser's `backend` field is the full URL, for example
   `http://127.0.0.1:<BACKEND_PORT>`.
3. The frontend is served over HTTP, not opened as an arbitrary `file://` URL.
4. The static server is serving the directory containing `index.html` and its
   JavaScript/CSS assets.

The source backend binds to loopback. A browser on another host cannot reach
that address; use a user-controlled local browser or a secure, explicit port
forward. Do not change the bind address as an unreviewed troubleshooting step.

### CORS error despite both processes running

The frontend and backend normally have different origins (for example ports
`8000` and `16666`). The backend calls `CORS(app)`, and each shown JSON route
also adds an allow-headers response header. If the response lacks the CORS
header, verify that the request reached the intended historical backend rather
than another service or proxy. If the browser sends an `OPTIONS` failure,
inspect the proxy and origin before changing application code. CORS does not
provide authentication or remote reachability.

### UI silently uses an old URL or path

The page persists most viewer fields in cookies. Read the actual dat.GUI
values, overwrite them, or clear the viewer's cookies. Do not rely on the
placeholder values from a prior session.

### CDN scripts or WebGL are unavailable

**Symptom:** a blank page, `THREE is not defined`, missing GUI controls, or
WebGL context errors.

**Recovery:** inspect browser console/network errors and make equivalent
frontend assets available locally; use a browser with WebGL enabled. The
backend cannot repair missing CDN JavaScript. Keep static serving scoped to the
frontend assets and do not use the viewer as a reason to expose model/data
folders.

## Dataset and info validation

### `/api/readinfo` returns an error or the backend crashes

Confirm all three values and their ownership:

- `dataset_class_name` exactly matches a registered class, normally
  `KittiDataset`.
- `info_path` is a readable pickle generated for this dataset revision.
- `root_path` is the dataset root visible to the backend, and each relative
  point/image path in the info entries resolves beneath the intended root.

The handler constructs the dataset immediately but may not read every referenced
point file until a sample is requested. A normal `image_indexes` response is
therefore not proof that every file is present. Use the data-preparation route
for KITTI layout and info checks.

### `get_pointcloud` reports missing root, invalid index, or bad bytes

- Missing root means `readinfo` did not complete in this process.
- The accepted `image_idx` is a zero-based ordinal from `image_indexes`, not
  necessarily a KITTI filename such as `000123`.
- The request must include `enable_int16`; include `int16_factor` when true.
- Decode as `Int16Array` only when enabled and divide by the same factor. With
  the flag disabled, decode as `Float32Array`. The response has XYZ only.
- A corrupted or absent `velodyne` file is a dataset problem, not a browser
  rendering problem.

### Image panel is blank but point cloud works

`get_image` may return an empty `image_b64`, and the backend explicitly says
camera support is no longer supported. Check the response before treating this
as a CORS failure. The web viewer's supported core is lidar; route camera/data
layout questions to data preparation.

## Detection and API misuse

### `loadDet` succeeds but no detection boxes appear

The endpoint returns only `status: normal` after loading a pickle or KITTI label
directory into `BACKEND.dt_annos`. The current point-cloud handler does not
consistently incorporate that stored state, while the browser expects
`dt_*` fields when `drawDet` is set. Inspect the actual JSON response. Do not
rewrite the API or claim detection visualization is verified; use checkpoint
inference only through its separate guarded route.

Only unpickle detection files that the user trusts. Python pickle loading is
not a safe operation on untrusted input.

### `status: error` is present but HTTP status looks successful

The source error helper returns a plain dictionary with a status and message;
it does not set an HTTP error code. Always parse JSON and check `status`, not
just `curl`'s HTTP exit behavior. Examples include `root path is not set`,
`config file not exist.`, and `ckpt file not exist.`.

### Direct request returns a 500 or an unhandled traceback

Check method, `Content-Type: application/json`, required key spelling, and
state order. The handlers do not normalize malformed JSON, missing keys,
unknown dataset classes, out-of-range indexes, missing network state, text
protobuf parse errors, or model exceptions. Repeat first with the browser's
known request shape from [api-reference](api-reference.md), then reduce to a
small trusted path/input fixture.

## Checkpoint/config and inference failures

### `buildNet` rejects a path

The backend checks `Path(config_path).exists()` and
`Path(checkpoint_path).exists()` before parsing. A normal response only means
those checks and the subsequent build returned; it does not validate the
checkpoint's architecture or backend. Ensure the text config matches the
checkpoint's `model.second` definition and that its eval dataset paths are
usable by the backend.

### Text protobuf parse or state-dict mismatch

The config is parsed as text into `TrainEvalPipelineConfig`, not arbitrary YAML
or JSON. A checkpoint must contain the state expected by the model built from
that config. Route schema/config questions to training-and-inference and do not
repair a mismatch by deleting fields or loading with an unsafe permissive mode.

### Inference is called before build, or with a different dataset state

The intended order is `readinfo -> build_network -> inference_by_idx`. The
backend stores all state globally and `build_network` replaces `BACKEND.dataset`
with the eval dataset constructed from the config. If another request changed
state, reload info and rebuild in one controlled session. `inference_by_idx`
expects an ordinal and a populated `net`/`device`; it does not use the client's
`remove_outside` value in this revision.

### Legacy Numba/CUDA errors

The README records old `NUMBAPRO_*` CUDA environment variables for the
historical Numba path. Those variables may be relevant to an old environment,
but setting them cannot add missing spconv symbols and is not detector
verification. Preserve the compatibility block, collect the exact import or
kernel error, and stop rather than repeatedly starting the service.

## Visualization limits and desktop deprecation

- The browser client allocates room for up to `500000` points; a larger cloud
  is truncated for rendering, not for source data.
- `simplevis` BEV outputs are arrays/images with explicit XYZ ranges and
  channel semantics; they are not interchangeable with the browser's base64
  XYZ stream. Use [web-viewer.md](web-viewer.md) and
  [geometry-and-evaluation](../../geometry-and-evaluation/SKILL.md) before
  changing box order, yaw sign, or axis conventions.
- `viewer.py`, `glwidget.py`, and `control_panel.py` are deprecated Qt/OpenGL
  evidence. Do not install their GUI stack or use their startup command as a
  fallback for a web failure. For maintained new projects, use the README's
  recommended OpenPCDet or MMDetection3D successors.
