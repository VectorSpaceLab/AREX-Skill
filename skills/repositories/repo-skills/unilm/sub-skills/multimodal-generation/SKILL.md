---
name: multimodal-generation
description: "Use UniLM Kosmos, TextDiffuser, WavLM, BEATs, SpeechT5, SpeechLM,
  VALL-E, and LatentLM for safe multimodal generation, OCR/markdown, audio, and
  latent diffusion workflow planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Multimodal Generation

Use this sub-skill when a task names Kosmos, Kosmos-2.5, TextDiffuser, TextDiffuser-2, WavLM, BEATs, SpeechT5, SpeechLM, VALL-E, or LatentLM, or when the request is about open-ended image/text generation, grounded multimodal generation, literate OCR/markdown generation, audio representation extraction, speech generation, or latent diffusion sampling/evaluation.

## Route Here

- Validate or plan Kosmos-2 grounded image-text generation, phrase grounding, captioning, VQA, GRIT-style data preparation, or fairseq generation commands.
- Validate or plan Kosmos-2.5 OCR and image-to-markdown inference with `--do_ocr` or `--do_md`, local image/checkpoint inputs, optional aspect-ratio preprocessing, and OCR bounding-box visualization.
- Choose TextDiffuser v1 text-to-image, template-conditioned generation, text inpainting, MARIO-Eval sampling, or TextDiffuser-2 full/LoRA/inpainting command shapes.
- Plan WavLM, BEATs, SpeechT5, SpeechLM, or VALL-E audio/speech workflows, including checkpoint loading, 16 kHz audio assumptions, fairseq manifests, TTS/VC generation, and reference-only zero-shot TTS notes.
- Validate LatentLM sampling, many-sample generation, training, or FID evaluation inputs, including checkpoint layout, VAE, ImageFolder/Hugging Face dataset choices, and reference-stat requirements.

## Route Elsewhere

- Use `vision-document-ai` for LayoutLM, LayoutLMv2/v3, LayoutXLM, MarkupLM, XDoc, DiT, TrOCR, BEiT, VLMo, or document OCR/layout tasks unless the request specifically names Kosmos-2.5 literate OCR or image-to-markdown.
- Use `embeddings-retrieval` for E5, SimLM, dense retrieval, reranking, hard-negative mining, or text embedding evaluation.
- Use `architectures-training` for architecture-only training mechanics, long-context models, optimizer schedules, TorchScale/DeepNet/Magneto internals, or Deepspeed/Apex mechanics not tied to these multimodal workflows.

## Read Or Run

- Read [references/workflows.md](references/workflows.md) to select the right model family and construct safe command templates for Kosmos, TextDiffuser, audio/speech, or LatentLM tasks.
- Read [references/input-checklists.md](references/input-checklists.md) before any native run to confirm required images, prompts, checkpoints, audio manifests, datasets, and outputs.
- Read [references/troubleshooting.md](references/troubleshooting.md) when checkpoints, tokenizers, CUDA/FlashAttention/xformers, fairseq, Hugging Face, audio sample rates, or LatentLM FID inputs fail.
- Run [scripts/check_multimodal_inputs.py](scripts/check_multimodal_inputs.py) to validate mode-specific local arguments and print a safe run checklist without importing heavy frameworks, downloading, or launching generation.

## Safe Default Workflow

1. Classify the request by family: Kosmos grounding/OCR, TextDiffuser text rendering, audio/speech representation or generation, or LatentLM latent diffusion.
2. Use the references to pick the native entry-point shape and required inputs; keep original inference/training scripts reference-only until the user confirms data, checkpoints, dependencies, network access, GPU readiness, and output location.
3. Run the bundled checker in the closest mode to catch missing local files and unsafe assumptions before constructing a native command.
4. If the checker passes, present the command as a template to run from a user-provided compatible source checkout and environment, not from this skill directory.
5. Prefer small validation or `--help` checks before long generation, distributed training, downloads, remote demos, or metric evaluation.
