---
name: detrex
description: "Use detrex for detection-transformer configs, training/evaluation,
  demos, model zoo conversion, and package API debugging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# detrex repo skill

detrex is a Detectron2-based toolbox for Transformer object detection, segmentation, and related DETR-family research workflows. Use this skill when a task names detrex or asks for DETR/DINO/Deformable-DETR/MaskDINO/CO-MOT configs, training, evaluation, demos, checkpoint conversion, or package API debugging.

## Before acting

1. Read [references/repo-provenance.md](references/repo-provenance.md) when checking whether this skill matches a checkout or when deciding whether to refresh it.
2. Read [references/environment-and-installation.md](references/environment-and-installation.md) before install/build/import work.
3. Run [scripts/check_environment.py](scripts/check_environment.py) for safe import, CUDA-extension, config, and tool-help checks.
4. Use [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import/backend issues, then route to the closest sub-skill troubleshooting page.

## Route by task

| User need | Read |
|---|---|
| Build or debug train/eval commands, LazyConfig overrides, datasets, fast debug, AMP, EMA, WandB, DDP, Hydra, or Slurm command shape | [training-and-configs](sub-skills/training-and-configs/SKILL.md) |
| Choose a project/model family, interpret model zoo rows, use DINO/MaskDINO/CO-MOT project notes, inspect/convert DETR-family checkpoints, or change pretrained backbones | [model-zoo-and-converters](sub-skills/model-zoo-and-converters/SKILL.md) |
| Run or construct image/video demos, visualize JSON predictions or datasets, inspect model structure/FLOPs, or build benchmark commands | [tools-and-demos](sub-skills/tools-and-demos/SKILL.md) |
| Import/inspect Python APIs for layers, losses, matchers, backbones, data mappers, config helpers, checkpointing, EMA, distributed utilities, WandB writer, or compiled ops | [package-apis](sub-skills/package-apis/SKILL.md) |

## Minimal install/import orientation

Public source installations normally require Linux, Python 3.7+, matching PyTorch/torchvision, Detectron2, compiler tools, and CUDA toolkit when the custom CUDA extension is needed. A minimal validation sequence is:

```bash
python -c "import torch, torchvision; print(torch.__version__, torchvision.__version__)"
python -c "import detectron2; import detrex; print('detrex import ok')"
python scripts/check_environment.py --strict --check-config common/train.py
python scripts/check_environment.py --strict --check-cuda-extension
```

Only require the CUDA-extension check when the task needs `MultiScaleDeformableAttention`, Deformable-DETR, DINO, or other compiled-op paths. CPU-safe API/config work can still be valid without running full GPU demos or COCO training.

## Operating guardrails

- Do not assume the original source checkout is available. Use installed package modules or bundled scripts/references in this skill.
- Do not download model weights, demo inputs, datasets, or benchmark assets unless the user explicitly asks and provides sources or approval.
- Treat full training, full COCO evaluation, real demos, benchmarks, and tracking evaluation as expensive/native workflows that need user-provided artifacts and runtime approval.
- Keep config, checkpoint, dataset, and backbone families aligned; DETR-family checkpoints are not interchangeable solely because they share a backbone.
- Use project-specific trainers when the model family documents a hacked or specialized trainer route.
- For custom datasets, validate Detectron2 registration, metadata, file paths, and mapper choice before debugging model code.
