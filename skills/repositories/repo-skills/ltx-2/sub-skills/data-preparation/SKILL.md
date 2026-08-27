---
name: data-preparation
description: "Prepares LTX training datasets by validating manifests, drafting
  scene-splitting and preprocessing commands, and checking cached latents,
  captions, references, and masks before training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Data Preparation

Use this sub-skill when the request is about getting LTX training data into a safe, trainable shape: manifest validation, scene splitting, caption planning, preprocessing command drafting, reference or mask prep, and inspection of cached `.precomputed` outputs.

## Route away

- Training mode selection, config authoring, launch, resume, or monitoring → `../training-workflows/SKILL.md`
- Inference or validation with trained LoRAs → `../inference-pipelines/SKILL.md`
- GPU / VRAM / OOM / backend tuning → `../performance-backends/SKILL.md`

## Fast paths

- Validate or normalize a manifest: `scripts/validate_dataset_manifest.py`
- Draft a preprocessing command: `scripts/build_preprocess_command.py`
- Run the bundled preprocessing launcher after approval: `scripts/process_dataset.py`
- Draft a scene-splitting command: `scripts/build_scene_split_command.py`
- Run the bundled scene splitter after approval: `scripts/split_scenes.py`
- Inspect precomputed latents and masks: `scripts/inspect_precomputed_latents.py`
- Use the bundled preprocessing internals only when you need to inspect or reuse them directly: `scripts/process_videos.py`, `scripts/process_captions.py`, and `scripts/decode_latents.py`

## What this sub-skill covers

- CSV, JSON, and JSONL manifests with caption, media, reference, and mask columns.
- Resolution buckets and audio-duration rules for video, image, mixed, and audio-only datasets.
- Unified versus split checkpoint preprocessing flags.
- Captioning backend choice, credential boundaries, and spot-check approval.
- Reference and mask preprocessing layouts for IC-LoRA and inpainting.
- Safe checks for stale or mismatched cached outputs.

## Working rules

- Do not start captioner servers, split videos, encode media, or download models here.
- Use the bundled scripts to validate inputs and draft commands; they are safe to run from any current directory.
- Prefer a fresh `.precomputed/` directory when the model, Gemma root, trigger token, bucket list, or reference scale factors change.
- For mixed image + video datasets, plan multiple buckets that include `F=1`; the later training step must use batch size 1.
- For IC-LoRA, inpainting, and audio-only datasets, require the corresponding reference or audio inputs before preprocessing.

## Read next

- `references/dataset-formats.md`
- `references/captioning-and-preprocessing.md`
- `references/reference-and-mask-prep.md`
- `references/troubleshooting.md`
