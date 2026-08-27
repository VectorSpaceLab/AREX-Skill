---
name: data-training
description: "Support data preparation, dataloaders, metrics, checkpoints,
  optimizer/scheduler args, and distributed/deepspeed/Megatron training
  guidance."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# data-training

Use this sub-skill when you need to shape Fengshen data or training commands, not when you need to choose a model family or a CLI entry point.

## Covers

- `UniversalDataModule` and `UniversalCheckpoint`
- `model_utils` optimizer/scheduler args and `configure_optimizers`
- `metric/utils_ner`, `EntityScore`, `SeqEntityScore`, and span helpers
- sequence-tagging collators/datasets and decode-type selection
- task / medical QA / LCSTS / T5 / BERT / Megatron / mmap dataloaders
- pretraining data formats and cache/shard workflows
- the custom `megatron_deepspeed` strategy wrapper
- optional Megatron fused CUDA kernels

## Route elsewhere

- model family selection, configs, and tokenizer choice -> model-zoo
- `fengshen-pipeline` CLI command surface -> pipelines-cli
- example-specific recipes, conversions, or one-off demos -> examples-conversion

## Start here

1. [references/data-formats.md](references/data-formats.md)
2. [references/training-arguments.md](references/training-arguments.md)
3. [references/pretraining-workflows.md](references/pretraining-workflows.md)
4. [references/distributed-training.md](references/distributed-training.md)
5. [references/metrics-and-validation.md](references/metrics-and-validation.md)
6. [references/troubleshooting.md](references/troubleshooting.md)

## Bundled checks

- [scripts/check_ner_labels.py](scripts/check_ner_labels.py) validates tiny BIO/BIOES label sequences and calls `get_entities` without downloads.
- [scripts/inspect_training_args.py](scripts/inspect_training_args.py) prints the grouped argparse destinations that are available in the current environment.

## Common questions this skill answers

- Which collator should I use for sequence-tagging data?
- What fields must appear in a JSONL, BMES, QA, LCSTS, T5, or mmap record?
- Which flags belong to data prep, checkpointing, trainer runtime, or optimizer scheduling?
- How do I resume pretraining without losing consumed-sample accounting?
- When does DeepSpeed use `DeepSpeedCPUAdam` vs `FusedAdam`?
- What breaks when Megatron fused kernels are not compiled?

## Fast routing hints

- For sequence tagging, match the label file and `decode_type` first.
- For pretraining, separate data conversion, runtime, optimizer, and checkpoint flags before editing a shell script.
- For distributed runs, keep `replace_sampler_ddp=False` when a custom sampler is in use.
- For validation, confirm the label markup and entity-span format before trusting F1.
