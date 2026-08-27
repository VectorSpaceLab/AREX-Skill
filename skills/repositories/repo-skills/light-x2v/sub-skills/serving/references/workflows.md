# Serving Workflows

## Standard async image flow

1. Start the service with `python -m lightx2v.server ...`.
2. Submit an image task to `/v1/tasks/image/`.
3. Poll `/v1/tasks/{task_id}/status` until it reaches `completed`.
4. Download the result from `/v1/tasks/{task_id}/result`.
5. Keep the output under the service's output directory so the file route can stream it back.

The bundled `scripts/post_image_task.py` helper performs this sequence for both sync and async image requests.

## Standard async video flow

1. Start the service with a video-capable `model_cls` and matching `task`.
2. Submit a video task to `/v1/tasks/video/`.
3. Poll status until completion.
4. Download the MP4 from `/v1/tasks/{task_id}/result`.

The bundled `scripts/post_video_task.py` helper follows the same queue → poll → download pattern.

## Synchronous image flow

Use `/v1/tasks/image/sync` when you want the service to block until the PNG is ready.

- If no `presigned_url` is provided, the response body is raw PNG bytes.
- If `presigned_url` is provided, the service uploads the PNG and returns a small JSON acknowledgment instead.
- A client disconnect cancels the task.

## OpenAI-compatible image flow

Use `/v1/images/generations` when you want an OpenAI-style interface.

- The request currently supports `n=1` only.
- `size` must use `WxH` format.
- `response_format=b64_json` returns the PNG as base64 in JSON.
- `response_format=url` stores the PNG under the service file root and returns a download URL.

The `/v1/images/edits` endpoint follows the same general response pattern but accepts uploaded image and mask files.

## Queue and cancel flows

- `GET /v1/service/status` tells you whether the service is idle or busy.
- `GET /v1/tasks/` shows the task queue and completed tasks.
- `DELETE /v1/tasks/{task_id}` cancels one task.
- `DELETE /v1/tasks/all/running` cancels all running tasks.

## Gradio note

The Gradio app is a convenience front-end built on top of the same serving logic. Use it when you want an interactive UI, but keep the HTTP API in mind because it is the underlying contract.

## Recommended response style

When you answer a serving question, include:
- the exact endpoint
- whether the flow is sync or async
- which fields are required
- how the result is returned
- the relevant helper script, if one exists
