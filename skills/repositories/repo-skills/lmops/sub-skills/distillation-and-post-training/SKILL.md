---
name: distillation-and-post-training
description: "MiniLLM, DPKD, and Tuna distillation and ranking-finetuning
  workflows for LMOps."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Distillation and Post-Training

Use this sub-skill for MiniLLM, DPKD, and Tuna workflows that distill or
rank-finetune language models without entering VeRL-style experiential
learning.

## Route here when

- The task is MiniLLM SFT, KD, SeqKD, on-policy MiniLLM training, evaluation,
  exposure-bias analysis, data processing, model resource planning, or tensor
  parallel conversion.
- The task is DPKD training or evaluation, including the runner scripts,
  argument-group choices, DPO-style switches, and checkpoint/output planning.
- The task is Tuna probabilistic ranking or contextual ranking data
  preparation, GPT-4 provenance checks, or ranking-aware finetuning.

## Route away

- GAD, OEL, OPCD, LLM-as-a-Coach, and OPO belong in
  `../rl-experiential-learning/SKILL.md`.
- ResLoRA belongs in `../adaptation-and-training/SKILL.md`.

## Bundled helpers

- `scripts/model_parallel_conversion_plan.py` preflights checkpoint family,
  source/target MP sizes, and path layout before any conversion.
- `scripts/check_tuna_ranking_data.py` validates the minimal probabilistic and
  contextual ranking JSON shapes used by Tuna.

## Read next

- `references/minillm-workflows.md`
- `references/dpkd-workflows.md`
- `references/tuna-data-and-training.md`
- `references/troubleshooting.md`

## Working order

1. Decide whether the request is MiniLLM, DPKD, or Tuna.
2. Check the family reference and the bundled helper before any path-sensitive
   or schema-sensitive action.
3. Treat large model downloads, multi-node launches, and OpenAI-backed
   ranking generation as documented workflow steps, not cheap smoke tests.
4. If a failure looks like a shared LMOps issue, consult the parent skill's
   broad project index when available at `../../references/project-index.md`.
