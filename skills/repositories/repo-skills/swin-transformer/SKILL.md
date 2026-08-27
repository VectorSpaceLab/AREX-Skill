---
name: swin-transformer
description: "Use this repo skill for Microsoft Swin-Transformer
  image-classification model, config, data, checkpoint, SimMIM, Swin-MoE, and
  optional CUDA acceleration workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Swin-Transformer Repo Skill

Use this skill when a task involves the official Microsoft Swin-Transformer image-classification codebase: Swin V1/V2, Swin-MLP, SimMIM masked image modeling, ImageNet data layouts, pretrained checkpoint handling, supervised training/evaluation commands, Swin-MoE, or the optional fused CUDA window-process extension.

This is a self-contained operating guide. It does not require the original source checkout used during skill creation. When a workflow needs code execution, use the user's current checkout or installed copy of Swin-Transformer and the bundled helper scripts in this skill.

## Quick routing

| User intent | Read next |
| --- | --- |
| Build or inspect `SwinTransformer`, `SwinTransformerV2`, `SwinMLP`, `build_model`, tensor shapes, FLOPs, or CPU smoke models | `sub-skills/core-models/SKILL.md` |
| Validate ImageNet folder/zip/22K layouts, understand `--zip`, map files, SimMIM data, checkpoint resume/pretrained behavior, or 22K-to-1K head remapping | `sub-skills/data-and-checkpoints/SKILL.md` |
| Construct or debug supervised `main.py` commands for training, fine-tuning, evaluation, throughput, AMP, DDP launch, or `--opts` overrides | `sub-skills/training-eval-cli/SKILL.md` |
| Run or adapt SimMIM pretraining/fine-tuning/evaluation workflows and mask/loss checks | `sub-skills/simmim-workflows/SKILL.md` |
| Work with Swin-MoE, Tutel, Apex fused optimizers/layernorm, or the fused CUDA window-process extension | `sub-skills/moe-and-acceleration/SKILL.md` |
| Need a config/model family map before choosing a route | `references/model-zoo-and-configs.md` |
| Need shared YACS config and flag behavior | `references/configuration.md` |
| Need cross-cutting troubleshooting | `references/troubleshooting.md` |
| Need to verify that a checkout/environment is usable | `scripts/check_env.py` |

## Baseline prerequisites

Swin-Transformer is a research-code checkout rather than an ordinary packaged distribution. For code execution, future agents should work against a current checkout or source tree on `PYTHONPATH` and install the runtime dependencies relevant to the selected workflow:

- Required for baseline inspection and CPU smoke checks: Python, PyTorch, torchvision, `timm==0.4.12`, `yacs`, `PyYAML`, `numpy`, `scipy`, and `termcolor`.
- Required for full supervised or SimMIM training/evaluation: CUDA-capable PyTorch, GPUs, ImageNet-style data, checkpoints when evaluating/fine-tuning, and distributed launcher environment.
- Optional: Apex for fused layernorm/fused optimizers, Tutel for Swin-MoE, and a compiled `swin_window_process` CUDA extension for `--fused_window_process`.

Minimal import smoke for a checkout:

```bash
python - <<'PY'
from config import get_config
from models import build_model
from data import build_loader
print('Swin-Transformer modules import')
PY
```

If that fails, read `references/troubleshooting.md` before running full training.

## Safe helper scripts

- Run `scripts/check_env.py --repo-root <checkout>` to check required imports and optional CUDA/Tutel/Apex/fused-extension availability without training or downloading.
- Run `scripts/inspect_swin_config.py --repo-root <checkout> --cfg <config.yaml>` to summarize a YAML config and flag risky settings.
- Run `scripts/swin_cli_command_builder.py --help` to assemble copyable command templates for supervised, SimMIM, and MoE workflows.

These helpers are safe by default: they do not download models or data, do not run distributed training, and do not build CUDA extensions.

## Important boundaries

- This skill covers image classification and the code in this repository. Object detection, semantic segmentation, video action recognition, feature distillation, and other downstream projects linked by the public README are separate repositories and are not covered here.
- Full accuracy reproduction and throughput benchmarking are intentionally not used as skill-verification gates because they require large datasets, checkpoints, GPUs, and long distributed runs.
- CPU smoke checks validate config/model/data plumbing only. They are not evidence that CUDA training, Swin-MoE, Apex, or the fused window kernel works.

## Provenance and staleness

Read `references/repo-provenance.md` before deciding whether this skill matches a particular checkout. If source APIs, config layout, CLI flags, or dependency behavior differ, refresh this repo skill before relying on it.
