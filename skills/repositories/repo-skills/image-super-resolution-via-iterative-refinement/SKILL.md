---
name: image-super-resolution-via-iterative-refinement
description: "Route Image Super-Resolution via Iterative Refinement SR3/DDPM
  dataset, config, training, inference, sampling, evaluation, and logging
  workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Image Super-Resolution via Iterative Refinement

Use this repo skill when a task names **Image Super-Resolution via Iterative Refinement**, **SR3**, this Janspiry PyTorch implementation, or asks for the repository's dataset preparation, config editing, super-resolution training/validation, pretrained inference, unconditional sampling, PSNR/SSIM evaluation, or W&B/TensorBoard logging workflows.

This skill is self-contained operating guidance. It distills the repository's scripts and configs into references and safe helper scripts; it does not require opening the original README or source files just to decide a workflow.

## First checks

1. Read [references/repo-provenance.md](references/repo-provenance.md) when deciding whether this skill is current for a checkout.
2. Read [references/installation.md](references/installation.md) before installing dependencies, checking CUDA, or deciding whether W&B/data/checkpoint prerequisites are available.
3. Run [scripts/check_environment.py](scripts/check_environment.py) in a target checkout when you need an import/CUDA/config smoke check.
4. Read [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting failures before drilling into workflow-specific troubleshooting.

## Route by task

| User intent | Read |
|---|---|
| Prepare, validate, or explain LR/HR/SR image or LMDB datasets | [sub-skills/data-preparation/SKILL.md](sub-skills/data-preparation/SKILL.md) |
| Inspect or edit JSON-with-comments configs, model family, beta schedule, checkpoint stem, or GPU ids | [sub-skills/model-configuration/SKILL.md](sub-skills/model-configuration/SKILL.md) |
| Build `sr.py` train/validation/resume/debug commands for conditional super-resolution | [sub-skills/super-resolution-training/SKILL.md](sub-skills/super-resolution-training/SKILL.md) |
| Build pretrained `infer.py` commands or unconditional `sample.py` commands | [sub-skills/inference-and-sampling/SKILL.md](sub-skills/inference-and-sampling/SKILL.md) |
| Score result directories with PSNR/SSIM or diagnose TensorBoard/W&B logging | [sub-skills/evaluation-and-logging/SKILL.md](sub-skills/evaluation-and-logging/SKILL.md) |

## Repository workflow map

- `data/prepare_data.py` source behavior is represented by the data-preparation references and bundled layout/fixture helpers.
- `sr.py` is the conditional super-resolution training and validation entry point; the bundled command builder prints safe launch commands but never runs training.
- `infer.py` is the pretrained conditional super-resolution inference entry point; it needs prepared validation data and a generator checkpoint stem.
- `sample.py` is the unconditional generation/train/eval entry point; it is not a supervised super-resolution evaluator.
- `eval.py` source behavior is represented by a stricter bundled result-pair evaluator under the evaluation sub-skill.

## Operational constraints to surface early

- Stock workflows are PyTorch/CUDA-oriented. The source code selects CUDA whenever GPU ids are configured; CPU-only operation is an adaptation, not the default path.
- Full training, validation, inference, and sample generation need substantial GPU time because stock beta schedules use 2000 reverse steps.
- Real data and pretrained checkpoints are external prerequisites. Do not download large datasets or checkpoint archives unless the user explicitly asks and approves network/storage use.
- W&B logging is optional and requires the `wandb` package plus user login/token. Do not enable it silently.
- Config files allow `//` comments; use the bundled config inspector or the repo-style parser behavior.

## Minimal smoke workflow

From a target checkout with dependencies installed:

```bash
python scripts/check_environment.py --repo-root /path/to/checkout --config /path/to/checkout/config/sr_sr3_16_128.json
```

Then route to the relevant sub-skill. For example, validate a tiny image layout before training, inspect the chosen config, generate a command, and only then run the repository workflow in the user's approved environment.
