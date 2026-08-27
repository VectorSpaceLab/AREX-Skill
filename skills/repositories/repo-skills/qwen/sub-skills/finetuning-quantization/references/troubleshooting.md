# Fine-tuning and Quantization Troubleshooting

## Data format

- Training script complains about JSON: the file is not a list of samples or `conversations` is missing.
- Role mismatch: fine-tuning data should use the repository's `user`/`assistant` conversation format.
- Sequence too long: lower `model_max_length`, trim the samples, or choose a larger-memory recipe.

## Training recipes

- LoRA on a base model with new special tokens and ZeRO3: the repository warns that this combination is incompatible when the new embedding/output layers must train.
- Q-LoRA on a BF16 base checkpoint: wrong model family. Use the Int4 chat checkpoint and fp16.
- Distributed launch fails immediately: check `GPUS_PER_NODE`, `NNODES`, `NODE_RANK`, `MASTER_ADDR`, and `MASTER_PORT`.
- No output saved: verify the output directory and the script's save strategy; the full run only writes checkpoint files after training or adapter save.

## Quantization

- `auto_gptq` import/version errors: the torch/CUDA/Transformers/Optimum/PEFT matrix is incompatible.
- Quantized model loads but special inference features fail: copy the checkpoint-side Python/kernel files the repository mentions.
- GPTQ output has the wrong layout: rename or place the generated weight file where the inference loader expects it.

## Memory and hardware

- OOM during fine-tuning: reduce batch size, gradient accumulation, or sequence length first.
- CPU-only finetuning is not a practical fallback for these repository recipes.
- DeepSpeed errors often reflect recipe/config mismatch rather than a bad checkpoint. Match the shell script and config file first.
