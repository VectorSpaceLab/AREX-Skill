---
name: training-and-experiments
description: "Run and debug H2O LLM Studio training experiments, distributed
  launchers, backend choices, and experiment artifacts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training And Experiments

Use this sub-skill when the task is to launch, monitor, or debug an H2O LLM Studio experiment after a dataset/config has already been chosen. It owns direct CLI training, GUI-launched training behavior, multi-GPU launch mechanics, backend/performance settings, and the files written to an experiment output directory.

## Read These First

- [Training CLI](references/training-cli.md): direct `llm_studio/train.py -Y` runs, deprecated `-C`, dynamic `--section.field` overrides, GUI launch behavior, and multi-GPU commands.
- [Experiment artifacts](references/experiment-artifacts.md): output directory contents, status flags, logs, charts, checkpoints, predictions, and how to decide whether a run finished.
- [Backend and performance](references/backend-and-performance.md): CUDA, DeepSpeed, DDP, LoRA/DoRA/RSLoRA, mixed precision, optimizer/scheduler, and memory/runtime trade-offs.
- [Troubleshooting](references/troubleshooting.md): symptoms, likely causes, recovery checks, and routes to sibling sub-skills for data/model/export issues.

## Bundled Helpers

- [`scripts/make_minimal_config.py`](scripts/make_minimal_config.py): create a tiny CSV plus CPU-like YAML config and print a non-executing training command.
- [`scripts/check_training_environment.py`](scripts/check_training_environment.py): inspect Python, package, PyTorch/CUDA, `CUDA_HOME`, `nvcc`, DeepSpeed importability, and a YAML config without starting training.
- [`scripts/distributed_train_wrapper.sh`](scripts/distributed_train_wrapper.sh): build a validated `torchrun` or `deepspeed` multi-GPU command; dry-run by default and executes only with `--execute`.

## Route Away

- Dataset columns, schema, YAML construction, config class details, and CSV/Parquet validation belong to `../configuration-and-data/SKILL.md`.
- Model wrapper internals, metrics, losses, prediction semantics, and evaluation internals belong to `../modeling-and-evaluation/SKILL.md`.
- Interactive prompting, model-card/export preflights, and Hugging Face publishing belong to `../export-and-prompt/SKILL.md`.
- App startup, work directories, H2O Wave settings, and server lifecycle belong to `../app-and-ui/SKILL.md`.
