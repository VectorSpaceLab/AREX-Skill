---
name: model-inference
description: "Load OpenCLIP, CLIP-style, and CoCa models for safe inference,
  tokenizer/preprocess setup, embeddings, and local or Hugging Face checkpoint
  routing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Model Inference

Use this sub-skill when an agent needs to instantiate OpenCLIP models, select a pretrained tag or checkpoint source, prepare image/text inputs, create embeddings, or inspect model/tokenizer/preprocess configuration.

## Route Here

- Load a built-in model by name with `open_clip.create_model`, `open_clip.create_model_and_transforms`, or `open_clip.create_model_from_pretrained`.
- Choose between random-init (`pretrained=None`), a named pretrained tag, a local checkpoint file, `hf-hub:org/repo`, or `local-dir:/path` model identifiers.
- Build tokenizer and image preprocess transforms with `open_clip.get_tokenizer`, `open_clip.tokenize`, `open_clip.image_transform`, or model-derived preprocess config.
- Run `encode_image`, `encode_text`, `model(image=..., text=...)`, or CoCa feature/generation calls safely in eval/no-grad mode.
- Diagnose model loading, tokenizer, QuickGELU, optional dependency, device/precision, cache, and local-dir config failures.

## Read First

- `references/workflows.md` for no-download inference, pretrained/HF/local loading, embeddings, CoCa caveats, and inspection recipes.
- `references/api-reference.md` for signatures, accepted identifier schemas, return contracts, and output shapes.
- `references/model-selection.md` for model/tag selection, QuickGELU compatibility, tokenizer choice, and local/HF checkpoint guidance.
- `references/troubleshooting.md` for common failures and precise fixes.
- `scripts/inference_smoke.py` for a deterministic helper that checks model creation, tokenizer, preprocess, and finite embeddings without downloads by default.

## Quick Start

```bash
python sub-skills/model-inference/scripts/inference_smoke.py --model ViT-B-32 --pretrained none --device cpu
```

The smoke script defaults to `pretrained=None`, uses a generated image, and performs shape/finite checks only. Passing a named pretrained tag or `hf-hub:` model can trigger network/cache access; use those only when downloads are explicitly intended.

## Boundaries

- Training loops, dataset ingestion, losses, EMA/FSDP, and checkpoint resume belong in `../training/SKILL.md`.
- CLAP audio inputs and audio zero-shot workflows belong in `../audio-clap/SKILL.md`.
- NaFlex patch dictionaries, GenLIP, and GenLAP workflows belong in `../naflex-generative/SKILL.md`.
- Zero-shot classifier construction, retrieval scoring pipelines, checkpoint conversion, and export belong in `../evaluation-conversion/SKILL.md`.
