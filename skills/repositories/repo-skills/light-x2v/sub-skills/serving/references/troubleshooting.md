# Serving Troubleshooting

## Server startup fails

### Symptoms
- `python -m lightx2v.server` exits before Uvicorn starts.
- The service fails while loading the worker, the file service, or a model runner.

### Likely causes
- The selected `model_cls` / `task` combination is invalid.
- The environment is missing an optional backend such as `decord`, `av`, `fastapi`, `uvicorn`, `httpx`, `requests`, or `pyzmq`.
- The model family expects a path layout that is not present.

### Recovery
- Re-check the inference family reference first.
- Install the missing dependency named in the traceback.
- Confirm the model path and config path before retrying.

## Queue full or busy service

### Symptoms
- Task creation raises a queue-full error.
- `/v1/service/status` stays `busy` longer than expected.

### Likely causes
- Too many pending or processing tasks.
- The worker is still holding the processing lock.

### Recovery
- Cancel stale tasks.
- Reduce the queue pressure and retry.
- Check the service status before resubmitting.

## Invalid request payload

### Symptoms
- `400` from the sync or OpenAI-compatible endpoints.
- `size`, prompt, or URL validation fails.
- A sync image request refuses `n != 1`.

### Likely causes
- Missing prompt or malformed size string.
- Unsupported response format.
- Invalid image / mask URL or a bad presigned URL.

### Recovery
- Validate the request body before sending it.
- For sync image calls, use `WxH` size strings and `n=1`.
- Ensure the image or mask path is reachable or correctly encoded.

## Result download problems

### Symptoms
- `/v1/tasks/{task_id}/result` returns `404`.
- The file route refuses access.

### Likely causes
- The task is not completed yet.
- The save path is outside the service output root.
- The result file was never written because the generation failed.

### Recovery
- Poll `/v1/tasks/{task_id}/status` first.
- Keep `save_result_path` inside the output directory managed by the service.
- Check the underlying task error before retrying.

## Sync upload or disconnect handling

### Symptoms
- Sync image requests time out.
- A client disconnect cancels the task.
- A presigned upload returns `502`.

### Likely causes
- The task took too long for the requested timeout.
- The client dropped the connection while the task was still running.
- The presigned URL is invalid or the upload credentials are wrong.

### Recovery
- Use the async image route when you do not need a blocking response.
- Re-check the presigned URL and credentials.
- If the request is long-running, increase the timeout or switch to async polling.

## What not to do

- Do not treat a service `idle` state as proof that the model family itself is ready; the worker still needs the correct backend and path layout.
- Do not use a generic task script for video if the request requires a family-specific field that is not present.
- Do not push server failures back into the inference route; serving has its own request and result contract.
