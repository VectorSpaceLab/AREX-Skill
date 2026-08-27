# Helios overview

Helios is a diffusion-style video generation repo centered on three public
checkpoints:

- **Helios-Base**: highest-quality general generation checkpoint.
- **Helios-Mid**: intermediate checkpoint used for staged distillation.
- **Helios-Distilled**: fastest checkpoint for practical inference and the
  public demo-style path.

## Workflow map

| Workflow | What it does | Main entry point |
| --- | --- | --- |
| Inference | Text-to-video, image-to-video, and video-to-video generation; low-VRAM and multi-GPU variants | `sub-skills/inference/SKILL.md` |
| Data preparation | Validate metadata and prepare the inputs that training expects | `sub-skills/data-preparation/SKILL.md` |
| Training | Stage 1/2/3 training, config validation, and checkpoint handling | `sub-skills/training/SKILL.md` |

## Model-family notes

- The diffusers-style pipeline surface is the most user-facing runtime API.
- The repository also contains a local pipeline implementation that exposes a
  richer set of training-oriented generation controls.
- The public demo flow favors the distilled checkpoint and short, interactive
  generation settings.

## Good first check

Run `scripts/check_helios_env.py` before a workflow. It summarizes the installed
backend, key package versions, and whether the Helios-facing imports are likely
to succeed.
