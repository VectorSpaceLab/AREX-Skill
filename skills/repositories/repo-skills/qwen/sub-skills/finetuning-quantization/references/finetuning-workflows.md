# Fine-tuning Workflows

## Full-parameter fine-tuning

The historical script `finetune/finetune_ds.sh` launches `finetune.py` under `torchrun` with DeepSpeed. It is distributed-first and expects a GPU-aware environment. Use this when the user wants to update the full model rather than only adapter weights.

Typical command shape:

```bash
bash finetune/finetune_ds.sh -m Qwen/Qwen-7B -d /path/to/data.json
```

Relevant behavior from `finetune.py`:

- Model, data, training, and LoRA arguments are parsed with Hugging Face dataclasses.
- `model_max_length` defaults to 8192.
- `TrainingArguments.use_lora` toggles adapter mode.
- `safe_save_model_for_hf_trainer` writes full weights or the LoRA state dict depending on configuration.

## LoRA

Single-GPU and distributed LoRA scripts exist. The important tradeoffs are:

- The repository uses bf16 by default when possible.
- For a base model with new ChatML tokens, trainable embeddings/output layers may be needed.
- If the user is LoRA-fineturning a base model and uses DeepSpeed ZeRO3 with trainable new tokens, the repository warns that the combination is incompatible.
- For chat models, the script usually keeps `modules_to_save` unset and can avoid the special-token issue.

Typical command shapes:

```bash
bash finetune/finetune_lora_single_gpu.sh -m Qwen/Qwen-7B -d /path/to/data.json
bash finetune/finetune_lora_ds.sh -m Qwen/Qwen-7B-Chat -d /path/to/data.json --deepspeed finetune/ds_config_zero2.json
```

## Q-LoRA

Q-LoRA uses the Int4 chat checkpoint and fp16 rather than BF16. The repository documents that single-GPU Q-LoRA requires DeepSpeed for the mixed-precision path and that the Int4 model already knows the ChatML special tokens.

Typical command shapes:

```bash
bash finetune/finetune_qlora_single_gpu.sh -m Qwen/Qwen-7B-Chat-Int4 -d /path/to/data.json
bash finetune/finetune_qlora_ds.sh -m Qwen/Qwen-7B-Chat-Int4 -d /path/to/data.json
```

## Adapter merge and export

The repository shows LoRA adapter merge with `AutoPeftModelForCausalLM` and `merge_and_unload()`. After merge, save the tokenizer too. The `*.cu`/`*.cpp` note matters when the checkpoint will later use KV-cache support.

Do not promise merge for Q-LoRA adapters; the repository only documents merge for LoRA.

## GPTQ quantization

`run_gptq.py` quantizes a fine-tuned checkpoint from calibration data:

```bash
python run_gptq.py --model_name_or_path /path/to/model --data_path /path/to/calibration.json --out_path /path/to/output --bits 4 --group-size 128
```

The calibration data should use the same conversation structure as fine-tuning data. After quantization, the repository describes copying Python and checkpoint-side support files and renaming the generated weight file to match the final model layout.
