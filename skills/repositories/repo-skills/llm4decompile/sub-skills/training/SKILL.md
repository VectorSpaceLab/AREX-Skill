---
name: training
description: "Train, fine-tune, or prepare datasets for LLM4Decompile models."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Training

Use this sub-skill when the user wants to train or fine-tune an LLM4Decompile checkpoint, prepare a training dataset, or inspect the repo's DeepSpeed, ColossalAI, or LLaMA-Factory launch paths.

## Covers

- supervised fine-tuning with `train/finetune.py`
- AnghaBench-style dataset generation with `train/compile.py`
- continual-pretraining dataset splicing with `train/colossalai_llm4decompile/prepare_pretrain_dataset.py`
- LLaMA-Factory dataset registry and YAML examples under `train/llama_factory_llm4decompile/`
- launcher patterns in `train/run_training.sh` and `train/colossalai_llm4decompile/run_llm4decompile_train.sh`

## Excludes

- benchmark scoring and inference-only flows → use `evaluation`
- Ghidra pseudo-code extraction or refinement → use `ghidra-refine`
- SK²Decompile preprocessing, RL, and BringUpBench evaluation → use `sk2decompile`

## Start Here

1. Read [`references/training-workflows.md`](references/training-workflows.md) for the training family map.
2. Read [`references/data-formats.md`](references/data-formats.md) before editing configs or datasets.
3. Read [`references/troubleshooting.md`](references/troubleshooting.md) if the environment or launcher fails.
4. Use the bundled scripts in this sub-skill's `scripts/` directory rather than source-checkout paths.

## Common routes

### Supervised fine-tuning

Use this route when the request mentions:

- `deepspeed`
- `finetune.py`
- `llm4binary_v1`
- `pseudo2norm`
- `norm2code`

Good entry points:

- `scripts/run_llamafactory_train.sh`
- `scripts/finetune.py`

### Dataset generation

Use this route when the request mentions:

- compiling raw C sources into trainable examples
- AnghaBench or similar source corpora
- JSONL output with optimization-level assembly maps

Good entry points:

- `scripts/compile_dataset.py`
- `scripts/prepare_pretrain_dataset.py`

### ColossalAI pretraining

Use this route when the request mentions:

- continual pretraining
- spliced Arrow datasets
- `colossalai run`
- `prepare_pretrain_dataset.py`

Good entry points:

- `scripts/prepare_pretrain_dataset.py`
- `scripts/run_colossalai_train.sh`

## Model and data signals

- The repository's example dataset registry key is `llm4binary_v1`.
- The example LLaMA-Factory configs are `pseudo2norm-example.yaml` and `norm2code-example.yaml`.
- Training commands in the repo assume a CUDA-capable torch stack, BF16-capable hardware when `bf16` is enabled, and a checkpoint path that matches the selected family.

## When to read the bundled references

- Use the workflow reference for command templates and decision points.
- Use the data-format reference to validate JSON, JSONL, and registry names before launching a long run.
- Use the troubleshooting reference for dependency, CUDA, or launcher failures.
