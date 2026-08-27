# DeepSpeed, Precision, and Hardware

## Installation notes

The repository's finetuning examples rely on PyTorch, Transformers, PEFT, DeepSpeed, and sometimes AutoGPTQ/Optimum. The exact compatible matrix depends on the desired path:

- Full fine-tuning and LoRA: Torch + Transformers + DeepSpeed + PEFT.
- Q-LoRA: Int4 checkpoint + DeepSpeed + fp16 + PEFT + AutoGPTQ-compatible setup.
- Quantization: AutoGPTQ + Optimum + a compatible torch/CUDA wheel.

## Hardware planning

| Path | Hardware expectation | Notes |
| --- | --- | --- |
| Full fine-tuning | multi-GPU or large-memory GPU | the repository's shell scripts are distributed-first |
| LoRA | single or multi-GPU | base-model LoRA with new tokens may need trainable embeddings/output layers |
| Q-LoRA | GPU with enough memory for Int4 + adapter training | repository scripts use fp16 and DeepSpeed |
| Multinode | multiple nodes and explicit `NNODES`/`NODE_RANK`/`MASTER_ADDR`/`MASTER_PORT` | network/launch coordination required |
| GPTQ | GPU and calibration data | quantization runs can be long and memory-heavy |

## Precision and stage choices

- BF16 is the default in many repository scripts when hardware supports it.
- FP16 is used for Q-LoRA and some fallback GPU paths.
- DeepSpeed ZeRO2 and ZeRO3 are not interchangeable; the repository uses ZeRO3 for some distributed full-tune paths and ZeRO2 for several LoRA paths.
- The repository warns that ZeRO3 is incompatible with LoRA when finetuning a base model with trainable new tokens.
- If memory is tight, the first variables to adjust are model size, sequence length, batch size, and precision before changing the whole training recipe.

## What to check before a real run

1. Confirm the checkpoint is the right family and format (base/chat/Int4).
2. Confirm the data schema and sequence lengths.
3. Confirm the DeepSpeed config file matches the chosen recipe.
4. Confirm the output directory is empty or intentionally reused.
5. Confirm the hardware can fit the batch, precision, and sequence length budget.
