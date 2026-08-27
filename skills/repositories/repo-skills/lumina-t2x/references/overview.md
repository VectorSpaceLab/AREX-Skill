# Lumina-T2X Overview

## Purpose

This reference gives a compact family map for the repository so future agents can route quickly before opening deeper workflow notes.

## Repository families

| Family | Main directories | Typical user intent | Primary outputs |
| --- | --- | --- | --- |
| Image generation | `lumina_t2i/`, `lumina_next_t2i/`, `lumina_next_t2i_mini/`, `lumina_next_compositional_generation/` | generate images, convert checkpoints, launch demos, run img2img or SD3-style inference | PNGs, demo UI, converted checkpoints |
| Image training | `lumina_t2i/train.py`, `lumina_next_t2i/train.py`, `lumina_next_t2i_mini/train.py`, `lumina_next_t2i_mini/train_dreambooth_sd3.py` | prepare data, finetune, resume, DreamBooth-style adaptation | checkpoints, logs, TensorBoard runs |
| Audio / music | `lumina_audio/`, `lumina_music/` | generate sounds or music from prompts, edit structure-caption settings, run Gradio demos | WAV files, Gradio outputs, caption TSVs |
| Visual anagrams | `visual_anagrams/` | generate multi-view optical illusions or animate them | illusion images, metadata pickles, MP4s |
| ImageNet training | `Flag-DiT-ImageNet/`, `Next-DiT-ImageNet/`, `Next-DiT-MoE/` | run large distributed training or sampling on ImageNet | checkpoints, logs, evaluation samples |

## Evidence cues

- `pyproject.toml` names the distribution `lumina-t2x` and defines the root console scripts `lumina` and `lumina_next`.
- `README.md` and the per-directory READMEs show the user-facing commands and checkpoint layouts.
- Model code in the image and benchmark families imports `flash_attn` directly, so image workflows need a compatible FlashAttention build.
- Audio and music demos are script-driven and depend on checkpoint folders plus the `n2s_openai.py` structure-caption helper for audio.

## Exclusion notes

- Generated caches, build directories, and log artifacts are not part of the runtime skill.
- The top-level `README.md` mentions video and 3D examples, but there is no dedicated runnable code tree for those workflows in this checkout, so they are not routed as primary skill targets.
