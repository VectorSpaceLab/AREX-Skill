---
name: "training-and-distribution"
description: "Guides MMGeneration training, resume, distributed launch, and
  launcher-specific workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training and Distribution

Use this sub-skill when the user wants to train a model, resume from a checkpoint, or understand the repo's distributed training and validation flow.

## Typical triggers

- "How do I train this config?"
- "How do I resume a run?"
- "How do I use DDP or Slurm?"
- "Can I train on CPU for debugging?"
- "Why does the training hook not behave as expected?"

## Include here

- `tools/train.py`
- `tools/dist_train.sh`
- `tools/slurm_train.sh`
- `mmgen.apis.train_model` and `set_random_seed`
- `DynamicIterBasedRunner`
- DDP wrapper and dynamic DDP notes
- EMA, visualization, checkpoint, and validation hook behavior
- CPU training guidance for debug-only use

## Exclude here

- Sampling and demo workflows -> `inference-and-sampling`
- Metrics and validation scripts -> `evaluation-and-metrics`
- Config syntax and registry extension -> `configuration-and-extension`
- Latent editing and deployment helpers -> `applications-and-deployment`

## Read these files first

- `references/workflows.md`
- `references/troubleshooting.md`
- `../../references/api-reference.md`
- `../../references/cli-reference.md`
- `../../references/model-overview.md`

## What good guidance looks like

A future agent should be able to:

1. Pick the right launcher: none, PyTorch DDP, or Slurm.
2. Explain how `work_dir`, `resume_from`, and `load_from` interact.
3. Distinguish static and dynamic GAN behavior in distributed mode.
4. Tell the user when CPU training is acceptable only as a debugging aid.
5. Route validation and evaluation questions to the evaluation sub-skill instead of mixing them into training advice.

## Common failure modes

- DDP settings that work for static GANs but fail for dynamic architectures.
- `apex_amp` being used outside the distributed-only path.
- Missing or incorrect `work_dir`, `cfg_options`, or checkpoint resume path.
- A custom hook or runtime block not being registered before the run starts.

For concrete recovery steps, read `references/troubleshooting.md`.
