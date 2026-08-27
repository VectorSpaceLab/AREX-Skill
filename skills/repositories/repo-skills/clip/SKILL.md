---
name: clip
description: "Use OpenAI CLIP for zero-shot image-text inference, prompt
  engineering, feature extraction, and responsible evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# CLIP

Use this skill when a task involves OpenAI CLIP: zero-shot image classification, image-text similarity, prompt template design, tokenization, CLIP image/text embeddings, linear-probe evaluation, or troubleshooting CLIP model loading.

## Fast Route

- For model names, `clip.load`, preprocessing, image-text logits, local checkpoints, JIT/device choices, and cache/download behavior, read [model-loading-inference](sub-skills/model-loading-inference/).
- For class-name prompt templates, `clip.tokenize`, context-length failures, zero-shot classifier weights, and prompt ensembling, read [prompt-engineering](sub-skills/prompt-engineering/).
- For batch image/text feature extraction, `.npz` embedding outputs, similarity/search prototypes, linear probes, and responsible evaluation limits, read [feature-evaluation](sub-skills/feature-evaluation/).
- For package-wide install/import, dependency, checkpoint download, dataset, and safety issues, read [references/troubleshooting.md](references/troubleshooting.md).
- For a no-download runtime check, run `python scripts/validate_clip_runtime.py --json`.

## Use This Skill When

- The user names `clip`, OpenAI CLIP, `ViT-B/32`, `RN50`, `clip.load`, `clip.tokenize`, `encode_image`, or `encode_text`.
- The task asks for zero-shot image classification, image-to-text ranking, image/text embedding extraction, CLIP feature caching, or CLIP linear-probe evaluation.
- The task mentions prompt templates for vision-language classification, prompt ensembling, class taxonomy design, or CLIP context length 77.
- The task has errors involving CLIP checkpoint downloads, checksum/cache problems, CPU/CUDA tensor placement, TorchScript/JIT loading, or overlong tokenized text.

## Avoid This Skill When

- The user is using OpenCLIP, Hugging Face `transformers.CLIPModel`, SigLIP, BLIP, or another CLIP-like implementation rather than this package.
- The user wants to train CLIP from scratch; this repository primarily exposes released model loading, inference, feature extraction, and evaluation examples.
- The request is about deploying CLIP in production, surveillance, facial recognition, or sensitive demographic classification without explicit research-only framing and safety review.
- The task is a general PyTorch, torchvision, or image-classification issue with no CLIP-specific API, model, tokenizer, or prompt signal.

## Minimal Setup Pattern

Install PyTorch/torchvision first using the wheel or conda variant appropriate for the user's CPU/CUDA environment, then install CLIP and its lightweight text/tokenizer dependencies:

```bash
pip install ftfy regex tqdm
pip install git+https://github.com/openai/CLIP.git
```

Run a no-download import/tokenizer check before any checkpoint download:

```bash
python scripts/validate_clip_runtime.py --json
```

A healthy runtime imports `clip`, lists the nine released model names, tokenizes sample text to shape `[n, 77]`, and reports that no checkpoint downloads were attempted.

## Checkpoint and Dataset Policy

- `clip.load("ViT-B/32")` and other named models may download checkpoints if they are not cached; ask before triggering downloads in restricted, offline, or expensive environments.
- Use `download_root=` to point CLIP at a cache, or pass a local checkpoint path as `name` for strict offline workflows.
- README examples using CIFAR100 and dataset docs for Country211, Rendered SST2, and YFCC100M require network and potentially large downloads; treat them as opt-in verification or evaluation evidence, not default skill actions.
- The native JIT/eager consistency test can download every available model, so run it only when checkpoint downloads and time budget are explicitly allowed.

## Core API Facts

- `clip.available_models()` returns the released model names: `RN50`, `RN101`, `RN50x4`, `RN50x16`, `RN50x64`, `ViT-B/32`, `ViT-B/16`, `ViT-L/14`, and `ViT-L/14@336px`.
- `clip.load(name, device=..., jit=False, download_root=None)` returns `(model, preprocess)` for a named model or local checkpoint path.
- `clip.tokenize(texts, context_length=77, truncate=False)` returns a `[number_of_texts, context_length]` token tensor and raises on overlong prompts unless `truncate=True`.
- Loaded models expose `encode_image(image)`, `encode_text(text)`, and `model(image, text)`; the forward call returns image/text logit matrices derived from normalized cosine similarities.

## Responsible Use

CLIP was released as a research model for studying robustness and zero-shot transfer. Model-card evidence warns that performance depends strongly on class taxonomy and prompts, that the model is English-oriented, and that deployment, surveillance, facial recognition, and sensitive demographic classification are out of scope without careful task-specific testing and safety review. Route evaluation and safety questions through [feature-evaluation responsible guidance](sub-skills/feature-evaluation/references/responsible-evaluation.md).
