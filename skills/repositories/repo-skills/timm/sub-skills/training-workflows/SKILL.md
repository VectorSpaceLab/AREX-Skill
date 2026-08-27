---
name: training-workflows
description: "Compose timm API-level training loops with optimizer and scheduler
  factories, loss selection, task wrappers, EMA, AMP scaling, metrics,
  checkpoint state, and safe CPU smoke checks. Use when writing or debugging
  custom training code rather than cataloging train.py CLI flags or building
  data loaders."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training Workflows

Use this sub-skill when an agent needs to assemble or debug timm training components in Python code: `create_optimizer_v2`, `optimizer_kwargs`, `create_scheduler_v2`, loss modules, task wrappers, EMA, AMP scaling, metrics, and checkpoint-saving concepts.

## Route by Need

- **Optimizer or parameter groups**: Start with `references/optimizer-scheduler-guide.md` for `create_optimizer_v2`, weight-decay filtering, layer decay, hybrid fallback groups, and `optimizer_kwargs` config translation.
- **LR schedule behavior**: Use `references/optimizer-scheduler-guide.md` for `create_scheduler_v2`, epoch-vs-update stepping, warmup, cycles, plateau metrics, and returned adjusted epoch counts.
- **Losses and task wrappers**: Use `references/training-api.md` for `LabelSmoothingCrossEntropy`, `SoftTargetCrossEntropy`, `BinaryCrossEntropy`, `JsdCrossEntropy`, `ClassificationTask`, and distillation task routing.
- **EMA, AMP, metrics, checkpoints**: Use `references/training-api.md` for `ModelEma` variants, `NativeScaler`, `accuracy`, `AverageMeter`, task checkpoint state, and `CheckpointSaver` concepts.
- **Failure diagnosis**: Use `references/troubleshooting.md` for unsupported optimizer names, layer-decay grouping, scheduler step confusion, mixup/BCE target shape, distillation shape mismatches, EMA resume, and AMP/device mismatch.
- **Smoke construction**: Run or adapt `scripts/training_api_smoke.py` to verify a model, optimizer, scheduler, loss, optional task wrapper, metrics, EMA, and one CPU backward pass.

## Boundaries

- This sub-skill covers API-level composition. Leave train script flag catalogs and launch recipes to `cli-workflows`.
- This sub-skill assumes tensors already come from a valid pipeline. Leave dataset, loader, transforms, mixup/cutmix construction, and collation details to `data-pipelines`.
- Do not make generated examples depend on repository-local files; keep examples importable from installed `timm` and standard PyTorch.

## Safe Defaults

For a minimal custom loop, prefer `create_model(..., pretrained=False)`, `create_optimizer_v2(model, opt='adamw', lr=...)`, `create_scheduler_v2(optimizer, sched='cosine', num_epochs=..., warmup_epochs=...)`, a target-compatible loss, `accuracy`/`AverageMeter` for logging, and optional `ModelEmaV3` after model/device placement.

Run the smoke script before recommending a larger recipe:

```bash
python scripts/training_api_smoke.py --model resnet18 --opt adamw --sched cosine
```
