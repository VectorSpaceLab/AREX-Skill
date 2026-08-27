---
name: sdk-webrtc
description: "Route Roboflow Inference SDK users through InferenceHTTPClient,
  HTTP configuration and error mapping, workflow and pipeline APIs, and WebRTC
  streaming sources and session lifecycle."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# SDK and WebRTC

Use this sub-skill when the user wants to call the Python SDK, configure HTTP
requests, choose workflow versus model_id streaming, or stream webcam, video
file, RTSP, MJPEG, local RTSP/RTMP, or manual frames through WebRTC.

## Route here when

- The user asks how to create or reuse `InferenceHTTPClient`.
- They need `infer`, `infer_async`, `infer_from_workflow`, `run_workflow`, or
  pipeline lifecycle calls.
- They want to configure `InferenceConfiguration`, inspect `HTTPClientMode`, or
  interpret SDK errors.
- They want to use `client.webrtc.stream(...)` with `WebcamSource`,
  `VideoFileSource`, `RTSPSource`, `MJPEGSource`, `LocalStreamSource`, or
  `ManualSource`.
- They need to understand session lifecycle, `on_frame`, `on_data`,
  `on_error`, `video()`, `wait()`, or cleanup behavior.
- They need the bundled webcam or video-file example flows.

## Do not route here when

- The request is about CLI commands such as `inference workflows ...`. Use
  [workflow-processing](../workflow-processing/SKILL.md).
- The request is about starting or deploying the inference server, Docker, or
  CLI server lifecycle. Use [cli-operations](../cli-operations/SKILL.md).
- The request is about backend/package negotiation, `AutoModel`, or model
  runtime selection. Use [model-runtime](../model-runtime/SKILL.md).

## Read these bundled references

1. [API reference](references/api-reference.md) for verified signatures,
   config fields, and error classes.
2. [Workflow and WebRTC patterns](references/webrtc-workflows.md) for workflow
   versus model_id choice, source selection, and session usage.
3. [Troubleshooting](references/troubleshooting.md) for auth, wrong URL/mode,
   missing WebRTC deps, invalid parameter combinations, and cleanup failures.
4. [Surface probe](scripts/check_webrtc_surface.py) when you need a safe
   import/signature check.
5. [Webcam example](scripts/webcam_basic.py) for an interactive webcam flow.
6. [Video file example](scripts/video_file_basic.py) for an interactive
   video-file flow.

## Operating rules

- Start with `InferenceHTTPClient.init(api_url, api_key)` or
  `InferenceHTTPClient(api_url, api_key)` and check `client.client_mode`
  before assuming an endpoint family.
- Use `client.webrtc.stream(...)` for WebRTC sessions. Pass exactly one of
  `workflow` or `model_id`.
- Use `workflow=` for multi-step workflows, inline workflow specs, or VLM-style
  flows. Use `model_id=` for a single supported model when you want the raw
  predictions dict per frame.
- If `workflow` is a string ID, also provide `workspace=`. If `workflow` is a
  dict, `workspace=` is optional.
- Do not pass `task_type` without `model_id`.
- In model_id mode, treat `data` as the raw serialized predictions dict and
  check for `None`.
- Prefer `with client.webrtc.stream(...) as session:` or call `session.close()`
  explicitly.
- Use `session.on_error` for server-reported per-frame failures; connection or
  initialization failures surface as exceptions.
- Use `session.video()` for iterator-style consumption and `session.run()` for
  callback-style consumption.
- `VideoFileSource` and `WebcamSource` are the two bundled examples; adapt them
  rather than reopening the source repo.
- Route anything about workflow CLI commands to `workflow-processing`, and
  route backend negotiation or `AutoModel` questions to `model-runtime`.

## What this sub-skill should answer

- How do I create the SDK client and pick the right HTTP mode?
- How do I run a hosted workflow, an inline workflow spec, or a pipeline
  request?
- How do I stream webcam or video frames and handle cleanup?
- When should I use `workflow=` versus `model_id=`?
- Which source class should I use for webcam, RTSP, MJPEG, video files, local
  streams, or manual frames?
