---
name: super-resolution-training
description: "Route sr.py super-resolution training, validation, resume, and
  debug workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Super-Resolution Training

Use this sub-skill for `sr.py` super-resolution runs when the user wants to train, resume, validate, or debug a conditional SR3/DDPM workflow.

## Start here
1. Read [`references/workflows.md`](references/workflows.md) to map the request to the right phase, config family, checkpoint rule, and output layout.
2. Read [`references/troubleshooting.md`](references/troubleshooting.md) for dataset, checkpoint, CUDA, W&B, and result-path failures.
3. Use [`scripts/build_sr_command.py`](scripts/build_sr_command.py) to validate a comment-bearing config and print a shell command. The helper only prints commands; it never launches training.

## Covered requests
- new SR3 or DDPM training runs
- resume training from a checkpoint prefix
- validation-only runs from a trained checkpoint
- debug-sized runs with the repository runtime shrinkage flag
- GPU selection and optional W&B enablement

## Do not use this sub-skill for
- dataset preparation
- unconditional generation
- pretrained inference
- metric-only evaluation
