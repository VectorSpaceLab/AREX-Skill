---
name: munit
description: "Route NVlabs MUNIT legacy multimodal image-to-image translation
  setup, data, training, inference, evaluation, and model-internals tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MUNIT Repo Skill

Use this repo skill for NVlabs/MUNIT, the legacy PyTorch implementation of Multimodal Unsupervised Image-to-Image Translation. It helps future agents operate the codebase without rereading the original docs or source: choose a legacy runtime, validate datasets/configs, construct training or inference commands, diagnose checkpoints and outputs, and understand the trainer/network internals.

## Critical Context

- MUNIT is an old CUDA/PyTorch project. The documented runtime is Python 2.7 or 3.6, PyTorch 0.4.1, TorchVision 0.2.x, CUDA 9.x, cuDNN 7.x, PyYAML, tensorboard, and tensorboardX.
- The repository is not an installable Python distribution. User workflows normally run scripts from a user-provided MUNIT checkout or a deliberately copied/ported equivalent.
- Unmodified training and inference call `.cuda()` directly. CPU-only import or parser checks are useful preflight checks, but they do not prove real training or translation will run.
- Pretrained checkpoints, VGG weights, Inception classifiers, and full datasets are external assets. Do not download them without explicit user approval.
- This skill is self-contained guidance and bundled helpers; do not ask future agents to open the source README, tutorial, configs, or scripts to complete ordinary tasks.

## Quick Setup Check

For an existing user checkout, start with the environment checker:

```bash
python sub-skills/environment-and-setup/scripts/check_munit_environment.py --repo-root /path/to/user/munit-checkout
```

Use `--expect-cuda` only when the user asks to probe CUDA availability. The checker avoids CUDA tensor allocation and does not run training or inference.

## Route Map

| User need | Read this sub-skill | Why |
| --- | --- | --- |
| Install, dependency, Docker, CUDA, checkpoint/data download boundary, or modern-PyTorch import failure | `sub-skills/environment-and-setup/` | Owns legacy runtime and setup troubleshooting. |
| YAML config editing, `data_root`, list files, train/test domain folders, demo-data validation, dataset preparation | `sub-skills/data-and-configuration/` | Owns config and data-loader semantics plus safe validators. |
| Training command construction, `MUNIT` vs `UNIT`, resume, logs, sample grids, checkpoints, long-run planning | `sub-skills/training/` | Owns `train.py` CLI and output/checkpoint behavior. |
| Single-image translation, example-guided style, batch translation, direction flags, output folders, IS/CIS metrics | `sub-skills/inference-and-evaluation/` | Owns `test.py` and `test_batch.py` command builders and failure modes. |
| AdaIN generator, UNIT VAE generator, multi-scale discriminator, losses, state dicts, code porting, architecture edits | `sub-skills/model-internals/` | Owns trainer/network APIs and migration pitfalls. |

## Common Workflow Order

1. Use `environment-and-setup` to choose the legacy runtime and identify blocked CUDA or modern-PyTorch issues.
2. Use `data-and-configuration` to validate the config and dataset paths.
3. Use `training` to construct a dry-run training or resume command.
4. Use `inference-and-evaluation` to construct checkpointed translation and optional metric commands.
5. Use `model-internals` only when changing architecture, porting the code, or explaining trainer/network behavior.

## Public Install Baseline

A historically faithful conda-style setup follows the repository documentation:

```bash
conda create -n munit-legacy python=3.6
conda activate munit-legacy
conda install pytorch=0.4.1 torchvision cuda91 -c pytorch
conda install -c anaconda pyyaml pip
pip install tensorboard tensorboardX
```

The Docker evidence uses a CUDA 9.1/cuDNN 7 Ubuntu 16.04 base. On modern GPUs or modern PyTorch, expect compatibility work; route that to `environment-and-setup` and `model-internals`.

## Repo-Level References

- `references/repo-provenance.md` records the source snapshot, dirty-state note, package/import facts, and evidence paths used to create this skill. Read it before deciding whether to refresh this skill for a changed checkout.
- `references/troubleshooting.md` summarizes cross-cutting MUNIT failures and routes each symptom to the right sub-skill.
- `references/repo-routing-metadata.json` is structured metadata for DisCo's managed repo-skill router when this skill is imported.

## Operating Boundaries

- Do not run `train.py`, `test.py`, `test_batch.py`, or demo dataset scripts as a casual check. Use the bundled dry-run helpers first.
- Do not treat the current working directory, the generation checkout, or any private inspection environment as part of this skill.
- Do not replace real CUDA/checkpoint/dataset verification with synthetic prompt checks when the task requires an actual model result.
- For modernizing the code, preserve MUNIT semantics first: two domains, style/content decomposition, AdaIN parameter assignment, loss weights, checkpoint `a`/`b` dictionaries, and output naming.
