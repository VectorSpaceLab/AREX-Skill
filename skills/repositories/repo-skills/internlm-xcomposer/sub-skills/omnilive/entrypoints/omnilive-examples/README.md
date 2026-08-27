# Bundled OmniLive Local Entrypoints

This directory contains argumentized, source-derived entrypoints for local OmniLive workflows. They no longer require the original source checkout; they operate on a user-provided local model root containing `audio/`, `base/`, `adapter/`, `memory/`, and optionally `merge_lora/`.

## Contents

- `infer_audio.py` / `run_audio_asr.sh` — audio ASR or classification through the `audio/` component.
- `infer_llm_base.py` / `run_base_vlm.sh` — base image VLM chat through the `base/` component.
- `merge_lora.py` / `run_merge_lora.sh` — PEFT merge from `base/` + `adapter/` into `merge_lora/`.
- `infer_llm_with_memory.py` / `run_memory_qa.sh` — memory-backed video QA using `merge_lora/` and `memory/`.

## Preflight

From the OmniLive sub-skill root, run the layout checker before the entrypoints:

```bash
python scripts/check_omnilive_layout.py /models/internlm-xcomposer2d5-ol-7b --workflow memory --require-weights
```

## Examples

```bash
# Audio ASR.
IXC_OMNILIVE_MODEL_ROOT=/models/internlm-xcomposer2d5-ol-7b ./run_audio_asr.sh --audio /data/chinese.mp3 --task asr

# Base VLM image QA.
IXC_OMNILIVE_MODEL_ROOT=/models/internlm-xcomposer2d5-ol-7b ./run_base_vlm.sh --image /data/dubai.png --question "Analyze the image."

# Merge base+adapter before memory QA.
IXC_OMNILIVE_MODEL_ROOT=/models/internlm-xcomposer2d5-ol-7b ./run_merge_lora.sh

# Memory video QA.
IXC_OMNILIVE_MODEL_ROOT=/models/internlm-xcomposer2d5-ol-7b ./run_memory_qa.sh --video-path /data/needle_32.mp4 --max-frame 16 --vs-thresh 0.35 --question "What does the hand do?"
```

All commands are real entrypoints and may allocate CUDA memory or load large checkpoints when executed.
