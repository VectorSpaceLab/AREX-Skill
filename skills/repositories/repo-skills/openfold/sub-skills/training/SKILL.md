---
name: training
description: "Plan OpenFold training, fine-tuning, validation, distillation,
  checkpoint, DeepSpeed, and distributed commands safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# OpenFold Training

Use this sub-skill when the task is to plan or troubleshoot OpenFold training, fine-tuning, distributed execution, DeepSpeed configuration, checkpoint resume, validation, distillation, or `train_openfold.py` command construction.

## Route Quickly

- Start with `references/training-cli-reference.md` for required positionals, key flags, validation rules, and safe command-building conventions.
- Use `references/training-workflows.md` for initial training, fine-tuning, resume, validation, distillation, logging, checkpoints, and experiment config overrides.
- Use `references/distributed-and-deepspeed.md` for GPU/node strategy, `--seed`, MPI, Slurm handoff, DeepSpeed JSON, BF16/A100 guidance, and precision conflicts.
- Use `references/troubleshooting.md` for missing caches/indexes, runtime imports, GPU impossibility, logging, DeepSpeed, and checkpoint failures.
- Run `scripts/build_training_command.py` to assemble a validated dry-run command; it prints shell-quoted argv and never launches training.
- Run `scripts/build_deepspeed_config.py` to generate a deterministic DeepSpeed config JSON without importing OpenFold or DeepSpeed.
- Copy and edit `templates/experiment_config.json` when the user needs a flattened `--experiment_config_json` override.

## Boundaries

- Route mmCIF/MSA layout creation, alignment DB/index construction, chain/mmCIF cache generation, duplicate-chain expansion, cluster files, and data validation to `../data-preparation/`.
- Route CUDA/PyTorch/DeepSpeed/MPI/W&B installation, optional extension failures, databases, parameters, and runtime asset readiness to `../installation-assets/`.
- Route low-level model APIs, config internals, checkpoint conversion APIs, JAX/OpenFold weight import details, and acceleration internals to `../model-apis/`.
- Route inference, relaxation, template search for prediction, and prediction output interpretation to `../inference/`.

## Operating Rules

- Treat helpers in this sub-skill as planners only: they must not download data, submit jobs, import OpenFold, import DeepSpeed, or start training.
- Preserve user-supplied paths exactly; do not assume a checkout path, data root, environment prefix, cluster partition, account, or private cache directory.
- For multi-GPU or multi-node training, always include `--seed`; OpenFold rejects distributed training without it.
- For DeepSpeed, prefer BF16 (`--precision bf16` or `bf16-mixed` depending on the installed Lightning version and local policy) on A100-class hardware and do not combine DeepSpeed with Lightning precision `16`.
- If CLI help/imports fail because optional compiled extensions such as `attn_core_inplace_cuda` are missing, document the environment gap instead of claiming full CLI verification.
