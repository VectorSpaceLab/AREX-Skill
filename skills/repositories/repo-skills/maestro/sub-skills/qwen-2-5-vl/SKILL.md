---
name: qwen-2-5-vl
description: "Route Qwen2.5-VL JSON extraction and COCO object-detection
  fine-tuning, inference, conversation formatting, pixel controls, and
  troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Qwen2.5-VL

Use this sub-skill for Qwen2.5-VL workflows that need Maestro's Qwen-specific training, loading, inference, or detection-format helpers.

## Route here when

- You need `maestro qwen_2_5_vl train`, `load_model`, `save_model`, `predict`, or the Qwen collators.
- You need to format a Qwen chat conversation with `system_message`, an image turn, and a prefix/suffix pair.
- You need Qwen detection JSON suffixes, `min_pixels` / `max_pixels`, or LoRA / QLoRA / none configuration.
- You need a safe config builder or formatter smoke for this model family.
- You need Qwen-specific troubleshooting for prompt formatting, pixel sizing, or `qwen-vl-utils` compatibility.

## Route away when

- The task is about JSONL / COCO dataset layout, Roboflow identifiers, generic metrics, split validation, or loader helpers; use [datasets-and-metrics](../datasets-and-metrics/).
- The task is Florence-2 or PaliGemma 2; use the sibling sub-skill for that model.

## Defaults and invariants

- Model ID: `Qwen/Qwen2.5-VL-3B-Instruct`
- Revision: `refs/heads/main`
- Learning rate: `2e-4`
- Optimisation strategies: `lora`, `qlora`, `none`
- Default pixel bounds: `min_pixels=256*28*28`, `max_pixels=1280*28*28`
- Max new tokens: `1024`
- The source recipes often override `min_pixels` to `512*28*28` for object detection; keep train, load, inference, and parsing bounds aligned.

## Prompt and chat handling

- `format_conversation(...)` inserts an optional system message first, then the image plus user prefix, then an optional assistant suffix for supervised training.
- `processor.apply_chat_template(...)` renders that message list into the model prompt string.
- `predict(...)` adds a generation prompt before generation so the model completes the assistant turn.
- Use the same `system_message` in training and inference when you want stable output formatting.
- Generic data layout, metrics, and COCO / JSONL wiring live in the sibling dataset skill; this sub-skill owns the Qwen-specific prompt, resize, and detection formatting logic.

## Bundled assets

- `references/api-reference.md`
- `references/workflows.md`
- `references/detection-formats.md`
- `references/troubleshooting.md`
- `scripts/smoke_qwen_detection_format.py`
- `scripts/build_qwen_config.py`

## Safe checks

- `python scripts/smoke_qwen_detection_format.py`
- `python scripts/build_qwen_config.py --help`
- `python scripts/build_qwen_config.py --emit cli --dataset /path/to/dataset`

## Notes

- Keep `qwen-vl-utils` pinned to `0.0.8` if `smart_resize(...)` starts failing against newer releases.
- Do not route dataset or metric questions here unless the Qwen-specific prompt or detection format is the real issue.
