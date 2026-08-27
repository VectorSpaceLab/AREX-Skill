---
name: dalle-pytorch
description: "Operate lucidrains DALLE-pytorch for DALL-E style VAE training,
  transformer training, generation, CLIP ranking, and backend troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# DALLE-pytorch operating skill

Use this skill when the task is about the `dalle-pytorch` / DALLE-pytorch package: DALL-E style text-to-image transformer modeling, discrete VAE codebooks, CLIP ranking, image/text training data, generation checkpoints, sparse attention, DeepSpeed, Horovod, Apex, or the package's training/generation helper surfaces.

## First checks

1. Confirm the user wants DALLE-pytorch, not DALL-E 2 or a diffusion package.
2. Check whether they are using a pip install, a local checkout, or only asking for API guidance. The published package exports `DiscreteVAE`, `DALLE`, `CLIP`, `OpenAIDiscreteVAE`, and `VQGanVAE`; the historical training/generation helpers were top-level repo scripts, not package console entry points.
3. Run the bundled install/API smoke when behavior matters:

```bash
python scripts/check_dalle_pytorch_install.py
```

Read `references/api-reference.md` for public signatures and object relationships. Read `references/troubleshooting.md` before fixing install/import, torch, VAE download, checkpoint, or backend failures.

## Route by task

| User task | Read next | Why |
| --- | --- | --- |
| Train or debug a discrete VAE, choose OpenAI/VQGAN/custom VAE, inspect VAE checkpoint contents, or create a VAE command | `sub-skills/vae-training/SKILL.md` | Owns `DiscreteVAE`, VAE checkpoints, image-folder training, VAE alternatives, and VAE-specific failures. |
| Train/resume the DALL-E transformer, validate image-text folders, use WebDataset shards, choose tokenizer flags, or understand DALL-E checkpoint payloads | `sub-skills/dalle-training/SKILL.md` | Owns transformer training, data layout, tokenizer choices, checkpoint/resume paths, and data validators. |
| Generate images/text, split prompts, prime from an image crop, use CLIP ranking, or debug generation checkpoints | `sub-skills/generation-and-ranking/SKILL.md` | Owns `generate_images`, `generate_texts`, `CLIP`, prompt/output layout, and generation troubleshooting. |
| Decide on DeepSpeed/Horovod/Apex/Docker/CUDA, sparse attention, `--distributed_backend`, or optional backend installation | `sub-skills/distributed-and-backends/SKILL.md` | Owns distributed wrappers, backend availability checks, attention variants, Docker and source-build caveats. |

## Safe operating boundaries

- Treat full training and generation as GPU/side-effect workflows. The original helpers call `.cuda()`, write checkpoints or outputs, and may log to W&B. Use bundled command builders and validators first; run long jobs only after the user approves compute, data, checkpoint, and logging side effects.
- Do not instantiate `OpenAIDiscreteVAE` blindly on modern torch. The source asserts `torch <= 1.10`; with newer torch the class fails before downloading weights.
- Do not trigger default OpenAI VAE or VQGAN downloads unless the user wants model-cache/network side effects.
- DeepSpeed sparse attention, Apex AMP, Horovod, and Docker GPU builds require machine-specific CUDA/toolchain decisions. Route those to `distributed-and-backends` instead of installing broad extras.
- When a user has only a pip install, prefer API recipes and bundled validators. When they have a checkout containing the historical scripts, bundled command builders can produce matching commands without requiring this skill to link back to source files.

## Quick package smoke

Use this for a fast sanity check:

```bash
python scripts/check_dalle_pytorch_install.py --include-cuda
```

Expected high-level signal:

- package metadata and `dalle_pytorch` import succeed;
- `DiscreteVAE`, `DALLE`, `CLIP`, tokenizer, and data helper signatures are visible;
- a tiny CPU `DiscreteVAE`/`DALLE`/`CLIP` smoke passes;
- optional CUDA availability is reported without running training.

## Key facts to remember

- Distribution name: `dalle-pytorch`; import root: `dalle_pytorch`; version baseline: `1.6.6`.
- `DiscreteVAE` can be trained directly or loaded as a checkpoint payload containing `hparams` and `weights`.
- `DALLE` freezes the VAE, predicts text and image tokens, and can generate images autoregressively with optional classifier-free `cond_scale`.
- Image-text folder training pairs image files and `.txt` files by matching stem recursively; each text file may contain multiple newline-separated captions.
- WebDataset training expects `--wds <image_key>,<caption_key>` and an image-text folder argument that points to a tar, shard folder, URL brace pattern, or GCS path.
- CLI helpers are checkout scripts. This skill bundles safe command builders and API smokes instead of copying long CUDA/W&B training scripts.

## References

- `references/api-reference.md`: public signatures, outputs, and model relationships.
- `references/troubleshooting.md`: cross-cutting install/import/backend/checkpoint issues.
- `references/repo-provenance.md`: source commit and evidence paths for refresh decisions.
- `references/repo-routing-metadata.json`: structured router metadata for managed imports.
