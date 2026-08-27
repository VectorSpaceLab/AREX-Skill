# V1 Architecture

LlamaFactory v1 is an experimental architecture selected by setting `USE_V1=1` before entering the normal CLI entry points `llamafactory-cli` or `lmf`. Without that environment variable, the CLI routes to the default v0 launcher.

## Launcher Routing

- `USE_V1=1 llamafactory-cli sft config.yaml` routes into the v1 launcher and SFT trainer.
- `USE_V1=1 llamafactory-cli train config.yaml` is treated like v1 SFT.
- `USE_V1=1 llamafactory-cli rm config.yaml` routes into the v1 reward-model trainer.
- `USE_V1=1 llamafactory-cli chat config.yaml` routes into the v1 CLI sampler.
- `USE_V1=1 llamafactory-cli merge config.yaml` routes to the v1 LoRA merge/export helper.
- v1 `dpo`, `env`, and `version` are not complete in the current source; do not promise them as working v1 commands.

For multi-device v1 training, the v1 launcher can re-execute through `torchrun` for `train`, `sft`, `dpo`, and `rm` when `FORCE_TORCHRUN=1` or more than one device is visible and Ray/KT are not active. It forwards the original subcommand into the re-executed script so downstream trainers still receive the config path.

## Layering

The v1 stack is organized around fewer, more explicit components than v0:

- `config`: dataclasses for model, data, training, and sampling arguments; YAML/JSON loading; CLI override merging; plugin config normalization.
- `core`: reusable `DataEngine`, `ModelEngine`, `BaseTrainer`, `BaseSampler`, rendering, batching, inference, checkpoint, and callback utilities.
- `accelerator`: distributed device/rank/world-size helpers, profiling, and interface state.
- `plugins`: extension points for data loading/conversion, model initialization, PEFT, quantization, kernels, distributed trainer wrapping, batching, optimizer, and scheduler behavior.
- `trainers`: concrete v1 trainers layered on `BaseTrainer`, currently including SFT and RM implementations.
- `samplers`: CLI sampler wrapper over the core sampler and inference engine.

## Core Engines

### DataEngine

`DataEngine` accepts a single `train_dataset` or `eval_dataset` path. It can interpret:

- Local dataset-info YAML files.
- Dataset-info YAML files hosted in a dataset repository.
- Existing local dataset paths.
- Direct Hugging Face dataset IDs.

Dataset-info entries may specify a dataset `source`, `split`, `streaming`, `size`, `weight`, and `converter`. Mixing streaming and non-streaming datasets is rejected. Index access is available for map-style datasets; streaming index access is not implemented.

Converter plugins normalize raw records into v1 message structures. Built-in converter names include `alpaca`, `sharegpt`, and `pair`. Pair conversion is important for RM-style chosen/rejected data.

### ModelEngine

`ModelEngine` initializes the processor, renderer, model config, model weights, optional quantization, optional PEFT/freeze adapter behavior, and optional kernel patches. `model_class` selects the HF auto class:

- `llm`: causal LM or image-text-to-text when the config maps to that class.
- `cls`: token-classification style model with one label, used by RM setup.
- `other`: generic auto model.

Plugin blocks drive most optional behavior:

- `init_config`: model initialization device policy such as `init_on_meta`, `init_on_rank0`, or `init_on_default`.
- `peft_config`: `lora` or `freeze` behavior, adapter resume/merge behavior, and export settings for merge.
- `kernel_config`: automatic kernel application or `liger_kernel` where dependencies and model support allow it.
- `quant_config`: `auto` or `bnb` quantization, usually with `quantization_bit` 4 or 8.

### BaseTrainer

`BaseTrainer` owns batch generation, training-step accounting, activation checkpointing, distributed/model sharding, optimizer and scheduler initialization, checkpoint resume/save, callbacks, logging, loss scaling by valid tokens, gradient clipping, and final model save. Concrete trainers implement `compute_loss`.

Important training constraints:

- `batching_strategy: dynamic_batching` requires a positive `max_steps` and cannot use `save_epochs`.
- `batching_strategy: padding_free` requires `flash_attn: flash_attention_2`.
- Context parallelism through `cp_size > 1` currently requires FSDP2 and flash attention; RM disallows `cp_size > 1`.
- `save_ckpt_as_hf: true` can double save-time memory usage.

### SFTTrainer

V1 SFT uses renderer-produced `loss_weights` and token log probabilities. It trains from `train_dataset`, constructs `ModelEngine(..., is_train=True)`, fits, saves the model, and destroys the distributed interface.

### RMTrainer

V1 RM sets `model_class` to `cls`, validates that the first dataset sample contains `chosen_messages` and `rejected_messages`, initializes a score head, and computes pairwise reward loss. If the data is raw chosen/rejected records, use a dataset converter that produces pair-format messages.

### Sampler

The v1 CLI sampler uses `sample_backend: hf` through the `HuggingFaceEngine`. A non-HF sample backend is present in the enum, but the base sampler currently raises for unknown/non-HF backends. Treat vLLM-style sampling as not ready in v1 unless the source explicitly implements it in the target version.

## Migration Caveats

- v1 is not a drop-in replacement for v0. It does not use v0 `stage`, `dataset`, `dataset_dir`, `finetuning_type`, `per_device_train_batch_size`, `gradient_accumulation_steps`, `do_train`, or `predict_with_generate` as primary config keys.
- v1 examples use `train_dataset`, `micro_batch_size`, and plugin blocks instead of v0’s stage/fine-tuning fields.
- v1 DPO trainer files exist but launcher execution is not enabled; route production DPO requests to v0 unless the user is explicitly developing v1 DPO.
- Many v1 tests are gated by accelerator type, Transformers version, and optional dependencies; static validation is safer than promising a local full run.
