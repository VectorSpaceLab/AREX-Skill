---
name: training-and-cli
description: "Routes TensorLayer training loops, evaluation helpers, and CLI workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Training and CLI

Use this sub-skill for TensorLayer supervised training loops, evaluation helpers, CLI help, and distributed-trainer entry points. This is the route for `fit`, `test`, `predict`, and `tl train` style tasks.

## Typical requests

- Run a tiny TensorLayer training loop.
- Check `tl.utils.fit`, `tl.utils.test`, or `tl.utils.predict` usage.
- Inspect the `tensorlayer.cli` entry point or `build_arg_parser` behavior.
- Understand how `tl train` or the distributed trainer is wired.

## Read first

- `references/cli-reference.md` for the CLI and utility API surface.
- `references/workflows.md` for a tiny synthetic fit/test/predict loop.
- `references/troubleshooting.md` for CLI, dataset, and distributed-training failures.

## Bundled checks

- `scripts/smoke_fit.py` runs a small synthetic classification problem through `tl.utils.fit`, `tl.utils.test`, and `tl.utils.predict`.
- Root `scripts/check_cli_help.py` verifies `python -m tensorlayer.cli --help` without the empty-`CUDA_VISIBLE_DEVICES` bug.

## Boundaries

Include here:
- `tensorlayer.utils`
- `tensorlayer.cli`
- `tensorlayer.distributed`
- fit/test/predict and evaluation helpers
- training-loop and parser behavior

Exclude or route elsewhere:
- layer/model architecture details -> `core-modeling`
- preprocessing and TFRecord helpers -> `data-and-utilities`
- pretrained vision model constructors -> `vision-and-apps`
- text, seq2seq, and NLP helpers -> `text-and-sequence`
- reward utilities and RL examples -> `reinforcement-learning`

## Fast path

1. Check whether the task is about a training loop, evaluation helper, or CLI parser.
2. Use synthetic data first; do not depend on MNIST/CIFAR downloads for a smoke.
3. Treat distributed execution as help-only unless the user explicitly requests a Horovod/OpenMPI environment.
