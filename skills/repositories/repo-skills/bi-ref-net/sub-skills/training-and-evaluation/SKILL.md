---
name: training-and-evaluation
description: "Route BiRefNet training launches, resume semantics, evaluation
  metrics, and best-checkpoint selection."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# training-and-evaluation

Use this sub-skill for BiRefNet fine-tuning, epoch scheduling, checkpoint loading/saving, metric evaluation, and best-epoch selection.

## Handles
- `train.py` CLI: `--resume`, `--epochs`, `--ckpt_dir`, `--dist`, `--use_accelerate`
- `train.sh` task-specific epoch, validation, and save schedules
- `train_test.sh` train-then-evaluate orchestration
- `test.sh` inference plus evaluation over configured testsets
- `eval_existingOnes.py`, `evaluation.metrics.evaluator`, `sort_and_round_scores`
- `gen_best_ep.py` checkpoint ranking from `e_results/*_eval.txt`

## Use the bundled script
- `scripts/birefnet_metric_smoke.py` — create tiny mask fixtures and exercise `evaluation.metrics.evaluator` from an explicit or inferred repo root.

## Read next
- `references/training-workflows.md`
- `references/evaluation-workflows.md`
- `references/metrics-reference.md`
- `references/troubleshooting.md`

## Recommended operating flow

1. Validate dataset layout and task/testset names with `../configuration-and-data/SKILL.md` before building a training or evaluation command.
2. Confirm backbone/weight compatibility with `../model-architecture/SKILL.md`; wrong `config.bb` often appears as a checkpoint tensor-size error.
3. For fine-tuning, compute total epochs from the checkpoint filename epoch plus the desired additional epochs because `train.py` resumes at filename epoch + 1.
4. Treat full training as GPU/data/weight/budget dependent; use this sub-skill to plan commands and only execute after explicit user approval.
5. Before evaluating real predictions, run `scripts/birefnet_metric_smoke.py` to confirm metric dependencies and evaluator wiring.

## Done criteria

- Training commands name the run directory, GPU IDs, total epoch count, resume path, and whether Accelerate/DDP is used.
- Evaluation commands have matching `gt_root`, `pred_root`, dataset names, and metric flags.
- Checkpoint selection criteria (`sm`, `wfm`, and DIS-only `hce`) are explicit.
- Asset-heavy native runs are marked skipped unless the user provides data, weights, hardware, and time budget.

## Route out
- Dataset tree and task/testset selection -> `../configuration-and-data/SKILL.md`
- Backbone choice, checkpoint key cleanup, and weight compatibility -> `../model-architecture/SKILL.md`
- Standalone image/video mask generation and foreground refinement -> `../inference-and-postprocessing/SKILL.md`
