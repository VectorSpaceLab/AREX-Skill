---
name: training
description: "Configure EdgeConnect training, internal validation sampling,
  checkpoint resume, and loss behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Training

Use this sub-skill when you need to plan, configure, or reason about EdgeConnect training-time stages and the internal validation loop.

## Covers
- `train.py` as the thin `MODE=1` wrapper over `main.load_config(mode=1)`.
- The distinction between `MODE` (run type) and `MODEL` (stage family).
- `EdgeConnect.train`, `EdgeConnect.eval`, and `EdgeConnect.sample` behavior.
- Stage-specific checkpoint loading, saving, sampling, and logging.
- Generator/discriminator architecture, VGG-based losses, and internal metrics.

## Entry points
- `references/training-workflows.md`
- `references/model-overview.md`
- `references/troubleshooting.md`
- `scripts/make_training_config.py`

## Use for
- choosing a training stage before a run
- generating or editing a training config
- understanding `*_gen.pth`, `*_dis.pth`, `samples/`, `results/`, and `log_*.dat`
- explaining why a run resumed, stalled, or produced unexpected losses

## Do not use for
- dataset flist construction or path validation
- test-time command wiring
- PSNR/SSIM/FID scoring after inference
