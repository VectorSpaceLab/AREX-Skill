# API reference

Use this reference when you need the public runtime surface without reopening
source files.

Verified against `inference_sdk/http/client.py`, `inference_sdk/http/entities.py`,
`inference_sdk/http/errors.py`, `inference_sdk/config.py`,
`inference_sdk/webrtc/client.py`, `inference_sdk/webrtc/config.py`,
`inference_sdk/webrtc/session.py`, `inference_sdk/webrtc/sources.py`,
`inference_sdk/webrtc/model_workflows.py`, and `tests/inference_sdk/**`.

## HTTP client surface

### Construction and mode

- `InferenceHTTPClient.init(api_url: str, api_key: Optional[str] = None) -> InferenceHTTPClient`
- `InferenceHTTPClient(api_url: str, api_key: Optional[str] = None)`
- Properties: `inference_configuration`, `client_mode`, `selected_model`, `webrtc`
- Mode rule: Roboflow-hosted URLs in `ALL_ROBOFLOW_API_URLS` default to `V0`;
  all other URLs default to `V1`.
- Mode overrides: `select_api_v0()`, `select_api_v1()`, `use_api_v0()`,
  `use_api_v1()`.
- Configuration helpers: `use_configuration(...)` and `configure(...)`.
- Model selection helpers: `select_model(...)` and `use_model(...)`.

### Core HTTP methods

| Method | Signature summary | Notes |
| --- | --- | --- |
| `infer` / `infer_async` | `(..., model_id=None)` | Dispatch to v0 or v1 based on client mode. |
| `infer_from_api_v0` / `infer_from_api_v0_async` | `(..., model_id=None)` | Low-level v0 path for image inference. |
| `infer_from_api_v1` / `infer_from_api_v1_async` | `(..., model_id=None)` | Low-level v1 path for supported task types. |
| `infer_on_stream` | `(input_uri, model_id=None)` | Iterates over a local stream or directory and calls `infer`. |
| `infer_from_workflow` | `(workspace_name=None, workflow_name=None, specification=None, images=None, parameters=None, excluded_fields=None, use_cache=True, enable_profiling=False, workflow_version_id=None, disable_sinks=False)` | Legacy workflow name is `workflow_name`. |
| `run_workflow` | `(workspace_name=None, workflow_id=None, specification=None, images=None, parameters=None, excluded_fields=None, use_cache=True, enable_profiling=False, workflow_version_id=None, disable_sinks=False)` | Preferred workflow name is `workflow_id`. |
| `start_inference_pipeline_with_workflow` | `(video_reference, workflow_specification=None, workspace_name=None, workflow_id=None, image_input_name='image', workflows_parameters=None, workflows_thread_pool_workers=4, cancel_thread_pool_tasks_on_exit=True, video_metadata_input_name='video_metadata', max_fps=None, source_buffer_filling_strategy='DROP_OLDEST', source_buffer_consumption_strategy='EAGER', video_source_properties=None, batch_collection_timeout=None, results_buffer_size=64)` | Starts a long-running video pipeline. |
| `list_inference_pipelines` / `get_inference_pipeline_status` / `pause_inference_pipeline` / `resume_inference_pipeline` / `terminate_inference_pipeline` / `consume_inference_pipeline_result` | pipeline lifecycle helpers | These are experimental video-pipeline calls. |
| `get_server_info` | `()` | Basic server info and health. |

Server-side model registry helpers remain on the same client: `get_model_description`,
`list_loaded_models`, `load_model`, `unload_model`, `unload_all_models`, and their
async counterparts. They are useful for server-side model administration, but they do
not replace backend/package negotiation, which belongs in `model-runtime`.

### InferenceConfiguration

`InferenceConfiguration.init_default()` returns the default dataclass. Use
`configure(...)` or `use_configuration(...)` to apply it.

| Group | Fields |
| --- | --- |
| Request shaping | `confidence_threshold`, `keypoint_confidence_threshold`, `format`, `mask_decode_mode`, `tradeoff_factor`, `max_candidates`, `max_detections`, `iou_threshold`, `stroke_width`, `count_inference`, `response_mask_format` |
| Pre/post-processing | `disable_preproc_auto_orientation`, `disable_preproc_contrast`, `disable_preproc_grayscale`, `disable_preproc_static_crop`, `class_agnostic_nms`, `class_filter`, `fix_batch_size`, `visualize_predictions`, `visualize_labels`, `output_visualisation_format`, `image_extensions_for_directory_scan`, `client_downsizing_disabled`, `default_max_input_size` |
| Workflow/pipeline/runtime | `service_secret`, `disable_active_learning`, `active_learning_target_dataset`, `source`, `source_info`, `max_concurrent_requests`, `max_batch_size`, `profiling_directory`, `workflow_run_retries_enabled` |

Conversion helpers:

- `to_api_call_parameters(client_mode, task_type)`
- `to_api_v1_query_parameters()`
- `to_object_detection_parameters()`
- `to_keypoints_detection_parameters()`
- `to_instance_segmentation_parameters()`
- `to_classification_parameters()`
- `to_legacy_call_parameters()`

### HTTP error mapping

| Error | Meaning | Typical recovery |
| --- | --- | --- |
| `HTTPCallErrorError` | The server returned an HTTP error response. | Check `status_code` and `api_message`. |
| `HTTPClientError` | Connection failure or retry exhaustion. | Check URL, server availability, and network. |
| `InvalidParameterError` | Invalid argument value or combination. | Fix the call signature or choose the right mode. |
| `WrongClientModeError` | A v1-only call was made while the client is in v0 mode, or vice versa. | Switch with `select_api_v0()` / `select_api_v1()` or use the right URL. |
| `APIKeyNotProvided` | The call needs an API key. | Pass `api_key` explicitly. |
| `ModelNotSelectedError` | Model inference needs a selected model. | Pass `model_id` or call `select_model(...)`. |
| `InvalidModelIdentifier` | The model id format is invalid. | Use the expected `project/version` form or the supported alias. |
| `ModelTaskTypeNotSupportedError` | The requested task is not supported by the path. | Choose a supported task or use `workflow=` instead. |
| `FeatureDeprecatedError` | A removed SDK helper was invoked. | Use the replacement named in the message. |

`wrap_errors(...)` and `wrap_errors_async(...)` convert requests/aiohttp errors
into the public error classes above. For `HTTPCallErrorError`, `description`,
`status_code`, and `api_message` are preserved.

## WebRTC surface

### StreamConfig

`StreamConfig` is a dataclass with these fields:

- `stream_output`
- `data_output`
- `realtime_processing`
- `declared_fps`
- `turn_server`
- `workflow_parameters`
- `requested_plan`
- `requested_region`
- `processing_timeout`

Notes:

- `turn_server` overrides auto-fetched TURN config.
- `requested_plan`, `requested_region`, and `processing_timeout` apply to serverless
  connections.
- `workflow_parameters` is merged into the workflow configuration payload.

### WebRTCClient

- `WebRTCClient(api_url: str, api_key: Optional[str])`
- `stream(source, *, workflow=None, model_id=None, task_type=None, image_input='image', workspace=None, config=None) -> WebRTCSession`

`stream(...)` rules:

- Exactly one of `workflow` or `model_id` must be provided.
- `task_type` is only valid with `model_id`.
- If `workflow` is a string ID, `workspace` is required.
- If `workflow` is a dict spec, `workspace` is optional.
- `model_id` mode auto-builds a minimal single-model workflow and delivers the raw
  serialized predictions dict to frame handlers.
- VLMs are not supported in `model_id` mode; use a full `workflow=` instead.

### Model-id helpers

- `resolve_task_type(model_id, task_type, api_key) -> str`
- `build_model_workflow(model_id, task_type) -> dict`
- `apply_model_id_defaults(config) -> StreamConfig`

Supported `model_id` task types:

- `object-detection`
- `instance-segmentation`
- `classification`
- `multi-label-classification`
- `keypoint-detection`
- `semantic-segmentation`

`apply_model_id_defaults(...)` fills empty outputs with `stream_output=['image']`
and `data_output=['predictions']`.

### Stream sources

| Source | Constructor | Best use |
| --- | --- | --- |
| `WebcamSource` | `WebcamSource(device_id=0, resolution=None)` | Local webcam or USB camera. |
| `RTSPSource` | `RTSPSource(url)` | Server-side capture of an RTSP stream. |
| `MJPEGSource` | `MJPEGSource(url)` | Server-side capture of an MJPEG stream. |
| `VideoFileSource` | `VideoFileSource(path, on_upload_progress=None, use_datachannel_frames=True, realtime_processing=False, use_cache=True)` | Local or downloadable video files. |
| `LocalStreamSource` | `LocalStreamSource(url)` | Client-side capture of RTSP/RTMP streams. |
| `ManualSource` | `ManualSource()` | Programmatic frame injection. |

`StreamSource` itself exposes `configure_peer_connection(...)`,
`get_initialization_params(...)`, and optional `cleanup(...)`.

### WebRTCSession

`WebRTCSession` is a context manager with these public methods:

- `run()`
- `wait(timeout: Optional[float] = None)`
- `close()`
- `on_frame(callback)`
- `on_data(field_name: Optional[str] = None)`
- `on_error(callback)`

Other useful public attributes:

- `video()` iterator
- `VideoMetadata(frame_id, received_at, pts=None, time_base=None, declared_fps=None, measured_fps=None, errors=[])`

Important behavior:

- In workflow mode, `video()` yields `(frame, metadata)`.
- In `model_id` mode, `video()` yields `(frame, data)` where `data` is the raw
  predictions dict or `None`.
- `on_frame` in model mode accepts `(frame, data)` or `(frame, data, metadata)`.
- `on_data` accepts `(value)` or `(value, metadata)`.
- `on_error` is only for server-reported per-frame errors.
- `close()` is idempotent and safe to call from callbacks.

### Source-specific notes

- `WebcamSource` auto-detects declared FPS when available.
- `VideoFileSource` can upload a local file or a downloadable URL; when
  `use_datachannel_frames=True`, frames are received through the data channel.
- `LocalStreamSource` accepts only `rtsp://`, `rtsps://`, `rtmp://`, or
  `rtmps://` URLs.
- `RTSPSource` and `MJPEGSource` let the server capture the stream directly.
- `ManualSource.send(frame)` queues a frame for programmatic processing.
