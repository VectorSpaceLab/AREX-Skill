---
name: turbot2av-extension
description: "Plan TurboT2AV text-to-audio-video extension setup, checkpoints,
  Pixi/LTX environment separation, inference commands, and TurboDiffusion-style
  acceleration choices."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TurboT2AV Extension

Use this sub-skill when the task is about the TurboT2AV text-to-audio-video extension rather than the core Wan T2V/I2V TurboDiffusion workflows.

Read these bundled references before giving commands:

- [TurboT2AV setup and inference](references/turbot2av.md) for environment separation, required weights, prompt files, student/teacher inference planning, and CLI options.
- [Acceleration notes](references/acceleration-notes.md) for SageSLA, TileLang W8A8, FastNorm, `topk=0.3`, `trim_text_context`, and how TurboT2AV acceleration differs from core TurboDiffusion.
- [Troubleshooting](references/troubleshooting.md) for Pixi/LTX isolation, Gemma gated access, missing checkpoints, CUDA/TileLang/SageAttention/SpargeAttn failures, and interpretation pitfalls.

Use the bundled command renderer instead of hand-assembling long inference commands:

- [scripts/build_turbot2av_command.py](scripts/build_turbot2av_command.py) renders a student or teacher `ltx_distillation.tools.run_av_inference_eval` command from user-supplied paths and options. It validates that required paths are supplied, prints only commands, and never downloads weights or runs inference.

Route elsewhere:

- Core Wan text-to-video or image-to-video inference belongs to the sibling video-inference guidance, not this sub-skill.
- TurboDiffusion CUDA operator build and Wan-specific `quant_linear` troubleshooting belongs to the acceleration-backends guidance; this sub-skill only explains how those ideas are adapted for LTX/TurboT2AV.
- Full LTX-2 internals, training, and Pixi installation script maintenance are reference-only; do not duplicate or rewrite the LTX-2 project here.
