---
name: training-workflows
description: "Lightly SSL training recipes for PyTorch, Lightning, and gated
  distributed variants."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# training-workflows

Use this sub-skill when a task needs to turn a LightlySSL method example into a runnable training plan, choose a recipe family, adapt a training loop to local data, or debug PyTorch Lightning/distributed training behavior. It does not run long training by default; it helps future agents plan and validate safely first.

## Use this sub-skill for

- Bare PyTorch Lightly recipes that wire a backbone, projection head, transform, dataloader, loss, optimizer, and training step.
- PyTorch Lightning module patterns, `Trainer` knobs, checkpoint handling, precision/device choices, and batch-size/worker decisions.
- Adapting repo-style CIFAR/download examples to local image folders or synthetic no-download smoke checks.
- Distributed or accelerator-aware training plans when the user explicitly asks for GPU, multi-GPU, DDP, or distributed losses.
- Troubleshooting feature-dimension mismatches, missing checkpoints, long-running data downloads, `drop_last`/batch issues, and DDP hangs.

## Start here

- [Training recipes](references/training-recipes.md) — method selection, bare PyTorch loop patterns, and local-folder adaptation.
- [Lightning workflows](references/lightning-workflows.md) — `LightningModule`, `Trainer`, checkpointing, and batch/device knobs.
- [Distributed training](references/distributed-training.md) — DDP settings, optional sync/gather caveats, and backend honesty.
- [Troubleshooting](references/troubleshooting.md) — common failures, causes, and fixes.
- [Synthetic SimCLR step](scripts/tiny_simclr_training_step.py) — one no-download smoke step for backbone, feature-dimension, and contrastive-loss wiring.

## Route elsewhere

- API component catalogs, transform/loss/head signatures, and tensor-only component debugging: use `ssl-building-blocks`.
- `lightly-ssl-train`, `lightly-embed`, `lightly-magic`, `lightly-crop`, Hydra overrides, and data folder validation: use `cli-data-embedding`.
- Maintainer tests, generated notebooks, docs, benchmarking utilities, and repository validation: use `evaluation-maintenance`.

## Safe workflow order

1. Choose the method family and recipe style: bare PyTorch, Lightning, or distributed Lightning.
2. Validate the low-level components with `ssl-building-blocks` when dimensions, transforms, or losses are uncertain.
3. Run `python scripts/tiny_simclr_training_step.py --device cpu` from this sub-skill before touching user data.
4. Replace example dataset downloads with a local folder or a user-provided dataset only after the smoke passes.
5. Scale to CUDA or DDP only after checking hardware, package backends, output paths, and runtime budget.
6. For repository edits to examples or docs, route to `evaluation-maintenance` for notebook/docs/test commands.

## Guardrails

- Prefer local image folders or synthetic tensors; do not make future agents run download-heavy example scripts as the first validation step.
- Treat distributed training as optional and explicitly gated by hardware, process group setup, and user approval.
- Do not claim GPU or DDP verification from a CPU import; run a real backend smoke when those capabilities are required.
- Keep CLI train/embed/magic as artifact-writing workflows. Use `cli-data-embedding` to build commands and set output/checkpoint paths before execution.
