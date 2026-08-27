---
name: trlx
description: "Guides trlX LLM post-training, RLHF, Accelerate, configuration,
  sweeps, and optional NeMo/Megatron workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# trlX repo skill

Use this skill when a task involves trlX (`trlx`), the CarperAI Transformer Reinforcement Learning X package for fine-tuning language models with RLHF-style workflows.

## Read this skill for

- `trlx.train` usage, signatures, argument modes, callbacks, and trainer return objects.
- PPO, ILQL, SFT, and RFT post-training recipes for causal or seq2seq language models.
- Reward-function training, reward-labeled sample training, prompt/completion SFT, PEFT, checkpoints, logging, and generation evaluation.
- `TRLConfig`/YAML/default config editing, trainer/method/pipeline matching, optimizer/scheduler names, and data pipeline contracts.
- Hugging Face Accelerate and DeepSpeed launch planning for trlX training scripts.
- Ray Tune sweeps with `python -m trlx.sweep` and trlX dot-path config updates.
- Optional NVIDIA NeMo/Megatron workflows, `.nemo` or rank-sharded checkpoints, and NeMo config wiring.

## Do not use this skill for

- General RL libraries such as Gymnasium, Stable-Baselines3, CleanRL, or Tianshou unless the task explicitly uses trlX.
- Generic NeMo workflows that do not touch trlX trainer/model wrappers.
- Long maintainer benchmark/report workflows that clone branches, run full GPU examples, and publish W&B reports; those were excluded from runtime guidance.
- Training execution itself when dependencies, datasets, credentials, or hardware are unavailable; first use the checks and troubleshooting references.

## Fast route map

| If the task mentions... | Go to |
| --- | --- |
| `trlx.train`, `reward_fn`, `prompts`, `samples`, `rewards`, PPO, ILQL, SFT, RFT, PEFT, checkpoints, Accelerate, DeepSpeed, or sweeps | [training sub-skill](sub-skills/training/SKILL.md) |
| NeMo, Megatron, Apex, `.nemo`, `NeMoPPOTrainer`, `NeMoILQLTrainer`, `NeMoSFTTrainer`, `PPOGPT`, `ILQLGPT`, `SFTGPT`, `mp_rank_XX`, or NeMo YAMLs | [nemo sub-skill](sub-skills/nemo/SKILL.md) |
| Package purpose, install shape, supported algorithms/backends, root route selection, or verified inspection facts | [package overview](references/package-overview.md) |
| Import failures, dependency conflicts, CUDA/DeepSpeed setup, missing NeMo, W&B/Ray import behavior, or launcher environment mismatch | [root troubleshooting](references/troubleshooting.md) |
| Staleness, source commit, package version, evidence paths, or whether to refresh this skill | [repo provenance](references/repo-provenance.md) |

## Minimal install and import check

For full training stacks, use a Python 3.9-3.11 environment. Install a CUDA-capable PyTorch matching the host hardware when GPU training is needed, then install trlX from a public source or a current checkout. A typical source-checkout path is:

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
```

When installing directly from the public repository, install the appropriate PyTorch wheel first because trlX's package metadata does not fully replace the repository's pinned runtime requirements.

After installation, run the bundled safe helper from this skill tree:

```bash
python scripts/check_trlx_install.py
python scripts/check_trlx_install.py --cuda
python scripts/check_trlx_install.py --json
```

The helper imports trlX, prints the `trlx.train` signature, registries, default config summaries, and optionally performs a tiny CUDA allocation. It does not download models or start training.

## Backend notes

- Accelerate-backed trlX APIs and CUDA-capable PyTorch import were verified for this skill's source snapshot.
- NeMo/Apex/Megatron was intentionally not installed in the minimum inspection environment. The NeMo sub-skill is source-backed and must not be treated as verified backend coverage until a NeMo/Apex environment is prepared.
- Many public examples require Hugging Face model/dataset downloads, W&B, Triton, Ray, large GPU memory, or multi-node launchers. The skill distills their patterns instead of making future agents run original source examples.
