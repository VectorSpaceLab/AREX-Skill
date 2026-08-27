---
name: tokenizers
description: "Router for VQ, VQGAN, Stable Diffusion VAE, and Consistency
  Decoder tokenizer training, finetuning, reconstruction, and round-trip
  checks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Tokenizers

Use this sub-skill for image-tokenizer work that stays inside tokenizer and reconstruction behavior.

## Owns
- VQ tokenizer training and finetuning.
- Reconstruction through VQ, VQGAN, Stable Diffusion VAE, and Consistency Decoder checkpoints.
- Image/code round-trip sanity checks for saved tokenizer codes.
- Legacy checkpoint migration notes for VQGAN `.ckpt` to `.pth` conversion.

## Routes out
- Code extraction, dataset cache prep, and other preprocessing -> `data-preparation`.
- Class-conditional generation, sampling, serving, and evaluation -> `class-conditional`.
- Text-conditional generation and evaluation -> `text-conditional`.
- Checkpoint publishing and remote mutation -> excluded.

## Best entry points
- Training: `scripts/train_vq.sh`, `scripts/train_vq_finetune.sh`, `scripts/train_vq_finetune_continue.sh`
- VQ reconstruction: `scripts/reconstruct_vq.sh`
- VQ validation / input sanity: `scripts/validate_vq.sh`
- VQGAN reconstruction: `scripts/reconstruct_vqgan.sh`
- Stable Diffusion VAE reconstruction: `scripts/reconstruct_vae.sh`
- Consistency Decoder reconstruction: `scripts/reconstruct_consistency_decoder.sh`
- Code/image round trip: `scripts/check_image_codes.py`

## Read before answering
- `references/workflows.md`
- `references/cli-reference.md`
- `references/checkpoints.md`
- `references/troubleshooting.md`

## Fast routing rules
- If the request mentions code extraction, T5 extraction, or dataset cache layout, send it to `data-preparation`.
- If it asks for c2i or t2i generation, send it to the generation sub-skill instead of this one.
- If a checkpoint decode fails, first check the model family, codebook size, image size, and `pretrained_models` or diffusers layout.
