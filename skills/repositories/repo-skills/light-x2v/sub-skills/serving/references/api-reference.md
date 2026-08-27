# Serving API Reference

## Service startup

The HTTP service is started with the package entry point:

```bash
python -m lightx2v.server \
  --model_cls wan2.1 \
  --task t2v \
  --model_path /path/to/model \
  --config_json /path/to/config.json \
  --host 0.0.0.0 \
  --port 8000
```

The service runs a distributed inference worker behind the FastAPI layer. The exact `model_cls`, `task`, and model-path layout must still match the inference family contract.

## Endpoint map

| Endpoint | Method | Purpose |
| --- | --- | --- |
| `/` | GET | Redirects to `/docs` |
| `/health` | GET | Simple liveness check |
| `/v1/tasks/` | GET | List all tracked tasks |
| `/v1/tasks/` | POST | Create a video task (legacy compatibility route) |
| `/v1/tasks/video/` | POST | Create a video task |
| `/v1/tasks/video/form` | POST | Create a video task from multipart form data |
| `/v1/tasks/image/` | POST | Create an image task |
| `/v1/tasks/image/sync` | POST | Create a synchronous image task and return PNG bytes or a presigned-upload JSON response |
| `/v1/tasks/image/form` | POST | Create an image task from multipart form data |
| `/v1/tasks/sensenova-vision/` | POST | Multi-task SenseNova-Vision submission |
| `/v1/tasks/{task_id}/status` | GET | Task status payload |
| `/v1/tasks/{task_id}/result` | GET | Download the completed image/video result |
| `/v1/tasks/{task_id}` | DELETE | Cancel one task |
| `/v1/tasks/all/running` | DELETE | Cancel all running tasks |
| `/v1/files/download/{file_path}` | GET | Download a file under the output directory |
| `/v1/service/status` | GET | Service busy/idle summary |
| `/v1/service/metadata` | GET | Inference worker metadata |
| `/v1/images/generations` | POST | OpenAI-compatible image generation |
| `/v1/images/edits` | POST | OpenAI-compatible image editing |

## Core schemas

### Image tasks

`ImageTaskRequest` includes:
- `prompt`
- `negative_prompt`
- `image_path`
- `image_mask_path`
- `save_result_path`
- `seed`
- `infer_steps`
- `aspect_ratio`
- `target_shape`
- `use_prompt_enhancer`
- optional `i2i_denoise_strength`
- optional `presigned_url` for synchronous uploads

### Video tasks

`VideoTaskRequest` includes:
- `prompt`
- `negative_prompt`
- `image_path`
- `last_frame_path`
- `audio_path`
- `save_result_path`
- `seed`
- `infer_steps`
- `target_video_length`
- `num_fragments`
- `video_duration`
- `target_fps`
- `resize_mode`

### OpenAI-compatible image generation

`OpenAIImageGenerationRequest` supports:
- `prompt`
- `n` (currently only `1`)
- `size` in `WxH` form
- `response_format` (`b64_json` or `url`)
- optional `seed`

## Task states

The task manager uses these states:

- `pending`
- `processing`
- `completed`
- `failed`
- `cancelled`

A queued request becomes `processing` when the background loop acquires the processing lock, then `completed` once the generation service finishes and stores the result.

## Status and result expectations

- `GET /v1/tasks/{task_id}/status` returns the current state and the output path when available.
- `GET /v1/tasks/{task_id}/result` only works after completion.
- Synchronous image requests may return raw PNG bytes or a JSON upload acknowledgment when a presigned URL is supplied.
- Service metadata reports the worker world size plus the selected model class and model path.
