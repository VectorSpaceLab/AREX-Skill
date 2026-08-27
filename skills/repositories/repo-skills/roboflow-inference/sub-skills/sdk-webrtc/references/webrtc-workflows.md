# Workflow and WebRTC patterns

This reference collects the common patterns for workflow vs model_id selection,
source choice, and session handling.

## Start with the right route

| Need | Use | Why |
| --- | --- | --- |
| Multi-step workflow, hosted workflow id, or inline workflow spec | `workflow=` | You already have a workflow graph or need one. |
| One supported model streamed per frame | `model_id=` | You want the SDK to build a minimal model workflow and hand you raw predictions. |
| VLM or custom multi-block flow | `workflow=` | There is no generic model block for every VLM family. |
| A workflow ID string without a workspace | `workflow=` dict spec | String IDs require `workspace=`. |

### Workflow mode

```python
session = client.webrtc.stream(
    source=WebcamSource(resolution=(1280, 720)),
    workflow="clip-frames",
    workspace="roboflow-docs",
    image_input="image",
    config=StreamConfig(
        stream_output=["annotated_image"],
        data_output=["predictions"],
    ),
)
```

Use workflow mode when you already know the workflow id or when you want to pass
an inline workflow specification. If the workflow is a string ID, pass
`workspace=` too. If the workflow is a dict, the workspace is not required.

### Model-id mode

```python
session = client.webrtc.stream(
    source=WebcamSource(),
    model_id="rfdetr-nano",
    task_type="object-detection",
)
```

In `model_id` mode:

- `task_type` is optional. If omitted, the SDK resolves it through the Roboflow
  model registry.
- Supported task types are `object-detection`, `instance-segmentation`,
  `classification`, `multi-label-classification`, `keypoint-detection`, and
  `semantic-segmentation`.
- The `data` argument in `on_frame` is the raw serialized predictions dict from
  the server. It is not normalized into a higher-level object.
- `None` means the frame had no predictions for that turn or could not be paired.
- VLMs are not supported in `model_id` mode; use `workflow=` instead.

The bundled model-id path fills empty `StreamConfig` outputs with
`stream_output=['image']` and `data_output=['predictions']`.

### Source selection guide

| Source | Use when | Notable behavior |
| --- | --- | --- |
| `WebcamSource` | You want a live local webcam feed. | Captures with OpenCV, can auto-detect FPS, and sends frames to the server. |
| `VideoFileSource` | You want to replay recorded footage. | Can upload a local file or downloadable URL, and can receive frames via data channel or video track. |
| `RTSPSource` | The server can reach the RTSP stream directly. | Adds a receive-only transceiver and passes `rtsp_url` to the server. |
| `MJPEGSource` | The server can reach an MJPEG HTTP(S) stream directly. | Adds a receive-only transceiver and passes `mjpeg_url` to the server. |
| `LocalStreamSource` | The stream is only reachable from the client machine. | Captures RTSP/RTMP locally through `MediaPlayer`. |
| `ManualSource` | Frames are generated programmatically. | Call `send(frame)` and the oldest queued frame is dropped when full. |

The bundled example scripts are:

- [`scripts/webcam_basic.py`](../scripts/webcam_basic.py)
- [`scripts/video_file_basic.py`](../scripts/video_file_basic.py)

Both support `--help` and `--dry-run` so future agents can inspect them without
opening a camera or contacting a server.

## Session lifecycle patterns

### Callback style

```python
with client.webrtc.stream(source=source, workflow=workflow, workspace="ws") as session:
    @session.on_frame
    def handle_frame(frame, metadata):
        ...

    @session.on_data()
    def handle_data(data, metadata):
        ...

    @session.on_error
    def handle_errors(errors, metadata):
        ...

    session.run()
```

### Iterator style

```python
with client.webrtc.stream(source=source, workflow=workflow, workspace="ws") as session:
    for frame, metadata in session.video():
        ...
```

In model mode, `session.video()` yields `(frame, data)` instead of `(frame,
metadata)`. If you need both data and metadata, use a 3-argument `on_frame`
handler.

### Manual source pattern

```python
source = ManualSource()
with client.webrtc.stream(source=source, workflow=workflow, workspace="ws") as session:
    source.send(frame)
    session.wait(timeout=30)
```

### Video-file pattern

- `VideoFileSource(..., on_upload_progress=...)` reports upload progress as
  `(uploaded_chunks, total_chunks)`.
- `realtime_processing=False` is the batch-style default.
- `use_cache=False` downloads a URL source to a temporary file that is removed at
  cleanup time.
- `use_datachannel_frames=True` merges workflow `stream_output` names into the
  `data_output` route so frames are delivered through the data channel.

### TURN and serverless notes

- `StreamConfig.turn_server` wins over any auto-fetched TURN configuration.
- `requested_plan`, `requested_region`, and `processing_timeout` are only used for
  serverless connections.
- If the server returns a 404 for `/initialise_webrtc_worker`, the API URL likely
  does not support WebRTC or points at the wrong Roboflow host.
