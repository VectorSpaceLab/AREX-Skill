---
name: "data-and-multimodal"
description: "Prepare and validate Qwen-VL multimodal JSON datasets, media
  paths, token formatting, and reasoning fields."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Data and Multimodal

Use this sub-skill when the user needs dataset preparation, schema validation, or multimodal path handling for SFT, GRPO, DPO, or classification.

## Covers

- LLaVA-style conversation JSON for SFT and GRPO.
- DPO prompt/chosen/rejected records.
- Classification records with labels and optional prompts.
- Image and video path resolution.
- Reasoning-field rules for supported Qwen model families.
- Basic data validation before training or serving.

## Excludes

- Model loading and weight download.
- SFT/DPO/GRPO/CLS training loops.
- Adapter merge or Gradio serving.

## Read first

- `../../references/data-formats.md` for the shared JSON shapes.
- `../../references/model-compatibility.md` for reasoning and model-family limits.
- `../../references/troubleshooting.md` for common media and schema errors.
- `scripts/validate_dataset.py` for safe local validation.

## Typical user requests

- "Is this JSON compatible with the repo?"
- "How should I format video or image conversations?"
- "Why does reasoning mode reject my samples?"
- "How do I check image paths before training?"

## Workflow

1. Identify the workflow family: SFT/GRPO, DPO, or classification.
2. Check whether the sample uses image or video media.
3. Confirm whether the model family allows reasoning fields.
4. Validate the JSON structure with the bundled validator.
5. Only then hand the data to the training sub-skill.

## Common decision points

- If the user has only text data, image/video keys are optional.
- If the user has video data, keep `fps` and `nframes` mutually exclusive.
- If the user has reasoning-aware samples, do not manually insert `<think>` tags into the answer text.
- If DPO has reasoning on one side only, the pair is invalid.
- If a classification dataset omits `prompt`, the repo inserts a default prompt string.

## Safe command

Use the validator before any CUDA-heavy workflow:

```bash
python scripts/validate_dataset.py dataset.json --mode auto --check-media-paths --image-folder /data/images
```

## What good output looks like

- The validator prints `ok: validated N samples`.
- The dataset contains the keys expected by the target training loop.
- Media paths resolve locally or are explicit URLs.
- Reasoning fields match the target Qwen family.

## If you need more detail

Read `references/workflow.md` for step-by-step validation logic and `references/troubleshooting.md` for the most common failures.
