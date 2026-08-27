---
name: evaluation-conversion
description: "Build OpenCLIP zero-shot and retrieval evaluation flows, diagnose
  checkpoint state dicts, and route conversion or Hugging Face export work
  across model families."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Evaluation and Conversion

Use this sub-skill when an OpenCLIP task is about zero-shot classifier construction, ImageNet zero-shot evaluation, paired retrieval metrics, checkpoint key diagnosis, third-party state-dict conversion, or Hugging Face export/push planning.

## Route First

- Use this sub-skill for `build_zero_shot_classifier`, `open_clip_train.zero_shot.zero_shot_eval`, `run_zero_shot_classifier`, retrieval metric knobs, `open_clip.factory.load_state_dict/load_checkpoint`, `open_clip.convert`, `open_clip.naflex_convert`, and `open_clip.push_to_hf_hub` helpers.
- Route embedding extraction, image preprocessing, tokenizer choice, and single-model inference setup to `../model-inference/SKILL.md` before applying classifier or retrieval metrics.
- Route CLAP/NaFlexClap audio transforms, Hugging Face audio dataset zero-shot details, and Transformers CLAP checkpoint conversion depth to `../audio-clap/SKILL.md`.
- Route GenLIP/GenLAP generative scoring, caption-loss evaluation, and prefix-LM classification alternatives to `../naflex-generative/SKILL.md`.
- Route optimizer resume, training-loop checkpoint cadence, distributed launch mechanics, and long-running training validation to `../training/SKILL.md`.

## Quick Start

1. Validate a no-download zero-shot classifier path with a tiny fake text model:

   ```bash
   python sub-skills/evaluation-conversion/scripts/zero_shot_classifier_smoke.py
   ```

2. Inspect a local checkpoint before loading it into an inference/export model:

   ```bash
   python sub-skills/evaluation-conversion/scripts/checkpoint_key_report.py /path/to/checkpoint.pt --prefer-ema
   ```

3. If a model config is available locally, compare checkpoint keys against random-initialized model keys without downloading weights:

   ```bash
   python sub-skills/evaluation-conversion/scripts/checkpoint_key_report.py /path/to/checkpoint.pt --model ViT-B-32 --prefer-ema --max-missing 20
   ```

## Evaluation Contracts

- `build_zero_shot_classifier(model, tokenizer, classnames, templates, num_classes_per_batch=10, device="cpu", use_tqdm=False)` builds normalized text-classifier weights shaped `[embed_dim, num_classes]` from contrastive text features.
- ImageNet zero-shot evaluation is image-only. It requires an image model with `visual` and `encode_image`; it also requires `encode_text`, so generative image models such as GenLIP skip this contrastive path.
- `zero_shot_eval` accepts bare models, DDP-like wrappers, compiled modules, or `TrainingTask` wrappers; unwrapping happens only for capability checks while classifier/eval calls still receive the original model-or-task object.
- FSDP zero-shot needs all ranks to participate in classifier construction and evaluation. Non-rank workers use a task `create_dummy_batch` when available, and NaFlex FSDP eval should use the task interface.
- Retrieval metrics are paired image/audio-to-text ranks from already-generated feature tensors or feature chunks; generate features with the model-inference or audio-clap sub-skill first.

## Conversion and Export Contracts

- OpenCLIP checkpoint loading defaults to `weights_only=True`; do not set unsafe pickle loading unless the user explicitly accepts the risk and the checkpoint is trusted.
- Raw inference checkpoints can be flat state dicts or nested under `state_dict`; training checkpoints may also include `state_dict_ema`, optimizer, scaler, epoch, and counters.
- For inference/export, prefer EMA weights when the training task maintained EMA; otherwise use the main `state_dict`. Use the key-report helper to identify which payloads exist before choosing.
- Conversion helpers cover big_vision SigLIP `.npz`, MobileCLIP key mapping, NaFlex timm/native ViT state-dict conversion, scalar shape reconciliation, and HF Hub packaging. Audio-specific HF CLAP conversion is routed to `../audio-clap/SKILL.md`.
- Hugging Face push helpers require credentials and network access. Treat `push_to_hf_hub` and `push_pretrained_to_hf_hub` as an explicit side-effecting step after local config/weights checks pass.

## References

- `references/evaluation.md` — zero-shot classifier construction, ImageNet zero-shot restrictions, FSDP/NaFlex behavior, and routing for audio/generative alternatives.
- `references/retrieval-metrics.md` — paired retrieval metric inputs, chunking, precision/device options, and common memory trade-offs.
- `references/conversion-and-export.md` — checkpoint payload selection, key-prefix diagnosis, conversion helpers, pretrained registry checks, and HF export/push workflow.
- `references/troubleshooting.md` — failures for incompatible model families, wrapped models, retrieval OOM, state-dict mismatch, unsafe checkpoints, and HF auth/network issues.

## Safe Helpers

- `scripts/zero_shot_classifier_smoke.py` constructs classifier weights using fake class names/templates and a tiny deterministic text module; it does not download weights, read datasets, or require OpenCLIP installed.
- `scripts/checkpoint_key_report.py` loads a local `.pt`/`.pth`/`.bin` checkpoint on CPU with `weights_only=True` by default, reports nested payloads and prefix patterns, and optionally compares against a random uninitialized OpenCLIP model without downloading weights.
