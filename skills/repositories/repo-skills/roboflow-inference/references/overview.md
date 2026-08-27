# Overview

This page maps Roboflow Inference surfaces to the bundled sub-skills.
Use it when you already know the task family but want a quick reminder of the
right route.

## Surface map

| Surface | Typical user request | Owning sub-skill |
| --- | --- | --- |
| `inference server start|status|stop` | Start or manage the local server, confirm Docker, or expose a tunnel. | `cli-operations` |
| `inference infer` | Run one-shot inference on an image, directory, or video. | `cli-operations` |
| `inference benchmark api-speed` | Benchmark API inference against a server or hosted endpoint. | `cli-operations` |
| `inference benchmark python-package-speed` | Benchmark the local `inference` package. | `cli-operations` |
| `inference benchmark inference-models-speed` | Experimental CLI benchmark for `inference-models`. | `cli-operations` for the command, `model-runtime` for backend or trust choices |
| `inference cloud ...` | Deploy or manage cloud inference VMs. | `cli-operations` |
| `inference rf-cloud ...` | Work with Roboflow Cloud staging or batch jobs. | `cli-operations` |
| `inference enterprise inference-compiler ...` | Compile a model into TensorRT through the enterprise CLI. | `cli-operations` |
| `inference workflows process-*` | Process images, image directories, or video files through Workflows. | `workflow-processing` |
| `InferenceHTTPClient` / `client.webrtc.stream(...)` | Call the Python SDK, workflow APIs, or stream frames. | `sdk-webrtc` |
| `AutoModel.from_pretrained(...)` | Load models, choose backends, or inspect runtime support. | `model-runtime` |

## Package map

| Package family | What it covers | What to read |
| --- | --- | --- |
| `inference` / `inference-cli` | CLI entry points, server lifecycle, cloud, rf-cloud, and workflow command families. | `cli-operations` or `workflow-processing` |
| `inference-sdk` | HTTP client, workflow API calls, and WebRTC streaming. | `sdk-webrtc` |
| `inference-models` | AutoModel loading, backend selection, local packages, cache/offline behavior, and runtime inspection. | `model-runtime` |

## Selection guidance

Choose the sub-skill that owns the exact user-facing command or API, then use a
neighboring sub-skill for shared troubleshooting if needed:

- server / cloud / rf-cloud / enterprise → `cli-operations`
- workflow CLI image or video processing → `workflow-processing`
- HTTP client or WebRTC frames → `sdk-webrtc`
- backend selection or package negotiation → `model-runtime`

If the user request spans more than one row, start from the row they named most
explicitly and hand off only for the adjacent concern.
