---
name: "inference"
description: "Routes direct LightX2V generation and model-preparation workflows
  that start from `LightX2VPipeline` or `python -m lightx2v.infer`."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Inference

Use this sub-skill for direct LightX2V generation or model-preparation requests that do not go through the HTTP server or the disaggregated deployment stack.

## Typical triggers

- "generate a video with LightX2V"
- "how do I call `LightX2VPipeline`?"
- "which `model_cls` and `task` should I use?"
- "how do I enable offload, parallelism, LoRA, or quantized checkpoints?"
- "what model directory layout does Wan / Qwen Image / HunyuanVideo / LTX / MiniMax-H3 / WorldMirror expect?"

## Read first

- [`references/workflows.md`](references/workflows.md) for the end-to-end generation flow and the main configuration knobs.
- [`references/model-families.md`](references/model-families.md) for the model-class and task matrix.
- [`references/troubleshooting.md`](references/troubleshooting.md) for invalid model/task combinations, missing files, and optional backend issues.
- [`scripts/check_model_request.py`](scripts/check_model_request.py) when you want to validate a request without running generation.
- [`../../references/troubleshooting.md`](../../references/troubleshooting.md) for cross-cutting package and environment failures.

## What belongs here

Include:
- `lightx2v.infer`
- `LightX2VPipeline`
- `create_generator()` / `generate()` / `enable_offload()` / `enable_quantize()` / `enable_parallel()` / `enable_lightvae()`
- prompt-only, image-conditioned, video-conditioned, audio-conditioned, reconstruction, and super-resolution generation
- model-path layout and `config_json` selection
- LoRA loading or LoRA-backed inference paths
- quantized or distilled inference configuration
- family-specific request shaping such as WorldMirror, WorldPlay, LTX, MiniMax-H3, or Qwen Image

Exclude or route elsewhere:
- HTTP server and queue management → `sub-skills/serving/`
- controller/encoder/transformer/decoder deployment → `sub-skills/disagg/`
- weight conversion and LoRA surgery → `sub-skills/conversion/`
- training workflows → out of scope for this skill graph

## Safe starting checks

- `python scripts/check_install.py`
- `python sub-skills/inference/scripts/check_model_request.py --help`
- `python -m lightx2v.infer --help`
- `python - <<'PY'\nfrom lightx2v import LightX2VPipeline\nprint(LightX2VPipeline)\nPY`

Use the bundled request checker before trying a real model run if the task is mostly about argument shape or config resolution.

## Guidance style

Prefer concrete instructions over model-family guesses:
- name the `model_cls`, `task`, and any family-specific path overrides
- state whether the workflow is prompt-only, image-conditioned, video-conditioned, audio-conditioned, reconstruction, or SR
- say which optional knobs matter: `offload`, `parallel`, `quantize`, `lightvae`, `lora_configs`, or family-specific checkpoint fields
- mention when a family expects a special directory layout or a specific `config.json`

## Decision points

When helping with a direct run, decide these items explicitly:
- family first: Wan, Qwen Image, HunyuanVideo, LTX, MiniMax-H3, WorldMirror, WorldPlay, SeedVR, or a smaller family such as ERNIE / Z-Image / Flux2 / Cosmos3 / Bagel / SenseNova-Vision / LongCat / Neopp / Motus / LingBot / FastWAM / InfiniteTalk / DreamZero
- task second: prompt-only, image-conditioned, audio-conditioned, reconstruction, or super-resolution
- path third: whether the model root already contains the needed `config.json`, `transformer` subtree, or specialized branch files
- optimization fourth: whether offload, parallelism, quantization, or LoRA loading is actually needed for the user’s target hardware
- output fifth: whether the request should save a file, return an in-memory tensor, or just validate the request shape

Common user-facing reminders:
- a CPU import check is not proof that a CUDA-generation path is ready
- families with split branches or special subfolders need their path layout called out explicitly
- `check_model_request.py` is the safe way to reason about the config before a real run
- `workflows.md` should be the default reference when the user needs the full generation sequence

## What a good answer should contain

For a future agent, a strong answer from this route should usually include:
- the chosen family and task
- the key path or config files that matter
- the optional optimization knobs that are relevant, if any
- the output path or output type the user should expect
- any family-specific warning about layout, checkpoints, or extra inputs

When a request spans both inference and serving, answer the inference part here and then cross-read the serving sub-skill for the API side.
