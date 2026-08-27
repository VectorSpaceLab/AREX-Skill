---
name: training
description: "Inspect and operate the MedSegDiff segmentation training workflow,
  including CLI configuration, model and diffusion factories, checkpoints,
  precision, batching, logging, and device setup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MedSegDiff training

Use this sub-skill for the `scripts/segmentation_train.py` path and its factory/runtime wiring. It is an operating guide, not a promise that training is cheap or CPU-compatible.

## Route

1. Start with [`references/workflows.md`](references/workflows.md) for dataset-branch selection, exact commands, documented configurations, checkpoint behavior, and the inspection/training boundary.
2. Use [`references/api-reference.md`](references/api-reference.md) for verified defaults and signatures before changing a flag or constructing the factory directly.
3. Use [`references/troubleshooting.md`](references/troubleshooting.md) when import, branch, shape, device, resume, precision, or version behavior is surprising.
4. Run [`scripts/inspect_train_cli.py`](scripts/inspect_train_cli.py) for `--help`, defaults, and branch inspection. It is deliberately stdlib-only: it does not import the training launcher, Visdom, PyTorch, a dataset, or a model.

## Hard boundary

- CLI/default inspection and a tiny direct factory construction are safe preflight operations when their dependencies are available.
- The real launcher imports `Visdom`, initializes a distributed process group, opens the dataset, builds the model, and enters an unbounded training loop unless `--lr_anneal_steps` is set. Treat it as CUDA-dependent and dataset/time intensive.
- A CPU run is not a truthful substitute for full training. Do not claim training success from parser or factory checks.
- `dpm_solver` changes the diffusion sampling path; it does not provide training data, shorten the need for training, or replace the training loop.

## Operating invariants

- Preserve the exact lowercase option spellings and pass boolean values explicitly (`True`/`False` or another accepted token); these are not `store_true` switches.
- The launcher chooses `ISIC`, `BRATS`, or a custom 2-D/3-D fallback before setting `in_ch`. Dataset branch and model input channels must agree.
- Keep architecture, diffusion, `version`, and channel flags identical when resuming a checkpoint; inspect the resume caveats before trusting restored optimizer/EMA state.
