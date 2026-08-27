---
name: post-training-recipes
description: "Select and adapt torchtune post-training recipes without launching
  expensive jobs accidentally."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Post-Training Recipes

Use this sub-skill when an agent must choose, customize, or explain a torchtune training recipe for supervised finetuning, LoRA, QLoRA, DoRA, DPO, PPO, KD, QAT, distributed training, or multi-node launch planning.

Do not use it for generation, Eleuther evaluation, post-training quantization conversion, or general CLI/config syntax. Route those to sibling skills.

## Safe Default

Training recipes can download gated artifacts, allocate GPUs, start network rendezvous, or consume long cluster jobs. Build and inspect commands first; only run them after the user explicitly approves the hardware, dataset, checkpoint, credential, and output-dir choices.

Use the bundled command builder to construct a safe dry command:

```bash
python sub-skills/post-training-recipes/scripts/build_tune_command.py \
  lora_finetune_distributed llama3_2/3B_lora \
  --nnodes 2 --nproc-per-node 8 \
  --rdzv-endpoint '<head-node>:29500' \
  --override checkpointer.checkpoint_dir='<checkpoint-dir>' \
  --override output_dir='<output-dir>'
```

The script prints `tune run ...`; it never executes training.

## Route By Task

- For built-in recipe selection, lifecycle coverage, and safe launch patterns, read [references/recipe-workflows.md](references/recipe-workflows.md).
- For config names, copied config editing, overrides, LoRA/QLoRA/DoRA/QAT settings, and validation preflights, read [references/recipe-configs.md](references/recipe-configs.md).
- For `torchrun`, SLURM, rendezvous, and multi-node placement rules, read [references/distributed-and-multinode.md](references/distributed-and-multinode.md).
- For GPU, dependency, checkpoint, distributed, precision, and optional logger failures, read [references/troubleshooting.md](references/troubleshooting.md).

## Boundaries And Cross-Links

- Use `tune ls`, `tune cp`, `tune cat`, `tune validate`, and `tune run`; do not import the `recipes` package directly, because it intentionally is not an importable API surface.
- Put torchrun flags before the recipe name and recipe/config overrides after `--config`.
- Cross-link to `../cli-and-config/SKILL.md` for general CLI/config mechanics and OmegaConf override syntax.
- Cross-link to `../data-and-datasets/SKILL.md` before changing dataset components or data schemas.
- Cross-link to `../training-utilities-and-rlhf/SKILL.md` for checkpointers, precision utilities, logging, profiling, and RLHF utility internals.
- Cross-link to `../inference-evaluation-quantization/SKILL.md` after a training checkpoint exists and the task moves to generation, evaluation, or quantization conversion.
