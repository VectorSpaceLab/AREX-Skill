# Training workflows

## Configuration layers

Dexbotic experiments compose model, data, trainer, and inference configuration. The important invariants are:

- `model_name_or_path` identifies a compatible base/checkpoint and must not be an arbitrary text-model directory.
- `dataset_name` must be present in the process-local registration registry; see [data-preparation](../../data-preparation/SKILL.md).
- `output_dir` must be writable and must not be an input checkpoint directory.
- `num_images`, `images_keys`, action dimension, state dimension, and camera order must agree.
- `bf16`/`tf32`, batch size, gradient accumulation, worker count, and checkpoint cadence must fit the selected hardware.
- `deepspeed`, `fsdp`, `fsdp_config`, and `fsdp_version` are backend-specific; do not carry settings between backends without checking their ownership.

## Standard SFT

The high-level flow is: register/import data source → build data processors and model config → select trainer backend → initialize norm stats → launch with the distributed runner → save checkpoint and stats → use the checkpoint in inference config. Start with a tiny bounded subset and inspect a batch before scaling.

## LoRA

LoRA is a parameter-efficient variant with model-family-specific target modules and documented recipe constraints. The validated Libero LoRA recipes use `--train-backend ddp`; their entrypoints reject DeepSpeed and FSDP. Treat that as an invariant, not a suggestion. Verify trainable parameter counts and the adapter/checkpoint save layout before evaluating.

## Model families

Dexbotic includes DM0, CogACT, Pi0/Pi05, OFT, discrete VLA, GR00T variants, MemVLA, NaviLA/Uni-NaVid, and hybrid experiments. The family determines action pipeline, prompt format, checkpoint loader, and serving wrapper. Do not select a family solely by a model-name string: inspect the experiment's model/data/inference config and its expected action contract.

## Checkpoints

FSDP may save sharded state dictionaries. Merge sharded weights with the supported Accelerate utility before using a consumer that expects a consolidated checkpoint. A checkpoint without matching `norm_stats.json`, tokenizer/processor metadata, or action-space metadata is not deployment-ready.
