---
name: training-evaluation
description: "Guide safe use of the learning-to-learn training and evaluation
  CLIs without depending on the source checkout."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# training-evaluation

Use this sub-skill when you need to run, adapt, or troubleshoot the repo's
`train.py` and `evaluate.py` workflows.

## Use this for
- Tiny CPU smoke commands for training and evaluation.
- Saved-optimizer directory handling for L2L reloads.
- Choosing between `optimizer=Adam` and `optimizer=L2L`.
- Understanding log / evaluation cadence and unroll math.

## Route elsewhere when
- You need meta-optimizer internals, variable interception, or save/load
  semantics beyond the CLI surface: `../meta-optimizer-api/SKILL.md`
- You need problem construction, dataset mode selection, MNIST/CIFAR data
  caveats, or custom loss guidance: `../problem-factories/SKILL.md`

## Safe default
Prefer the simple scalar problem, one epoch, two steps, and a one-step unroll.
For save/load smoke checks, point `--save-path` at a fresh directory and let the
helper script choose a save-triggering evaluation period.

## Read next
- `references/cli-reference.md`
- `references/workflows.md`
- `references/troubleshooting.md`
- `scripts/l2l_cli_smoke.py`
