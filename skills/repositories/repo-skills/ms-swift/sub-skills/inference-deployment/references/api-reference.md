# Inference API Reference

This reference summarizes the ms-swift inference/deployment argument classes, engine classes, request objects, endpoints, and request shapes most useful to coding agents.

## CLI entry points

- `swift infer`: runs interactive, dataset, or batch inference through `InferArguments`.
- `swift deploy`: starts an OpenAI-compatible FastAPI server through `DeployArguments`.
- `swift app`: starts a Gradio inference UI through `AppArguments`; it either self-deploys a model or connects to an existing base URL.

The package import root is `swift`. Common public imports are also re-exported from `swift`, while engine-specific imports are available from `swift.infer_engine`.

## `InferArguments` essentials

`InferArguments` controls direct inference. It extends model/template/base arguments plus backend argument mixins.

| Field/flag | Use |
| --- | --- |
| `--model` | Base model id or local model directory. |
| `--adapters` | One or more LoRA adapter paths or model ids; deploy also accepts `name=path` mappings. |
| `--merge_lora true` | Merge adapter before inference when appropriate. Useful for backends that cannot dynamically load the adapter. |
| `--infer_backend` | One of `transformers`, `vllm`, `sglang`, `lmdeploy`; legacy `pt` maps to `transformers`. |
| `--stream` | Streaming display for interactive inference. Avoid for batch result persistence. |
| `--max_new_tokens` | Default maximum generated tokens; maps into request generation config. |
| `--temperature`, `--top_p`, `--top_k`, `--repetition_penalty`, `--num_beams` | Generation controls used to build `RequestConfig`. |
| `--result_path` | JSONL output path for dataset/batch inference or deployed request logging. |
| `--write_batch_size` | Batch size for writing result shards. |
| `--metric acc|rouge` | Optional post-inference metric when labels are available. |
| `--max_batch_size` | `transformers` engine batch cap; accelerated backends use their own batching. |
| `--val_dataset`, `--dataset`, `--val_dataset_sample` | Enter dataset inference mode instead of human interactive mode. |
| `--logprobs true`, `--top_logprobs`, `--prompt_logprobs` | Request logprob outputs where backend/server supports them. |

Behavior notes:

- With no dataset, `swift infer` defaults to interactive human mode and typically streams unless disabled.
- With a validation/evaluation dataset, Swift initializes result saving and dataset iteration.
- In distributed inference, interactive and streaming modes are not supported.
- If `--infer_backend vllm` and adapters are set, Swift uses an adapter request for the first adapter in direct inference.

## `DeployArguments` essentials

`DeployArguments` extends `InferArguments` with server settings.

| Field/flag | Use |
| --- | --- |
| `--host` | Bind host; default is `0.0.0.0`. Use `127.0.0.1` for local-only serving. |
| `--port` | Requested port; Swift finds a free port starting from this value. |
| `--api_key` | Optional bearer token required by OpenAI-compatible clients. |
| `--ssl_keyfile`, `--ssl_certfile` | Optional TLS files. |
| `--owned_by` | Owner string in `/v1/models` responses. |
| `--served_model_name` | Public model id for clients. Defaults to the model suffix when unset. |
| `--verbose` | Log request details. Defaults true for deploy, false in app/eval-like contexts. |
| `--log_interval` | Seconds between throughput/stat logs; `-1` disables. |
| `--log_level` | Uvicorn/server logging level. |
| `--max_logprobs` | Server-side maximum accepted `top_logprobs`; default `20`. |
| `--vllm_use_async_engine` | Defaults true for deploy scenarios. Required for vLLM data parallel deploy. |

Deployment adapter mapping:

- `--adapters ./adapter` loads an unnamed adapter in model setup.
- `--adapters lora1=./adapter-a lora2=./adapter-b` exposes `lora1` and `lora2` as extra model ids in `/v1/models`.
- Swift resolves adapter paths/model ids and creates an `adapter_mapping`; client `model` chooses the adapter request.

## `AppArguments` essentials

`AppArguments` combines web UI arguments and deployment arguments.

| Field/flag | Use |
| --- | --- |
| `--base_url` | Existing OpenAI-compatible base URL such as `http://127.0.0.1:8000/v1`; if unset, app launches a local deployment. |
| `--studio_title` | UI title; defaults from the model when unset. |
| `--is_multimodal` | Force multimodal UI when auto-detection is not possible. |
| `--lang en|zh` | UI language. |
| `--server_name`, `--server_port`, `--share` | Gradio launch controls inherited from web UI arguments. |
| `--stream` | Defaults true for app responses. |

If `--base_url` is set, `swift app` does not load a local model and instead builds a UI against the provided service.

## Engine classes

Import engines from `swift.infer_engine`.

| Engine | Constructor focus | Best use |
| --- | --- | --- |
| `TransformersEngine` | `TransformersEngine(model, max_batch_size=..., adapters=..., device_map=..., attn_impl=...)` | Maximum Swift model compatibility, QLoRA support, local debugging, custom Python apps. |
| `VllmEngine` | `VllmEngine(model_id_or_path, max_model_len=..., max_num_seqs=..., tensor_parallel_size=..., limit_mm_per_prompt=..., enable_lora=...)` | High-throughput LLM/VLM inference and deploy for vLLM-supported models. |
| `SglangEngine` | `SglangEngine(model_id_or_path, tp_size=..., dp_size=..., pp_size=..., context_length=...)` | SGLang-supported accelerated text inference/deployment. |
| `LmdeployEngine` | `LmdeployEngine(model_id_or_path, tp=..., session_len=..., cache_max_entry_count=..., vision_batch_size=...)` | LMDeploy-supported accelerated text/VLM inference. |
| `InferClient` | `InferClient(host="127.0.0.1", port=8000, api_key="EMPTY", base_url=None)` | Swift-native client for a local/remote `swift deploy` service. |

All engines implement:

```python
engine.infer([InferRequest(...)], RequestConfig(...))
await engine.infer_async(InferRequest(...), RequestConfig(...))
```

Streaming responses return iterators of stream chunks; non-streaming responses return chat completion response objects.

## `InferRequest`

`InferRequest` is the internal request container.

```python
from swift.infer_engine import InferRequest

request = InferRequest(
    messages=[{"role": "user", "content": "Who are you?"}],
)
```

Fields:

| Field | Meaning |
| --- | --- |
| `messages` | Chat messages. Each message has `role` and `content`. |
| `images` | Image resources as local paths, URLs, base64 strings, or PIL images. |
| `videos` | Video resources as local paths, URLs, or base64 strings. |
| `audios` | Audio resources as local paths, URLs, or base64 strings. |
| `tools` | Optional tool specs for agent templates. |
| `objects` | Extra multimodal objects grouped by type. |
| `chat_template_kwargs` | Extra template-specific request data. |

Multimodal requests can use either tag style:

```python
InferRequest(
    messages=[{"role": "user", "content": "<image>Describe this image."}],
    images=["./image.png"],
)
```

or OpenAI-style content blocks:

```python
InferRequest(messages=[{
    "role": "user",
    "content": [
        {"type": "image", "image": "./image.png"},
        {"type": "text", "text": "Describe this image."},
    ],
}])
```

The number and order of `<image>`, `<video>`, and `<audio>` tags should match the corresponding media lists.

## `RequestConfig`

`RequestConfig` captures per-request generation behavior.

| Field | Meaning |
| --- | --- |
| `max_tokens` | Maximum generated tokens. `None` lets Swift/backend infer from model length. |
| `temperature`, `top_k`, `top_p`, `repetition_penalty` | Sampling controls. Defaults differ from OpenAI defaults when unset. |
| `num_beams` | Beam count; streaming is disabled when beams are not 1. |
| `stop` | Stop strings. |
| `seed` | Per-request seed where supported. |
| `stream` | Return stream chunks when true. |
| `logprobs`, `top_logprobs`, `prompt_logprobs` | Token probability outputs where supported. |
| `n`, `best_of` | Multiple completion controls where backend supports them. |
| `presence_penalty`, `frequency_penalty`, `length_penalty` | Additional generation penalties. |
| `return_details` | Return token ids/details in non-stream mode where supported. |
| `structured_outputs_regex` | vLLM guided decoding regex support. |

## OpenAI-compatible endpoints

`swift deploy` registers:

| Endpoint | Method | Use |
| --- | --- | --- |
| `/health` | GET | Health check. |
| `/ping` | GET/POST | SageMaker-style ping/health check. |
| `/v1/models` | GET | Model list; includes served base model and named adapters. |
| `/v1/chat/completions` | POST | OpenAI-compatible chat generation. |
| `/v1/completions` | POST | Completion API converted internally to chat completion. |
| `/v1/embeddings` | POST | Embedding API converted internally. |
| `/infer/` | POST | Swift rollout/internal endpoint accepting `infer_requests` and `request_config`. |

Chat request shape:

```json
{
  "model": "served-model-name",
  "messages": [{"role": "user", "content": "Who are you?"}],
  "max_tokens": 128,
  "temperature": 0,
  "stream": false,
  "logprobs": false
}
```

Streaming returns server-sent `data:` chunks and a final `data: [DONE]` marker.

## Python server lifecycle helper

Swift exposes a deployment context helper for tests or local tooling:

```python
from swift import DeployArguments
from swift.pipelines.infer import run_deploy

args = DeployArguments(
    model="Qwen/Qwen2.5-0.5B-Instruct",
    infer_backend="transformers",
    host="127.0.0.1",
    port=8000,
)
with run_deploy(args, return_url=True) as base_url:
    print(base_url)
```

This launches deployment in a spawned process and terminates it when the context exits. Use it only in controlled scripts/tests because it loads the model.
