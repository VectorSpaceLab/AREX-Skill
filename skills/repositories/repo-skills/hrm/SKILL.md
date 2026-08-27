---
name: hrm
description: "Use the HRM repository for puzzle dataset preparation, HRM ACT
  model configuration, CUDA training/evaluation, and ARC checkpoint
  post-processing."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# HRM Repo Skill

Use this skill for the `sapientinc/HRM` repository, publicly called
Hierarchical Reasoning Model (HRM). HRM trains a recurrent, hierarchical
reasoning model on ARC, Sudoku, and Maze puzzle datasets using CUDA, PyTorch,
FlashAttention, Hydra config, W&B logging, and checkpoint evaluation scripts.

## When to use

- The user names HRM, Hierarchical Reasoning Model, ARC-AGI, ConceptARC,
  Sudoku Extreme, Maze 30x30, `pretrain.py`, `evaluate.py`, `arc_eval.ipynb`,
  or `puzzle_visualizer.html`.
- The task involves HRM's converted dataset layout with `dataset.json`,
  `identifiers.json`, and `<subset>__*.npy` arrays.
- The task asks about `hrm.hrm_act_v1@HierarchicalReasoningModel_ACTV1`,
  `losses@ACTLossHead`, StableMax loss, ACT halting, sparse puzzle embeddings,
  FlashAttention, or `adam_atan2`.
- The user wants to launch or debug HRM CUDA training/evaluation, checkpoints,
  W&B metrics, or ARC prediction aggregation.

## Sub-skill routing

| Need | Read |
|---|---|
| Build, validate, inspect, or visualize ARC/Sudoku/Maze converted datasets | [data-preparation](sub-skills/data-preparation/SKILL.md) |
| Understand HRM ACT v1 model internals, dynamic identifiers, config fields, losses, or model dependency imports | [model-architecture](sub-skills/model-architecture/SKILL.md) |
| Launch `pretrain.py`, distributed `torchrun`, `evaluate.py`, checkpoint workflows, W&B/offline mode, or ARC post-processing | [training-evaluation](sub-skills/training-evaluation/SKILL.md) |

## Setup snapshot

The repository is a source tree rather than a packaged Python distribution.
Install dependencies in an isolated environment and run from an HRM checkout or
with the checkout on `PYTHONPATH`.

```bash
# PyTorch CUDA first; choose the wheel/index matching the host driver and GPU.
pip install torch torchvision torchaudio --index-url <pytorch-cuda-index>

# FlashAttention: FA2 for Ampere/A100 or earlier, FA3 for Hopper when needed.
pip install flash-attn

# Remaining repository requirements.
pip install -r requirements.txt
```

For hosted experiment tracking, run `wandb login`. For safe smoke/debug runs,
use `WANDB_MODE=offline`. Use `DISABLE_COMPILE=true` to bypass `torch.compile`
while diagnosing shape, dependency, or checkpoint issues.

## Minimal safe checks

```bash
python dataset/build_arc_dataset.py --help
python dataset/build_sudoku_dataset.py --help
python dataset/build_maze_dataset.py --help
WANDB_MODE=offline DISABLE_COMPILE=true python pretrain.py --help
```

After installing CUDA dependencies, run the bundled readiness helper from this
skill:

```bash
python sub-skills/training-evaluation/scripts/check_training_env.py \
  --repo-root /path/to/HRM --require-cuda
```

Read [references/troubleshooting.md](references/troubleshooting.md) when an
install, dataset, model import, W&B, or checkpoint failure spans multiple
sub-skills.

## Provenance and freshness

Read [references/repo-provenance.md](references/repo-provenance.md) before
refreshing this skill or applying it to a different HRM checkout. The skill was
built from HRM commit `ac15626f8db096a63c775b84c9dc868776a6feda` and records
source evidence paths plus verified dependency facts.

Structured router metadata for managed DisCo import is in
[references/repo-routing-metadata.json](references/repo-routing-metadata.json).

## Important boundaries

- Do not ask future agents to open or run original repo docs/notebooks as
  runtime documentation. This skill bundles distilled references plus safe
  helper scripts.
- Full dataset downloads, submodule clones, multi-GPU training, checkpoint
  evaluation, W&B online logging, and browser visualization can be network-,
  storage-, GPU-, or manual-workflow-heavy; request explicit approval before
  running them as verification.
- CPU dataset validation is useful, but HRM model training/evaluation is a
  required CUDA workflow. Do not claim CUDA backend verification from CPU-only
  imports.
- A bounded current-environment model-forward smoke found a possible
  FlashAttention output `.view(...)` stride issue in `models/layers.py`; treat
  full forward/training verification as dependency-sensitive until a bounded
  forward run passes in the target environment.
