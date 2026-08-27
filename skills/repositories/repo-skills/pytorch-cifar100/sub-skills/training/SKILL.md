---
name: training
description: "Routes CIFAR-100 training command construction, warmup,
  TensorBoard, checkpoint resume, and LR-finder constraints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Training

Use this sub-skill when you need to run, resume, or adapt `train.py` for CIFAR-100.

## Start here

1. Read [`references/training-workflows.md`](references/training-workflows.md) for the end-to-end training flow, checkpoint lifecycle, resume behavior, and TensorBoard side effects.
2. Read [`references/data-and-config.md`](references/data-and-config.md) for the CIFAR-100 layout, normalization constants, and legacy `dataset.py` caveats.
3. Read [`references/troubleshooting.md`](references/troubleshooting.md) when a command fails, `resume` cannot find weights, or CUDA/logging/data setup is unclear.
4. Use [`scripts/build_train_command.py`](scripts/build_train_command.py) to validate a proposed `train.py` command before launching a long run.
5. Read [`references/lr-finder.md`](references/lr-finder.md) only when you intentionally want the optional learning-rate scan.

## Core command

```bash
python train.py -net <name> [-gpu] [-b B] [-warm WARM] [-lr LR] [-resume]
```

Defaults:
- `-b 128`
- `-warm 1`
- `-lr 0.1`
- `-gpu` off
- `-resume` off

## Scope

This sub-skill covers:
- CIFAR-100 training command construction
- warmup, SGD, MultiStepLR, TensorBoard, and checkpoint side effects
- resume semantics and safe command planning
- optional LR-finder constraints as a reference-only add-on

This sub-skill does not cover:
- architecture internals beyond choosing `-net`
- final checkpoint metric interpretation
- standalone evaluation or `test.py` usage
