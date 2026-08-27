---
name: evaluation
description: "Evaluate pytorch-cifar100 checkpoints safely with test.py, metric
  interpretation, and checkpoint/path validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# evaluation

Use this sub-skill when a user already has a pytorch-cifar100 checkpoint and needs to run the repository evaluator, select safe evaluation options, or interpret the printed metrics. This sub-skill does not create checkpoints and does not catalog architectures beyond the net-name validation needed for evaluation.

## Route

- **In scope:** building a safe `test.py` command, validating `-net` and `-weights`, choosing CPU/GPU and batch size, explaining CIFAR-100 test-data side effects, interpreting Top-1/Top-5 error and parameter-count output.
- **Route to `training`:** creating checkpoints, resuming training, changing optimization settings, or deciding which epochs to save.
- **Route to `model-zoo`:** model internals, architecture trade-offs, output-shape adaptation, or choosing among architecture families.

## Concise workflow

1. Confirm the checkpoint is user-supplied; no pretrained checkpoints are bundled with this skill.
2. Pick the same CLI net name that produced the checkpoint. If uncertain, inspect the checkpoint path/name and use `scripts/build_eval_command.py --list-nets` for supported evaluator names.
3. Build but do not execute the command with `scripts/build_eval_command.py`; it checks net spelling, validates the weights path unless explicitly allowed, and warns about CIFAR-100 download and GPU behavior.
4. Run the printed command from the repository root so imports resolve and the evaluator can use `./data` for CIFAR-100.
5. Read the end of stdout for `Top 1 err`, `Top 5 err`, and `Parameter numbers`; lower error is better, and the printed errors are fractions unless you convert them to percentages.

## Bundled references

- `references/evaluation-workflows.md` — evaluator command, runtime behavior, metric interpretation, and CPU/GPU/batch choices.
- `references/checkpoints.md` — checkpoint naming, expected state_dict format, architecture matching, and safe checkpoint path selection.
- `references/troubleshooting.md` — common failures and targeted recovery steps.
