# Model Loading and Serving CLI

This reference distills align-anything serving behavior from the package's model loader, registry, serving CLIs, device utilities, evaluation docs, and bundled script patterns. It is self-contained for runtime use; do not depend on the original checkout being present.

## Loading entry point

Use `align_anything.models.pretrained_model.load_pretrained_models(...)` for text, vision-language, audio-language, video-language, reward, MiniCPM-V/O, and other registered causal-LM-style models.

Core call shape:

```python
from align_anything.models.pretrained_model import load_pretrained_models

model, tokenizer, processor = load_pretrained_models(
    model_name_or_path,
    model_max_length=2048,
    padding_side="right",
    auto_device_mapping=False,
    dtype=torch.float16,
    cache_dir=None,
    trust_remote_code=True,
    is_reward_model=False,
    modality=["image", "audio"],          # optional; useful for remote-code models
    auto_model_kwargs={},                  # optional model-specific overrides
    auto_tokenizer_kwargs={},              # optional tokenizer-specific overrides
    processor_kwargs={},                   # optional AutoProcessor kwargs
)
```

The loader returns three values even though some type hints in the package are narrower:

- `model`: an `AnyModel` or `AnyModelForScore` instance, usually a Transformers `PreTrainedModel` subclass.
- `tokenizer`: the processor tokenizer when an `AutoProcessor` with `.tokenizer` exists; otherwise an `AutoTokenizer`.
- `processor`: the `AutoProcessor` instance when available; otherwise `None`.

Important behavior:

- `model_name_or_path` and `cache_dir` are expanded with `~` support.
- `auto_device_mapping=True` passes `device_map="auto"` into model loading; otherwise no device map is passed.
- The model receives the caller's `trust_remote_code` value, except the special remote-code registry classes always call their remote class with `trust_remote_code=True`.
- The tokenizer and processor are loaded with `trust_remote_code=True` by the align-anything loader.
- If a processor with `.tokenizer` is found, processor tokenizer padding side and model max length are updated, token embeddings are resized against `processor.tokenizer`, and a model-provided `chat_template` is copied to the processor.
- If no processor exists, the tokenizer embeddings are resized and a model-provided `chat_template` is copied to the tokenizer.
- Default loader dtype is `torch.bfloat16`; the packaged serving CLIs use `torch.float16`.
- Vision/audio/language submodules can be frozen by loader flags. This matters mostly for training, but it also explains why frozen tower parameter flags may appear during inspection.

## Registry routing

`load_pretrained_models` chooses `AnyModel` for normal models and `AnyModelForScore` when `is_reward_model=True`.

### Normal generation registry

| config `model_type` | align-anything class |
|---|---|
| `llama` | `AccustomedLlamaModel` |
| `mllama` | `AccustomedMllamaModel` |
| `llava` | `AccustomedLlavaModel` |
| `llava_next` | `AccustomedLlavaNextModel` |
| `qwen2_audio` | `AccustomedQwen2AudioModel` |
| `chameleon` | `AccustomedChameleonModel` |
| `qwen2_vl` | `AccustomedQwen2VLModel` |
| `qwen2_5_vl` | `AccustomedQwen2_5_VLModel` |
| `modeling_emu3.mllm.modeling_emu3` | `Emu3ForCausalLM` |
| `llava_next_video` | `AccustomedLlavaNextVideoModel` |
| `idefics2` | `AccustomedIdefics2Model` |
| `gemma3` | `AccustomedGemma3Model` |
| `opt` | `AccustomedOPTModel` |
| `qwen2` | `AccustomedQwen2Model` |
| `qwen3` | `AccustomedQwen3Model` |
| `qwen3_moe` | `AccustomedQwen3MoeModel` |

If the config type is not one of the align-anything additions, the registry falls back to Transformers' causal-LM auto mapping.

### Reward-score registry

| config `model_type` | score class |
|---|---|
| `llama` | `AccustomedLlamaRewardModel` |
| `mllama` | `AccustomedMllamaRewardModel` |
| `llava` | `AccustomedLlavaRewardModel` |
| `llava_next` | `AccustomedLlavaNextRewardModel` |
| `qwen2_audio` | `AccustomedQwen2AudioRewardModel` |
| `chameleon` | `AccustomedChameleonRewardModel` |
| `qwen2_vl` | `AccustomedQwen2VLRewardModel` |
| `qwen2_5_vl` | `AccustomedQwen2_5_VLRewardModel` |
| `idefics2` | `AccustomedIdefics2RewardModel` |
| `llava_next_video` | `AccustomedLlavaNextVideoRewardModel` |
| `gemma3` | `AccustomedGemma3RewardModel` |
| `opt` | `AccustomedOPTRewardModel` |
| `qwen2` | `AccustomedQwen2RewardModel` |
| `qwen3` | `AccustomedQwen3RewardModel` |
| `qwen3_moe` | `AccustomedQwen3MoeRewardModel` |

### Remote-code registry

The following `model_type` values are handled by explicit remote-code wrappers. Set `MODEL_NAME_OR_PATH` in the environment before loading them, keep `trust_remote_code=True`, and use a trusted model source.

| config `model_type` | wrapper | notable serving constraints |
|---|---|---|
| `minicpmv` | `AccustomedMiniCPMV` | expects remote MiniCPM-V code; set `ZERO_STAGE=0` unless a launcher already sets it; ZeRO stage 3 is rejected. |
| `minicpmo` | `AccustomedMiniCPMO` | initializes omni components according to `modality` or explicit `auto_model_kwargs`; ZeRO stage 2 is rejected. |
| `baichuan_m1` | `AccustomedBaichuanM1` | uses remote Baichuan model code and a custom chat template wrapper. |

For MiniCPM-O-style omni serving, the packaged CLI passes:

```python
auto_model_kwargs={"init_vision": True, "init_audio": True, "init_tts": True}
```

For registry-driven MiniCPM-O loading without explicit kwargs, pass `modality=["image", "audio"]` to initialize vision and audio; note that the wrapper's `model_additional_kwargs` sets `init_tts=False` in that path.

## Device and dtype selection

`align_anything.utils.device_utils.get_current_device()` chooses the current accelerator in this order: XPU, NPU, MPS, CUDA, then CPU. `LOCAL_RANK` selects the index for XPU/NPU/MPS/CUDA. `get_device_count()` counts XPU/NPU/CUDA devices.

Practical serving choices:

| Case | Recommended loader/device pattern |
|---|---|
| Small text model on one GPU | `dtype=torch.float16`, `auto_device_mapping=False`, then `model.eval().to(get_current_device())`. |
| Large or sharded multimodal model | `dtype=torch.float16` or `torch.bfloat16`, `auto_device_mapping=True`, do not call `.to(device)` afterward. |
| CPU-only smoke load | use `dtype=torch.float32`, `auto_device_mapping=False`, and avoid generation unless the model is tiny. |
| Reward model inspection | `is_reward_model=True`; expect score-head outputs rather than chat/generation interfaces. |
| NPU/XPU/MPS | device utility can select these, but confirm dependency variants and dtype support separately. |

## Packaged CLIs

The serving CLIs are Gradio `ChatInterface` applications. Launch them through the bundled [`../scripts/run_cli_template.sh`](../scripts/run_cli_template.sh) or directly as Python modules.

### Text CLI

Use for text-only chat models or when no processor is required.

```bash
python -m align_anything.serve.text_modal_cli \
  --model_name_or_path "$MODEL_NAME_OR_PATH"
```

Behavior:

- Loads with `dtype=torch.float16` and `trust_remote_code=True`.
- Moves the model to `get_current_device()`.
- Converts prior user/assistant messages into `[{"role": ..., "content": "..."}]`.
- Calls `model.chat(messages=conversation, tokenizer=tokenizer)`.

### Multi-modal CLI

Use for one selected modality: `image`, `audio`, `video`, or limited `text` mode.

```bash
python -m align_anything.serve.multi_modal_cli \
  --model_name_or_path "$MODEL_NAME_OR_PATH" \
  --modality image
```

Behavior:

- Loads with `auto_device_mapping=True` and `dtype=torch.float16`.
- Builds a `ChatTemplate` from the processor; if the model has `apply_chat_template`, that custom formatter is used.
- For uploaded files, creates modality-aware user content and collects media objects separately.
- Generates with `model.generate(**inputs, max_new_tokens=200, temperature=0.2)`.
- Decodes only the new tokens with `processor.decode(...)`.

Choose modality carefully:

| `--modality` | Expected media | Input path |
|---|---|---|
| `image` | image file(s) supported by PIL | `processor(images=..., text=..., return_tensors="pt", padding=True)` |
| `audio` | audio file(s) readable by librosa/soundfile | `processor(audios=..., text=..., sampling_rate=processor.feature_extractor.sampling_rate, ...)` |
| `video` | video file(s) readable by PyAV/FFmpeg | 8 evenly spaced RGB frames, then `processor(videos=..., text=..., ...)` |
| `text` | no files | text-only conversation; file uploads are not supported by this path. |

### Omni-modal CLI

Use for MiniCPM-O-style mixed image/audio/video input in one conversation.

```bash
python -m align_anything.serve.omni_modal_cli \
  --model_name_or_path "$MODEL_NAME_OR_PATH"
```

Behavior:

- Sets `MODEL_NAME_OR_PATH` in the environment.
- Loads with `dtype=torch.float16`, `trust_remote_code=True`, and `auto_model_kwargs={"init_vision": True, "init_audio": True, "init_tts": True}`.
- Moves the model to `get_current_device()`.
- Starts each request with `model.get_sys_prompt(mode="omni", language="en")`.
- Converts file extensions to media inputs: images as PIL images, audio as 16 kHz mono arrays, video as repeated `<unit>`, image frame, audio-chunk triples.
- Calls `model.chat(..., omni_input=True, use_tts_template=True, max_slice_nums=1, use_image_id=False, return_dict=True)` and returns `res.text`.

## Smoke-check workflow

Use the bundled loading checker before launching Gradio:

From this sub-skill directory:

```bash
python scripts/check_model_loading.py \
  --model-name-or-path "$MODEL_NAME_OR_PATH" \
  --preset multi-image \
  --dtype float16 \
  --trust-remote-code \
  --auto-device-mapping
```

Recommended sequence:

1. `--no-load` to verify arguments and imports without downloading weights.
2. Real load with a tiny compatible model or cached target model.
3. Optional `--move-to-current-device` for single-device text/omni patterns only.
4. CLI launch with `run_cli_template.sh` once model loading succeeds.

## Evaluation-backend note

The repository's evaluation docs also support vLLM, DeepSpeed, and Accelerate backends for benchmark generation. That is separate from these Gradio serving CLIs. Use vLLM/DeepSpeed evaluation settings for benchmark throughput; use this sub-skill for interactive model loading and CLI serving.
