# Serving API Reference

Read this for controller and worker endpoints, streaming payloads, and prompt/image request structure.

## Controller endpoints

The controller owns worker registration and request dispatch.

| Endpoint | Method | Request body | Response or behavior |
|---|---|---|---|
| `/register_worker` | POST | `{"worker_name": url, "check_heart_beat": true, "worker_status": {...}}` | Registers or refreshes a worker. |
| `/refresh_all_workers` | POST | none | Re-queries known workers and drops stale ones. |
| `/list_models` | POST | none | Returns `{"models": [...]}` sorted by UI priority. |
| `/get_worker_address` | POST | `{"model": "otter"}` | Returns `{"address": worker_url}` or empty address. |
| `/receive_heart_beat` | POST | `{"worker_name": url, "queue_length": int}` | Returns `{"exist": true|false}`; false tells worker to re-register. |
| `/worker_generate_stream` | POST | generation payload | Proxies stream chunks from the chosen worker, separated by null bytes. |
| `/worker_get_status` | POST | none | Returns aggregate `model_names`, `speed`, and `queue_length`. |

Dispatch is either `shortest_queue` or weighted `lottery`. `shortest_queue` divides queue length by worker speed and increments the chosen worker queue.

## Worker endpoints

| Endpoint | Method | Request body | Response or behavior |
|---|---|---|---|
| `/worker_generate_stream` | POST | generation payload | Streams JSON chunks terminated with `\0`, each with `text` and `error_code`. |
| `/worker_get_status` | POST | none | Returns `model_names`, `speed`, and `queue_length`. |

The worker wraps generation in an async semaphore sized by `--limit_model_concurrency`. A `ValueError` or `torch.cuda.CudaError` is converted to `error_code: 1` with the generic server error message.

## Generation payload

The worker expects a payload with:

```json
{
  "model": "otter",
  "prompt": "<image>User: describe this image GPT:<answer>",
  "images": ["<urlsafe-base64-encoded-image>"],
  "generation_kwargs": {
    "max_new_tokens": 256,
    "temperature": 0.2,
    "do_sample": true
  }
}
```

Notes:

- `prompt` is tokenized with the model's `text_tokenizer`.
- `images` may be omitted or empty for text-only/no-image cases.
- For image input, `images` is a list of base64-encoded images and becomes `vision_x` shaped like `[B, T, C, H, W]` after unsqueeze operations.
- For video input, the first image element may itself be a list of frame base64 strings; the worker treats that as one video and creates a `[B, T, F, C, H, W]` tensor.
- `generation_kwargs` are passed through to `model.generate` with `vision_x`, `lang_x`, `attention_mask`, and a `TextIteratorStreamer`.
- The worker creates `bad_words_id` for `User:` and `GPT:` but does not pass it to generation in the current code path.

## Prompt conventions

For Otter image prompts, use the same convention as the inference sub-skill:

```text
<image>User: <question> GPT:<answer>
```

For no-image text prompts through Otter-style generation:

```text
User:<question> GPT:<answer>
```

For video, keep one `<image>` marker for the visual context and pass frames through the `images` payload.

## Moderation and logs

The Gradio UI can call OpenAI moderation when `--moderate` is enabled. That path requires `OPENAI_API_KEY` and sends user text to the moderation API. Logs are written under the service log directory configured by the serving code; avoid putting secrets in prompts or model paths.

## Endpoint smoke strategy

Do not run endpoint smoke tests unless the user has allowed long-running local services. For a safe preflight:

1. Run `python scripts/check_serving_imports.py`.
2. Generate command templates with `python scripts/build_serving_commands.py --checkpoint ...`.
3. If services are launched with user permission, call `/list_models` on the controller, then send a small text-only payload to `/worker_generate_stream` only after a worker has registered.
