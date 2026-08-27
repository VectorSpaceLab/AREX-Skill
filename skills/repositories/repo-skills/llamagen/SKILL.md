---
name: llamagen
description: "Router for LlamaGen autoregressive image-generation workflows,
  including tokenizers, data preparation, class-conditional generation, and
  text-conditional generation."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# LlamaGen

Use this skill when the user asks about the LlamaGen repository, its released checkpoints, or its image-generation workflows.

## What this skill owns
- Tokenizer family workflows: VQ, VQGAN, Stable Diffusion VAE, and Consistency Decoder training or reconstruction.
- Preprocessing workflows: discrete-code extraction, T5 feature extraction, OpenImages manifests, and dataset cache layout.
- Class-conditional image generation: c2i training, sampling, serving, and c2i evaluation.
- Text-conditional image generation: t2i stage-1 / stage-2 training, prompt sampling, and t2i evaluation.

## When to route where
- Tokenizer training, finetuning, reconstruction, or code/image round-trip checks -> `sub-skills/tokenizers/`
- Code/T5 cache generation, OpenImages manifests, or dataset-layout questions -> `sub-skills/data-preparation/`
- ImageNet class-conditional generation, serving, packaging, or c2i evaluation -> `sub-skills/class-conditional/`
- Caption-conditioned training, sampling, or t2i evaluation -> `sub-skills/text-conditional/`

## Before you start
- Read `references/repo-provenance.md` to confirm the checkout snapshot.
- Read `references/troubleshooting.md` when the request mentions installs, imports, CUDA, checkpoints, caches, or evaluation dependencies.
- Run `scripts/check_env.py` when you need a quick import and backend smoke before a larger workflow.

## Setup and smoke
- Install the repo baseline with `python -m pip install -r requirements.txt`.
- Install any workflow-specific extras called out by the nearest sub-skill references before sampling, serving, or evaluation.
- Minimal import smoke: `python scripts/check_env.py --repo-root . --skip-cuda`.
- CUDA smoke on a GPU host: `python scripts/check_env.py --repo-root . --with-serving --with-eval --with-gradio`.

## Root guidance
This root skill is a router, not a manual. Read the nearest sub-skill for concrete commands, argument conventions, cache layouts, and troubleshooting.

### Typical selection cues
- VQ / VQGAN / VAE / Consistency Decoder -> tokenizer sub-skill.
- ImageNet code caches or FLAN-T5 features -> data-preparation sub-skill.
- `train_c2i`, `sample_c2i`, `serve_c2i`, `eval c2i` -> class-conditional sub-skill.
- `train_t2i`, `sample_t2i`, `evaluate t2i` -> text-conditional sub-skill.

## Cross-cutting runtime notes
- The repo is source-driven; future agents should rely on the bundled references and scripts rather than the original checkout layout.
- Core workflows are CUDA-oriented. If `torch.cuda.is_available()` is false, the training / generation routes are not ready.
- Evaluation paths depend on extra packages such as TensorFlow, CLIP, and clean-fid; use the bundled troubleshooting notes before assuming a workflow is broken.
- `app.py` is reference-only and should not be treated as a safe import-time runtime helper.

## Useful bundled entry points
- `scripts/check_env.py` for a quick import / CUDA smoke.
- `references/repo-routing-metadata.json` for router placement metadata.
- `references/troubleshooting.md` for cross-cutting install and runtime failures.

## How to think about requests
1. Identify whether the user is asking about tokenizers, preprocessing, c2i, or t2i.
2. Route to the matching sub-skill.
3. Use the sub-skill references for exact flags, layouts, and failure modes.
4. Fall back to the root troubleshooting notes only for cross-cutting issues.
