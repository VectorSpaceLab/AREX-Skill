---
name: datasets
summary: "Manage rLLM datasets, task layouts, registries, and eval-to-training
  data curation."
description: "Use rLLM dataset APIs and CLI for dataset registration, local
  benchmark/task formats, verifier metadata, Harbor-compatible layouts, and SFT
  data curation from eval episodes."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# rLLM Datasets and Tasks

Use this sub-skill when the task mentions `rllm dataset`, `DatasetRegistry`, `BenchmarkLoader`, `dataset.toml`, `task.toml`, `task_path`, local benchmark directories, Harbor datasets, registered splits, or converting evaluation episodes into SFT data.

## Start Here

1. Read `references/dataset-operations.md` for CLI workflows: list, pull, info, inspect, register, remove, and `from-eval`.
2. Read `references/data-formats.md` for file formats, task directory shapes, verifier metadata, and how rows become `Task` objects.
3. Read `references/troubleshooting.md` when a dataset cannot be found, loaded, inspected, or scored.
4. Switch to `../evaluation/SKILL.md` for actually running an agent on the dataset, and `../training/SKILL.md` for RL/SFT consumption.

## Ownership Boundaries

- This sub-skill owns **data shape and registry state**, not provider/model setup.
- It owns the **task/verifier metadata** that evaluation and training consume.
- It does not prove the evaluator/verifier succeeds; use evaluation/training sub-skills for runtime execution.

## Safe Check

For a local benchmark directory, run:

```bash
python scripts/inspect_task_layout.py /path/to/benchmark
```

The helper is read-only. It reports `dataset.toml`, per-task directories, data files, and environment/test directories without executing verifiers.
