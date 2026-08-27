# Web viewer API reference

Read this before making direct requests or interpreting browser failures. All
routes are `POST` routes under the configured backend base URL and expect a
JSON request body. Successful route bodies are shaped as
`{"results": [<object>]}`. The backend's small `error_response` helper returns
an object with `status: "error"` and a `[ERROR]...` message; it does not set a
separate error HTTP status. Missing JSON keys, invalid indexes, unhandled
imports, and most file/parser exceptions can instead become ordinary server
errors.

## Endpoint table

| Endpoint | Required JSON keys | State prerequisite | Normal `results[0]` |
|---|---|---|---|
| `/api/readinfo` | `root_path`, `info_path`, `dataset_class_name` | none | `status: "normal"`, `image_indexes` |
| `/api/read_detection` | `det_path` | `readinfo` or any prior root state | `status: "normal"` |
| `/api/get_pointcloud` | `image_idx`, `enable_int16`; `int16_factor` if enabled | successful `readinfo` | `status: "normal"`, `pointcloud`, `num_features`, optional GT fields |
| `/api/get_image` | `image_idx` | successful `readinfo` | `status: "normal"`, `image_b64` |
| `/api/build_network` | `checkpoint_path`, `config_path` | successful `readinfo` | `status: "normal"` |
| `/api/inference_by_idx` | `image_idx` | successful `readinfo` and `build_network` | `status: "normal"`, `dt_*` prediction fields |

The source client also sends `with_det` and `remove_outside` to
`get_pointcloud` and `remove_outside` to `inference_by_idx`. The current Flask
handlers do not consume those keys. Do not infer filtering or detection
fusion from their presence.

## Read dataset info

```bash
curl -sS -X POST "http://127.0.0.1:<BACKEND_PORT>/api/readinfo" \
  -H 'Content-Type: application/json' \
  --data '{"root_path":"<DATASET_ROOT>","info_path":"<INFO_PKL>","dataset_class_name":"KittiDataset"}'
```

The handler constructs the registered dataset class with `root_path` and
`info_path`, then sets process-global `BACKEND.root_path`, `BACKEND.dataset`,
and `BACKEND.image_idxes`. The returned indexes are `list(range(len(dataset)))`:
they are zero-based dataset ordinals, not necessarily the original KITTI file
stem or `metadata.image_idx`. Use an index from the response when requesting a
sample.

Expected normal body (schematic):

```json
{"results":[{"status":"normal","image_indexes":[0,1,2]}]}
```

`KittiDataset` expects a readable pickle whose entries refer to point-cloud
paths under the supplied root. The dataset constructor prints its remaining
info count to the backend process log; that print is not part of the JSON
contract.

## Load detections

```bash
curl -sS -X POST "http://127.0.0.1:<BACKEND_PORT>/api/read_detection" \
  -H 'Content-Type: application/json' \
  --data '{"det_path":"<DETECTION_FILE_OR_KITTI_LABEL_DIR>"}'
```

If `det_path` is a regular file, the handler uses binary `pickle.load`; for a
non-file path it calls the historical KITTI label reader. It stores the result
in process-global `BACKEND.dt_annos`. A normal response does not contain the
loaded annotations. In this revision, `get_pointcloud` reads ground truth from
the dataset sensor record and does not visibly merge `BACKEND.dt_annos`; the
browser's `drawDet` flag therefore cannot be treated as a reliable detection
load assertion.

Before the root is set, the body is approximately:

```json
{"status":"error","message":"[ERROR]root path is not set"}
```

## Get point cloud

```bash
curl -sS -X POST "http://127.0.0.1:<BACKEND_PORT>/api/get_pointcloud" \
  -H 'Content-Type: application/json' \
  --data '{"image_idx":0,"enable_int16":true,"int16_factor":100}'
```

The handler retrieves `dataset.get_sensor_data(ordinal)`, where `ordinal` is
the position of `image_idx` in `BACKEND.image_idxes`. It takes only XYZ from
the returned point array and reports three features. The point bytes are
base64-encoded raw NumPy bytes, with no header, shape, or dtype marker.

- With `enable_int16: true`, bytes are `int16` after multiplication by
  `int16_factor`. The browser divides decoded values by the same factor.
- With `enable_int16: false`, bytes are `float32`.
- `num_features` is `3`; calculate `len(decoded_values) // 3`.
- If the sensor annotation has boxes, fields are `locs`, `dims`, `rots`, and
  `labels`. The backend builds `rots` as three-element arrays with the final
  value equal to negative source yaw.

Schematic normal body:

```json
{
  "results": [{
    "status": "normal",
    "num_features": 3,
    "pointcloud": "<base64 raw XYZ bytes>",
    "locs": [["x","y","z"]],
    "dims": [["w","l","h"]],
    "rots": [[0,0,"-yaw"]],
    "labels": ["Car"]
  }]
}
```

The placeholder strings above stand for numeric JSON values. A missing root
returns the explicit error object. A missing/out-of-range ordinal, malformed
body, or dataset I/O failure is not normalized by the handler.

## Get image

```bash
curl -sS -X POST "http://127.0.0.1:<BACKEND_PORT>/api/get_image" \
  -H 'Content-Type: application/json' \
  --data '{"image_idx":0}'
```

The handler requests lidar plus camera data from the dataset. If camera bytes
are present, it returns a browser data URL:

```json
{"results":[{"status":"normal","image_b64":"data:image/png;base64,<...>"}]}
```

If no camera data is supplied, `image_b64` is `""`. The backend module's
header states that it now supports lidar only and camera is no longer
supported; treat this endpoint as a compatibility path, not a promise of
camera operation.

## Build a network

```bash
curl -sS -X POST "http://127.0.0.1:<BACKEND_PORT>/api/build_network" \
  -H 'Content-Type: application/json' \
  --data '{"config_path":"<PIPELINE_CONFIG>","checkpoint_path":"<CHECKPOINT>"}'
```

The handler requires a root state, verifies both paths with `Path.exists()`,
parses text protobuf into `TrainEvalPipelineConfig`, and builds
`config.model.second`. It selects `cuda` if `torch.cuda.is_available()` and
otherwise `cpu`, calls the historical `build_network`, loads the checkpoint
state, and rebuilds the eval dataset using the network's voxel generator and
target assigner. It stores `net`, `config`, and `device` globally.

Explicit error bodies for the two path checks are approximately:

```json
{"status":"error","message":"[ERROR]config file not exist."}
{"status":"error","message":"[ERROR]ckpt file not exist."}
```

A normal body only says `status: "normal"`; it does not report the device,
model class, or checkpoint compatibility. Parse errors, state-dict mismatch,
legacy spconv symbols, CUDA issues, and dataset construction failures may
escape as server exceptions. Follow the guarded route in
[visualization-and-serving](../SKILL.md) and hand compatibility work to
[training-and-inference](../../training-and-inference/SKILL.md).

## Inference by index

```bash
curl -sS -X POST "http://127.0.0.1:<BACKEND_PORT>/api/inference_by_idx" \
  -H 'Content-Type: application/json' \
  --data '{"image_idx":0}'
```

The handler obtains `dataset[ordinal]`, pads a leading batch coordinate column,
adds a batch dimension to anchors, converts the example to the selected
`device`, and calls `BACKEND.net`. It returns:

```json
{
  "results": [{
    "status": "normal",
    "dt_locs": [["x","y","z"]],
    "dt_dims": [["w","l","h"]],
    "dt_rots": [[0,0,"-yaw"]],
    "dt_labels": [0],
    "dt_scores": [0.9]
  }]
}
```

The values are schematic numeric lists. The browser labels boxes using
`dt_scores`; `dt_labels` is still returned. Without a built network,
`BACKEND.net` or `BACKEND.device` is unset and the call is not a valid
workflow. No detector execution has been accepted as verified for this
repository snapshot.

## Direct-request diagnostic order

Use this sequence against a user-started service, without starting one from a
check or test:

1. `readinfo` and inspect `results[0].image_indexes`.
2. `get_pointcloud` with a returned ordinal and matching binary dtype settings.
3. `get_image` only if camera display is needed.
4. `read_detection` and inspect only its status; do not assume fusion.
5. `build_network` only after the compatibility gate and explicit user request.
6. `inference_by_idx` only after a normal build response.

Always inspect both the HTTP status and the JSON `status` field. A JSON
`status: "error"` can be returned with an otherwise successful HTTP response.
