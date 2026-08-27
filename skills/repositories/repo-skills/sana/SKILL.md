---
name: sana
description: "Use and maintain Sana image, video, training, evaluation, and
  deployment workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Sana

Use this repo skill when the task names Sana, SANA-1.5, SANA-Sprint, SANA-Video, LongSANA, SANA-WM, SANA-Streaming, or Sol-RL, or when the request spans more than one Sana workflow family. This root skill is a router for the sub-skills below, not a long manual.

This skill is self-contained guidance distilled from the Sana repository. It does not require the original checkout to remain available once this tree has been generated.

## Route By Task

| User task | Read |
| --- | --- |
| Still-image generation, prompt-file image batches, ControlNet HED, 4-bit/8-bit image inference, 2K/4K tiling, Gradio image demos | [image-generation](sub-skills/image-generation/SKILL.md) |
| SANA-Video, LongSANA, SANA-WM, SANA-WM streaming, or SANA-Streaming V2V | [video-world-streaming](sub-skills/video-world-streaming/SKILL.md) |
| Image/video training, data layout validation, FSDP/DDP launch planning, LoRA/DreamBooth, Sprint, Sol-RL, or Cosmos-RL boundaries | [training-data-configs](sub-skills/training-data-configs/SKILL.md) |
| Metrics, checkpoint conversion/export, `sana-run`, `sana-upload`, SGLang, ComfyUI, or deployment planning | [evaluation-conversion-deployment](sub-skills/evaluation-conversion-deployment/SKILL.md) |

## Common Entry Points

- `python scripts/check_sana_install.py` performs a safe import/CLI smoke check.
- `python scripts/check_sana_install.py --skip-cli` keeps the check import-only.
- `python -m pip install -e .` is the expected editable install path after the required Python 3.11/CUDA stack is ready.
- `sana-run --help` and `sana-upload --help` are the public entry points for the two console scripts.

## Shared References

- `references/troubleshooting.md`: cross-cutting install, import, backend, and CLI triage.
- `references/repo-provenance.md`: source snapshot and staleness cues for this generated skill.
- `references/repo-routing-metadata.json`: structured managed-router metadata for this skill.

## Start Here

1. Pick the route that matches the user request.
2. Read the sub-skill before drafting commands or explanations.
3. Use the bundled helper in that sub-skill if the workflow has one.
4. Keep final guidance self-contained; do not point runtime instructions back at the original checkout.

## Boundaries

- Do not turn this root into a model runner, trainer, benchmark harness, or download assistant.
- Do not duplicate the full workflow manuals here; the sub-skills own those details.
- Do not assume CPU-only smoke checks prove a CUDA generation or distributed-training workflow works.
