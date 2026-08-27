---
name: turbo-diffusion
description: "Use TurboDiffusion for accelerated Wan video generation,
  interactive serving, checkpoint conversion, CUDA acceleration backends, and
  TurboT2AV extension planning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TurboDiffusion

Use this repo skill when a task involves TurboDiffusion, TurboWan, Wan2.1/Wan2.2 accelerated video generation, SLA/SageSLA attention, rCM/SLA checkpoint conversion or training, the `turbodiffusion-serve` TUI, or TurboT2AV audio-video generation.

TurboDiffusion is a CUDA-first package. Most real generation workflows need a compatible NVIDIA GPU, model checkpoints, Wan VAE/text encoder files, and source-layout imports. Do not start downloads, long generation, or training unless the user explicitly supplied the needed assets and budget.

## First checks

1. Read [repo provenance](references/repo-provenance.md) when deciding whether this skill is current for a checkout.
2. Read [installation and backend notes](references/installation-and-backends.md) before installing, compiling, or diagnosing CUDA/SageSLA/custom-op problems.
3. Run [scripts/check_turbodiffusion_env.py](scripts/check_turbodiffusion_env.py) when a user asks whether their current environment can import TurboDiffusion, see CUDA, load custom ops, or use optional SageSLA.
4. Read [model and asset catalog](references/model-and-asset-catalog.md) before building commands that mention VAE/text encoder/DiT checkpoints, high/low I2V checkpoints, prompt files, or TurboT2AV assets.
5. Use [cross-cutting troubleshooting](references/troubleshooting.md) for install/import, source-layout, missing checkpoint, CUDA, and optional dependency failures.

## Sub-skill routing

| User request | Read |
| --- | --- |
| Build a one-shot text-to-video or image-to-video command; choose Wan2.1/Wan2.2 model flags; validate prompt/image/checkpoint arguments; avoid running models while planning. | [video-inference](sub-skills/video-inference/SKILL.md) |
| Launch or debug the interactive terminal server; decide T2V vs I2V TUI flags; understand slash commands and runtime-adjustable parameters. | [interactive-serving](sub-skills/interactive-serving/SKILL.md) |
| Prepare SLA/rCM training commands, checkpoint conversion, checkpoint merging, safetensors-to-pth conversion, quantized checkpoint export, or data/checkpoint layout checks. | [training-and-checkpoints](sub-skills/training-and-checkpoints/SKILL.md) |
| Diagnose CUDA extension build/import, `turbo_diffusion_ops`, INT8/FastNorm, `attention_type=sla` vs `sagesla`, SpargeAttn, `flash-attn`, or source-layout import quirks. | [acceleration-backends](sub-skills/acceleration-backends/SKILL.md) |
| Plan TurboT2AV text-to-audio-video generation, LTX-2/Pixi setup, HF/Gemma checkpoint requirements, or TileLang/SageSLA acceleration choices. | [turbot2av-extension](sub-skills/turbot2av-extension/SKILL.md) |

## Operating rules

- Prefer the bundled command builders in sub-skill `scripts/` for command construction. They render commands and validate obvious mistakes without downloading weights, starting training, or running generation.
- For source checkouts, TurboDiffusion scripts and even the installed TUI entry point may require adding the package source directory to `PYTHONPATH` so top-level imports such as `imaginaire`, `rcm`, `serve`, and `modify_model` resolve. Capture this as a public source-layout requirement, not as a local path.
- Treat `attention_type=sagesla` as optional-backend dependent: install SpargeAttn first or fall back to `sla`/`original` when SageSLA is not available.
- Match `--quant_linear` to quantized checkpoints. Do not add it to unquantized checkpoints on large-memory GPUs unless the user explicitly wants the quantized path.
- Do not run full T2V/I2V/TurboT2AV generation unless the user provides the checkpoints, VAE/text encoder assets, output location, GPU budget, and permission to spend time/GPU memory.
- Do not run full rCM/SLA training unless the user provides checkpoint/data roots, distributed/GPU budget, logging policy, and any credentials such as WandB or Hugging Face tokens.

## Minimal environment smoke

Use this public smoke from an installed/source-layout environment before deeper work:

```bash
python - <<'PY'
import torch
print('torch', torch.__version__, torch.version.cuda, torch.cuda.is_available())
try:
    import turbo_diffusion_ops
    print('custom ops: ok')
except Exception as exc:
    print('custom ops:', type(exc).__name__, exc)
PY
```

For a fuller check, run the bundled [environment diagnostic](scripts/check_turbodiffusion_env.py). If it reports missing `imaginaire` or `rcm`, use the source-layout `PYTHONPATH` guidance in [installation and backend notes](references/installation-and-backends.md).
