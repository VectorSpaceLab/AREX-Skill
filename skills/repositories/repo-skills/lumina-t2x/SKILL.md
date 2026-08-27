---
name: lumina-t2x
description: "Routes Lumina-T2X tasks across text-to-image generation, image
  training, audio/music demos, visual anagrams, and ImageNet benchmark
  training."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Lumina-T2X

Lumina-T2X is a family skill for the Alpha-VLLM image, audio, music, and benchmark subprojects in this repository.
Use this root router when the user asks about Lumina-T2I, Lumina-Next-T2I, Lumina-Next-T2I-Mini, compositional generation, text-to-audio, text-to-music, visual anagrams, or the Flag-DiT / Next-DiT ImageNet training branches.

## Quick prerequisites

- CUDA-capable GPU support is required for the model-backed workflows in this repo.
- `flash-attn` is required by the image, audio/music, visual-anagram, and ImageNet model code paths.
- A full CUDA+C++ Apex build is optional, but a Python-only Apex install is a known failure mode.
- The repo has multiple dependency families:
  - core image generation: `pip install -e .`
  - audio extras: `pip install -e ".[audio]"`
  - music extras: `pip install -e ".[music]"`
- For a fast environment sanity check, run `scripts/check_env.py` before any heavy workflow.

## Route map

- `sub-skills/image-generation/SKILL.md`
  - Text-to-image inference, checkpoint conversion, demos, img2img, compositional generation, and SD3-style image generation.
- `sub-skills/image-training/SKILL.md`
  - Lumina-T2I / Lumina-Next-T2I / Lumina-Next-T2I-Mini training, data preparation, resume logic, and DreamBooth-style finetuning.
- `sub-skills/audio-music/SKILL.md`
  - Text-to-audio and text-to-music demos, checkpoint layout, structure-caption setup, and config editing.
- `sub-skills/visual-anagrams/SKILL.md`
  - Optical-illusion generation, view selection, animation, and metadata handling.
- `sub-skills/imagenet-training/SKILL.md`
  - Flag-DiT, Next-DiT, and Next-DiT-MoE ImageNet training and sampling.

## Read next

- `references/repo-provenance.md` when checking whether this skill matches the current checkout.
- `references/troubleshooting.md` for shared install, backend, and checkpoint failures.
- `references/overview.md` for the compact repo family map.
- `scripts/check_env.py` when you need a safe dependency and backend probe.

## Common navigation hints

- If the request mentions `lumina` or `lumina_next`, start with `image-generation` or `image-training`.
- If the request mentions `demo_audio.py`, `demo_music.py`, or structure captions, start with `audio-music`.
- If the request mentions `generate.py`, `views`, `animate.py`, or illusion metadata, start with `visual-anagrams`.
- If the request mentions `ImageNet`, `FSDP`, `srun`, `torchrun`, or `run_8gpus.sh`, start with `imagenet-training`.
