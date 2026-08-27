---
name: training-evaluation
description: "Assemble MONAI training and evaluation loops with Ignite-based
  engines, handlers, schedulers, checkpointing, validation, logging,
  AMP/distributed caveats, and tiny workflow checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MONAI Training and Evaluation

Use this sub-skill when a task asks for MONAI training/evaluation loops, `monai.engines` trainer/evaluator wiring, Ignite event handlers, validation callbacks, checkpointing, stats/logging, MONAI optimizer utilities, or debugging engine/handler behavior.

## Route by task

- For a handwritten PyTorch loop that needs MONAI structure, read `references/workflows.md` to choose plain PyTorch versus `SupervisedTrainer`/`SupervisedEvaluator` and wire loaders, network, loss, optimizer, metrics, handlers, and validation.
- For constructor arguments, handler attachment points, output keys, metric transforms, or scheduler utilities, read `references/api-reference.md` before coding against `monai.engines`, `monai.handlers`, or `monai.optimizers`.
- For runtime errors, silent logs, stale metrics, missing checkpoints, AMP/CUDA assumptions, distributed sampler issues, or optional tracking dependencies, read `references/troubleshooting.md`.
- To prove the installed MONAI plus Ignite stack can run a tiny CPU training/validation workflow, run `scripts/tiny_supervised_workflow.py --help` first, then `scripts/tiny_supervised_workflow.py`.

## Boundaries

- This sub-skill owns training/evaluation orchestration: `monai.engines`, `monai.handlers`, `monai.optimizers`, trainer/evaluator events, validation, checkpoints, stats/logging, AMP and distributed considerations.
- For data dictionaries, transforms, datasets, caches, and dataloaders, use the `data-transforms` sub-skill first, then return here for engine wiring.
- For model architecture, losses, inferers, postprocessing transforms, and metric selection details, use the `modeling-inference` sub-skill first, then return here for loop integration.
- For config-driven bundle training/evaluation, use the `bundle-config` sub-skill instead of hand-assembling engines.
- For Auto3DSeg orchestration, use the `apps-auto3dseg` sub-skill instead of writing trainer/evaluator loops manually.
