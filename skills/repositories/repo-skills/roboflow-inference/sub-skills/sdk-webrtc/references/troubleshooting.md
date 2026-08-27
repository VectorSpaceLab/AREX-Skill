# Troubleshooting

This page covers the predictable SDK and WebRTC failure modes that future agents
should recognize quickly.

## API key redaction and auth

| Symptom | Likely cause | What to do next |
| --- | --- | --- |
| `APIKeyNotProvided` | The call needs authentication and no key was passed. | Pass `api_key=` when creating `InferenceHTTPClient` or use the same key for the WebRTC stream. |
| `HTTPCallErrorError` with 401/403 | The key was passed, but the server rejected it. | Check that the key belongs to the right Roboflow workspace and that the model/workflow is accessible. |
| `RuntimeError` from `resolve_task_type(...)` mentioning a redacted `api_key=` string | Model-id task lookup failed, usually because the model is private, inaccessible, or the API is unreachable. | The error intentionally redacts secrets. Re-check access, or pass `task_type=` explicitly when you already know it. |

Notes:

- The task-type lookup sends the key in an `Authorization` header, not in the URL.
- The surfaced error should never contain the raw secret.

## Wrong client mode or wrong API URL

| Symptom | Likely cause | What to do next |
| --- | --- | --- |
| `WrongClientModeError` | A v1-only method was called while the client is in v0 mode, or the inverse. | Check `client.client_mode`. Use `select_api_v0()` / `select_api_v1()` only when you intentionally override the auto choice. |
| Unexpected v0-style URLs when using a self-hosted server | The API URL was treated as hosted Roboflow, or the wrong endpoint was chosen. | Pick the correct `api_url` and verify whether the server is hosted or self-hosted. |
| 404 on `/initialise_webrtc_worker` | The host does not support WebRTC, or the URL points at the wrong Roboflow surface. | For self-hosted inference, confirm WebRTC is enabled. For Roboflow-hosted use, do not point WebRTC at a serverless URL. |

The 404 case is especially common when a serverless or otherwise non-WebRTC host is
used as the `api_url` for `client.webrtc.stream(...)`.

## Missing WebRTC dependencies

| Symptom | Likely cause | What to do next |
| --- | --- | --- |
| `ImportError: WebRTC dependencies are not installed` | `aiortc` and `av` are missing. | Install `inference-sdk[webrtc]` or at least `aiortc>=1.9.0` plus the pinned `av` dependency. |
| `ModuleNotFoundError: dataclasses_json` while importing the SDK | The base SDK dependency set is incomplete. | Install the full SDK dependency set before trying the WebRTC helpers again. |
| `scripts/check_webrtc_surface.py` reports a missing import | The runtime surface is not fully installed. | Use the helper output to identify the missing package, then install the smallest compatible set. |

## Workflow versus model_id mistakes

| Symptom | Likely cause | What to do next |
| --- | --- | --- |
| `InvalidParameterError: Exactly one of 'workflow' or 'model_id' must be provided` | Both were passed, or neither was passed. | Choose one route only. |
| `task_type is only valid together with 'model_id'` | `task_type` was supplied in workflow mode. | Remove `task_type`, or switch to `model_id=`. |
| `workspace parameter required when workflow is an ID string` | A hosted workflow id was passed without a workspace. | Add `workspace=` or switch to an inline workflow dict. |
| `task_type ... is not supported for model_id streaming` | The model type is not in the supported model-id list. | Use `workflow=` instead, or choose a supported task type. |
| The error message points at workflow= for a VLM model | VLMs do not have a generic model block for `model_id` mode. | Pass a full workflow specification. |

## Session lifecycle and cleanup

| Symptom | Likely cause | What to do next |
| --- | --- | --- |
| `TimeoutError` from `wait()` | The stream never ended within the timeout. | Use a larger timeout, or call `session.close()` when your callback decides to stop. |
| `WebRTCSession was not properly closed` warning | The session was left for garbage collection. | Prefer `with client.webrtc.stream(...) as session:` or call `session.close()` explicitly. |
| A callback exits but the stream keeps running | The callback raised or returned without closing the session. | Call `session.close()` from the callback or use the context manager. |
| `TypeError` in a frame/data handler | The callback arity does not match the mode. | In workflow mode use `(frame, metadata)`. In model mode use `(frame, data)` or `(frame, data, metadata)`. For `on_data`, use `(value)` or `(value, metadata)`. |

Cleanup rules to remember:

- `close()` is idempotent.
- `close()` is safe from callbacks and other threads.
- `on_error` only reports server-side per-frame errors, not connection setup failures.
- `VideoFileSource(use_cache=False)` deletes its temporary download during cleanup.

## Source-specific input issues

| Symptom | Likely cause | What to do next |
| --- | --- | --- |
| `InvalidParameterError` for a source URL | The scheme is not allowed by that source class. | Use `rtsp://` or `rtsps://` for `RTSPSource`, `http(s)` for `MJPEGSource`, and `rtsp(s)`/`rtmp(s)` for `LocalStreamSource`. |
| `RuntimeError: Could not open webcam device` | The webcam device index is unavailable. | Check the device number and whether another app is using the camera. |
| `RuntimeError: Failed to read from ...` | The video file or capture source cannot be read. | Check the file, codec support, or stream availability. |
| Download or cache failure for a video URL | The video source URL is unreachable or the cache path is not writable. | Retry with a reachable URL, or disable caching with `use_cache=False`. |

If the problem is actually backend installation, package negotiation, or `AutoModel`
selection, stop here and use [model-runtime](../../model-runtime/SKILL.md) instead.
