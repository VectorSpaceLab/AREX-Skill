# Model backends

This reference covers model registration, backend selection, message/media handling, and the most common backend-specific troubleshooting points.

## Backend types

| Type | Typical location | When to use |
| --- | --- | --- |
| Chat | `lmms_eval/models/chat/` | Preferred for new multimodal backends |
| Simple | `lmms_eval/models/simple/` | Legacy or backends without chat-template support |

The registry prefers chat when both chat and simple implementations exist for the same model id.

## Registry behavior

- Model ids and aliases are declared in `lmms_eval/models/__init__.py`.
- `ModelRegistryV2` resolves aliases, chooses chat over simple by default, and validates that `is_simple` matches the resolved type.
- `lmms-eval models --aliases` shows the same registry from the CLI.

## Common constructor arguments

These show up often across the model backends and examples:

| Argument | Meaning |
| --- | --- |
| `pretrained` | Local path or public checkpoint id |
| `model_version` | API-facing model name for provider wrappers |
| `device` / `device_map` | Local device placement |
| `max_new_tokens` | Default generation length |
| `temperature`, `do_sample`, `top_p` | Generation controls |
| `max_pixels` | Image token / resolution budget |
| `max_num_frames` | Video frame budget |
| `tensor_parallel_size` | Parallelism for serving backends |
| `message_format` | Provider-specific message serialization |

## Current request shapes

These are the shapes the current runtime and tests expect when model methods unpack `Instance.args`:

| Output type | Simple model shape | Chat/model-message shape |
| --- | --- | --- |
| `generate_until` | `(ctx, gen_kwargs, doc_to_visual, doc_id, task, split)` | `(ctx, doc_to_messages, gen_kwargs, doc_id, task, split)` |
| `loglikelihood` | `(ctx, doc_to_target, doc_to_visual, doc_id, task, split)` | same as simple in the current evaluator contract when used |
| `generate_until_multi_round` | `(ctx, gen_kwargs, doc_to_visual, doc_to_text, doc_id, task, split)` | same 7-tuple shape |
| `generate_until_agentic` | `(ctx, gen_kwargs, doc_to_visual, doc_to_text, doc_id, task, split)` | same 7-tuple shape |
| `generate_visual_cot` | backend-specific | backend-specific |

If a backend unpacks a different shape, it is probably stale.

## ChatMessages protocol

`lmms_eval.protocol.ChatMessages` is the canonical multimodal container for chat backends.

Useful methods:

- `extract_media()` -> `(images, videos, audios)`
- `to_hf_messages(video_kwargs=None, image_kwargs=None)`
- `to_openai_messages(video_kwargs=None, pass_video_url=False)`
- `to_qwen3_vl_openai_messages(video_kwargs=None)`

The installed runtime exposes the following signature for video loading:

```python
read_video(video_path, *, num_frm=8, fps=None, format='rgb24', force_include_last_frame=False, backend=None)
```

Available video decode backends include `pyav`, `torchcodec`, and `dali`. The `LMMS_VIDEO_DECODE_BACKEND` environment variable controls the default.

## Common backend families

- API/provider wrappers: `openai`, `async_openai`, `claude`, `gemini`, `reka`, `litellm`.
- Local HF-style backends: `qwen2_5_vl`, `qwen3_vl`, `llava_hf`, `internvl_hf`, `huggingface`.
- Serving backends: `vllm`, `vllm_generate`, `sglang`, `async_hf_model`.
- Legacy/simple wrappers: many files in `models/simple/`.

## Throughput metrics

Chat backends log timing-oriented metrics during inference. The user-facing summary often includes:

- end-to-end latency
- time to first token
- time per output token
- output-token throughput

The exact metrics vary by backend; `vllm` has the richest native TTFT/TPOT coverage.

## New model checklist

1. Subclass `lmms_eval.api.model.lmms`.
2. Set `is_simple = False` for chat models.
3. Implement `generate_until`; implement `loglikelihood` when the task family needs it.
4. Register the model id in `lmms_eval/models/__init__.py` or the registry loader.
5. Verify the class with a small smoke before any large evaluation.

## Common backend pitfalls

- `is_simple` is wrong for the resolved model type.
- `model_args` are missing the public checkpoint id or API `model_version`.
- Media helpers return the wrong shape or a non-list.
- Optional backends such as `decord`, `qwen-vl-utils`, `torchcodec`, `vllm`, or `sglang` are absent.
- Video decoders need the right environment variable and, for some backends, a local file rather than a URL.

For backend-specific failures, read the subskill troubleshooting note and use the smoke script in `scripts/model_registry_smoke.py` before opening the source tree.
