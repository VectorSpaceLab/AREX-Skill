---
name: "serving"
description: "Routes LightX2V FastAPI service workflows, task APIs,
  OpenAI-compatible image endpoints, queue inspection, and result download
  flows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Serving

Use this sub-skill for any LightX2V request that goes through the HTTP service stack instead of the direct pipeline.

## Typical triggers

- "start the LightX2V server"
- "how do I call `/v1/tasks` or `/v1/images`?"
- "how do I poll task status or download the result?"
- "how do I stop a task?"
- "how do I use the sync image endpoint or presigned upload?"
- "how do I debug service status, queue pressure, or client disconnects?"

## Read first

- [`references/api-reference.md`](references/api-reference.md) for the endpoint map and request/response schemas.
- [`references/workflows.md`](references/workflows.md) for the standard start/submit/poll/download sequence and the OpenAI-compatible image flows.
- [`references/troubleshooting.md`](references/troubleshooting.md) for the expected error codes and recovery steps.
- [`scripts/start_server.sh`](scripts/start_server.sh) when you want a shell wrapper for the service entry point.
- [`../../references/troubleshooting.md`](../../references/troubleshooting.md) for cross-cutting import and dependency failures.

## What belongs here

Include:
- `python -m lightx2v.server`
- `ApiServer`, `TaskManager`, `FileService`, and the generation service layer
- `/v1/tasks`, `/v1/images`, `/v1/files`, and `/v1/service`
- image and video queueing, polling, download, and stop flows
- OpenAI-compatible image generation and edit endpoints
- presigned upload handling for synchronous image tasks
- Gradio deployments that sit on top of the same serving stack

Exclude or route elsewhere:
- direct generation without the HTTP API → `sub-skills/inference/`
- controller / encoder / transformer / decoder deployment → `sub-skills/disagg/`
- LoRA, dummy-meta, and conversion helpers → `sub-skills/conversion/`

## Safe starting checks

- `python scripts/check_install.py`
- `python -m lightx2v.server --help`
- `python sub-skills/serving/scripts/check_status.py --url http://127.0.0.1:8000`
- `bash sub-skills/serving/scripts/start_server.sh --help`

## Guidance style

Prefer concrete, user-facing instructions:
- name the endpoint and the request type
- mention whether the request is synchronous or asynchronous
- show which fields are required for images, masks, video, audio, or presigned uploads
- state the expected status transitions and final download path
- call out when a response is JSON versus a binary image/video body

## Decision points

When answering a serving question, separate the problem into these choices:
- transport: sync HTTP, async queue, or OpenAI-compatible endpoint
- media type: image, video, mask, or presigned upload response
- response shape: binary bytes, task JSON, download URL, or status JSON
- control action: poll, download, cancel, inspect queue, or inspect service metadata
- helper script: `check_status.py`, `stop_task.py`, `post_image_task.py`, `post_video_task.py`, `post_openai_image.py`, or `start_server.sh`

Common reminders:
- sync image calls only support `n=1`
- size strings must use `WxH` format for the OpenAI-compatible image API
- the result download route only works after the task reaches `completed`
- presigned uploads return JSON acknowledgment instead of raw image bytes
- the Gradio front-end is a convenience layer over the same serving stack

## What a good answer should contain

For a future agent, a strong answer from this route should usually include:
- the endpoint name and method
- whether the flow is sync or async
- the required request fields and any size / format constraints
- the expected response shape, download path, or cancellation behavior
- the helper script that matches the exact flow, when one exists

If the request is really about how to generate a model output from local code, route back to inference; if it is about how the server accepts and serves that output, keep it here.
