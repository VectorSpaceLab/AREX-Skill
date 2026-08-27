# Offline inference API reference

This reference distills the local Python inference APIs that future agents need without reopening the source checkout. Importing or running these APIs can load model weights; the bundled `scripts/build_offline_request.py` is the safe no-load generator.

## Entry points and verified signatures

Prefer explicit entrypoint imports in runnable scripts:

```python
from vllm_omni.entrypoints.omni import Omni
from vllm_omni.entrypoints.async_omni import AsyncOmni
from vllm_omni.inputs.data import OmniDiffusionSamplingParams
```

Verified installed signatures:

```python
Omni.__init__(self, model: str, **kwargs) -> None

Omni.generate(
    self,
    prompts: OmniPromptType | Sequence[OmniPromptType],
    sampling_params_list: OmniSamplingParams | Sequence[OmniSamplingParams] | None = None,
    *,
    py_generator: bool = False,
    use_tqdm: bool | Callable[..., tqdm] = True,
) -> Generator[OmniRequestOutput, None, None] | list[OmniRequestOutput]

AsyncOmni.__init__(self, *args: Any, model: str = "", **kwargs: Any) -> None

AsyncOmni.generate(
    self,
    prompt: OmniPromptType | AsyncGenerator[StreamingInput, None] | list[OmniPromptType],
    sampling_params: Any = None,
    request_id: str = "",
    *,
    prompt_text: str | None = None,
    lora_request: Any = None,
    tokenization_kwargs: dict[str, Any] | None = None,
    sampling_params_list: Sequence[OmniSamplingParams] | None = None,
    output_modalities: list[str] | None = None,
    trace_headers: Mapping[str, str] | None = None,
    priority: int = 0,
    data_parallel_rank: int | None = None,
    reasoning_ended: bool | None = None,
    reasoning_parser_kwargs: dict[str, Any] | None = None,
    arrival_time: float | None = None,
) -> AsyncGenerator[OmniRequestOutput, None]
```

### `Omni(model=..., **kwargs)`

`model` is a model id or local model path. The constructor may resolve or download model weights and initializes the underlying orchestrator/stages.

Common user-facing kwargs include:

- `deploy_config`: path to a deploy YAML when the model needs or benefits from an explicit stage configuration.
- `log_stats`: enable detailed request/stage stats logging.
- `stage_init_timeout`, `init_timeout`: startup timeouts in seconds.
- `output_modalities`: default final output modality list such as `['text']`, `['audio']`, or `['text', 'audio']` when the pipeline supports multiple final stages.
- `diffusion_batch_size`: scheduler-level batch size for diffusion request handling.
- Model/stage options such as dtype, max sequence limits, cache/offload/parallel/quantization options are passed through as kwargs, but detailed planning for those belongs to model-recipes and stage-configuration.

Do not pass an `engine_args` object. Pass supported kwargs directly.

### `Omni.generate(...)`

Use `Omni.generate` for ordinary blocking local scripts.

- `prompts` can be a single prompt (`str`, token prompt, or dict) or a sequence of prompts. For diffusion, multiple prompts are submitted as independent logical requests; the runtime may co-batch compatible requests internally.
- `sampling_params_list` can be `None`, one `SamplingParams`/`OmniDiffusionSamplingParams`, or a sequence matching pipeline stages. If omitted, model/deploy defaults are used.
- `py_generator=False` returns a `list[OmniRequestOutput]` after completion.
- `py_generator=True` returns a Python generator that yields `OmniRequestOutput` objects as final stage outputs are produced. Consume or close the generator; after generator completion the wrapper closes the `Omni` instance.
- `use_tqdm=False` disables the progress bar for scripts or tests.

`Omni.generate` coerces non-delta LLM stage sampling params to final-only output unless that stage explicitly requested delta streaming. For stage-level streaming/chunking, use `AsyncOmni`.

### `AsyncOmni.generate(...)`

Use `AsyncOmni` when you need async generator consumption, request concurrency, or async-chunk style stage overlap.

- It yields `OmniRequestOutput` objects through `async for`.
- `request_id` is optional; the runtime appends an internal random suffix and reports the external id back on yielded objects.
- `sampling_params` is a convenience for the first stage. `sampling_params_list` is the explicit per-stage form.
- `output_modalities` selects final output stage(s) for that request.
- When sampling params are omitted, async generation normally coerces suitable stages toward delta output, so consumers must be prepared for partial audio/text chunks before a final `finished=True` item.
- If a pipeline has a diffusion stage, `AsyncOmni.generate` rejects a `list` prompt for that single request. Submit independent requests concurrently instead.
- Call `async_omni.shutdown()` in `finally` when the object owns workers.

## Prompt dictionary contracts

An Omni prompt may be a vLLM native prompt or an Omni dictionary. Common dictionary keys:

| Key | Use |
| --- | --- |
| `prompt` | Text prompt or model-specific chat template string. |
| `modalities` | Requested final modality routing, e.g. `['image']`, `['video']`, `['text']`, `['audio']`, or `['text', 'audio']`. |
| `negative_prompt` | Diffusion classifier-free guidance negative prompt when supported. |
| `multi_modal_data` | Input media payloads, e.g. `{'image': PIL.Image}`, `{'audio': (np.ndarray, sr)}`, `{'video': list_or_array_of_frames}`. |
| `mm_processor_kwargs` | Extra multimodal preprocessor flags, such as `{'use_audio_in_video': True}` for models that use a video's audio track. |
| `additional_information` | Model-specific structured payload, especially TTS tasks and staged pipelines. |
| `prompt_token_ids` | Token placeholder list for models that replace embeddings internally, such as some TTS paths. |
| `prompt_embeds`, `negative_prompt_embeds` | Precomputed embedding tensors for advanced stage-transfer or diffusion paths. |
| `model_intermediate_buffer` | Runner-owned stage payload for pipeline transfer; use only when implementing advanced stage interactions. |

Canonical prompt shapes:

```python
# Text-to-image / image generation.
prompt = {"prompt": "a cup of coffee on the table", "modalities": ["image"]}

# Image-to-image/edit.
prompt = {
    "prompt": "change the background to a classroom",
    "modalities": ["image"],
    "multi_modal_data": {"image": input_image},
}

# Image-to-video.
prompt = {
    "prompt": "the fox turns toward the camera",
    "modalities": ["video"],
    "multi_modal_data": {"image": input_image},
}

# Multimodal chat/comprehension.
prompt = {
    "prompt": chat_template_string_with_media_placeholders,
    "multi_modal_data": {"image": input_image, "audio": (audio_np, sample_rate)},
}

# TTS/task payload.
prompt = {
    "prompt_token_ids": [0] * estimated_prompt_len,
    "additional_information": {
        "task_type": ["CustomVoice"],
        "text": ["Text to speak"],
        "language": ["English"],
        "speaker": ["Ryan"],
        "max_new_tokens": [2048],
    },
}
```

## Sampling params

`OmniSamplingParams` means either vLLM `SamplingParams` for autoregressive stages or `OmniDiffusionSamplingParams` for diffusion stages.

### `OmniDiffusionSamplingParams`

Most user-facing diffusion fields:

| Field | Meaning and guidance |
| --- | --- |
| `height`, `width` | Output pixel dimensions when supported. Leave as `None` to use model defaults. Lower them to reduce memory. |
| `num_frames` | Number of frames for video generation. Images default to `1`. Lower it to reduce memory/time. |
| `fps`, `frame_rate` | Output encoding and model-internal frame-rate hints. `frame_rate` takes precedence for model runtime; `fps` is also used by output encoding. |
| `num_inference_steps` | Denoising steps. More steps may improve quality but increase latency. Some few-step/distilled models expect small values. |
| `guidance_scale` | Common diffusion guidance scale. Model defaults differ; very high values may reduce quality. |
| `guidance_scale_2`, `true_cfg_scale`, `guidance_rescale` | Model-specific secondary or true CFG controls used by some image/edit/video models. |
| `strength` | Image-to-image denoising strength for models that support it. |
| `seed` | Request-scoped deterministic seed. If also using a `torch.Generator`, keep seed/generator consistent. |
| `generator`, `generator_device` | Optional explicit torch generator(s). Device must match the runtime backend. |
| `output_type` | Optional model/pipeline output type selector, such as image vs latent where supported. |
| `num_outputs_per_prompt` | Number of images/videos/audio outputs per prompt when supported. |
| `extra_args` | Dictionary for declared model-specific controls that do not have stable top-level fields. |
| `return_frames`, `save_output` | Output/format toggles used by selected diffusion pipelines. |
| `return_trajectory_latents`, `return_trajectory_decoded` | Request denoising trajectory payloads for debugging/RL-like consumers when supported. |
| `lora_request`, `lora_scale` | Per-request LoRA adapter request and scale. Adapter loading/backend selection is configured at model init/deploy level. |

`OmniDiffusionSamplingParams.from_params(vllm.SamplingParams)` maps `SamplingParams.seed` and recognized `extra_args` keys into diffusion fields. Unsupported param types raise `TypeError`.

Offload, HSDP, sequence/ring/CFG parallelism, cache backends, quantization, and device placement are constructor/deploy concerns, not ordinary request sampling fields. Route those decisions to model-recipes or stage-configuration.

### Per-stage params

For single-stage diffusion models, this is often enough:

```python
sampling_params = OmniDiffusionSamplingParams(height=1024, width=1024, seed=42)
outputs = omni.generate(prompt, sampling_params)
```

For multi-stage pipelines, pass one params object per stage or start from `omni.default_sampling_params_list` and replace the diffusion stage object:

```python
from copy import deepcopy

params = [deepcopy(p) for p in (omni.default_sampling_params_list or [])]
diffusion_params = OmniDiffusionSamplingParams(height=1024, width=1024, seed=42)

replaced = False
for i, p in enumerate(params):
    if isinstance(p, OmniDiffusionSamplingParams):
        params[i] = diffusion_params
        replaced = True
if not params or (not replaced and len(params) == 1):
    params = [diffusion_params]

outputs = omni.generate(prompt, sampling_params_list=params)
```

## Output object access

`Omni.generate` and `AsyncOmni.generate` yield or return `OmniRequestOutput` objects. Important fields:

| Field/property | Meaning |
| --- | --- |
| `request_id` | External request id when provided, otherwise generated id. |
| `finished` | Whether this item completes the request/stage. Async delta flows may yield unfinished chunks. |
| `stage_id`, `replica_id` | Stage metadata for pipeline outputs. |
| `final_output_type` | Usually `text`, `image`, `audio`, `video`, or `latents`/`latent`. Some video diffusion paths place frames in image-like fields. |
| `outputs` | vLLM completion outputs. Text is usually `outputs[0].text`; AR multimodal payloads may be `outputs[0].multimodal_output`. |
| `images` | List of PIL images or image/video-like payloads for diffusion paths. |
| `multimodal_output` | Dict-like payload for generated tensors/metadata. It may be a structured mapping with `.to_dict()`. |
| `custom_output` | Custom model/pipeline data. |
| `latents`, `trajectory_latents`, `trajectory_timesteps`, `trajectory_log_probs`, `trajectory_decoded` | Latent/trajectory payloads when requested and supported. |
| `metrics`, `stage_durations`, `peak_memory_mb` | Request metrics and profiling/memory summaries when available. |
| `error`, `error_status_code`, `error_type` | Terminal error output fields if an error object is returned instead of raised. |

Robust access pattern:

```python
def as_plain_mapping(mm):
    if mm is None:
        return {}
    if hasattr(mm, "to_dict") and callable(mm.to_dict):
        return mm.to_dict()
    return dict(mm) if hasattr(mm, "items") else {}


def first_text(output):
    if getattr(output, "outputs", None):
        text = getattr(output.outputs[0], "text", None)
        if text is not None:
            return text
    mm = as_plain_mapping(getattr(output, "multimodal_output", None))
    return mm.get("text")


def image_payloads(output):
    if getattr(output, "images", None):
        return list(output.images)
    mm = as_plain_mapping(getattr(output, "multimodal_output", None))
    for key in ("image", "images", "model_outputs"):
        if key in mm:
            value = mm[key]
            return value if isinstance(value, list) else [value]
    return []


def audio_payload(output):
    candidates = []
    if getattr(output, "outputs", None):
        candidates.append(getattr(output.outputs[0], "multimodal_output", None))
    candidates.append(getattr(output, "multimodal_output", None))
    for candidate in candidates:
        mm = as_plain_mapping(candidate)
        if "audio" in mm:
            sr = None
            for key in ("sr", "sample_rate", "audio_sample_rate"):
                if key in mm and mm[key] is not None:
                    sr = mm[key]
                    break
            metadata = mm.get("metadata") if isinstance(mm.get("metadata"), dict) else {}
            if sr is None:
                sr = metadata.get("sample_rate")
            if sr is None and isinstance(metadata.get("audio"), dict):
                sr = metadata["audio"].get("sample_rate")
            return mm["audio"], sr
    return None, None
```

For audio chunks, concatenate lists of tensors along the last dimension when shapes allow, then flatten to one-dimensional CPU data before writing WAV. For image/video tensors, detach and move to CPU before converting or encoding. For text, concatenate async delta text parts if the model emits partial chunks.
