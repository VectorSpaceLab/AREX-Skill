# Fine-tuning workflows

These workflows are self-contained for the generated skill tree. Commands assume the current directory is the `fine-tuning` sub-skill directory so that `scripts/train_alpaca_sft.py` and `scripts/default_offload_opt_param.json` resolve without the original repository checkout.

## 1. CPU-side preparation and command planning

Use this flow when the user wants to prepare or review a training run without launching GPU training.

1. Confirm the data handoff from `dataset-and-prompts`.
   - `data_path` should point to a validated Alpaca-style JSON training file.
   - This sub-skill only consumes that file. Do not duplicate prompt/schema validation here.
2. Check the trainer argument surface without loading a model:

   ```bash
   python scripts/train_alpaca_sft.py --help
   ```

   The help should expose `--model_name_or_path`, `--data_path`, `--output_dir`, `--model_max_length`, `--fsdp`, `--fsdp_transformer_layer_cls_to_wrap`, and `--deepspeed` through `HfArgumentParser` plus Hugging Face `TrainingArguments`.
3. Build a launch command safely:

   ```bash
   python scripts/build_training_command.py \
     --model_name_or_path <hf-llama-or-opt-checkpoint> \
     --data_path <validated_alpaca_json> \
     --output_dir <output_dir> \
     --model_family llama \
     --recipe fsdp-full-shard
   ```

   The builder prints shell text only. It does not import Torch, launch `torchrun`, write checkpoints, or open the dataset.
4. Confirm batch-size math before launch:

   ```text
   global_batch_size = nproc_per_node * per_device_train_batch_size * gradient_accumulation_steps
   ```

   The documented 4-GPU recipe uses `4 * 4 * 8 = 128`. If you change GPU count or micro-batch size, adjust accumulation if you want to keep the same global batch.
5. Optional CPU smoke scope: a future verification task may run parser/help, command builder, JSON/data loading, and a tiny tokenizer/model fixture. Do not report this as full FSDP or DeepSpeed training verification.

## 2. LLaMA FSDP full-shard recipe

Use this when the user has a Hugging Face-converted LLaMA checkpoint and tokenizer and enough GPU memory for the documented FSDP path. The repository README used 4 A100 80GB GPUs for LLaMA-7B.

```bash
torchrun --nproc_per_node=4 --master_port=<port> scripts/train_alpaca_sft.py \
    --model_name_or_path <hf_converted_llama_checkpoint_and_tokenizer> \
    --data_path <validated_alpaca_json> \
    --bf16 True \
    --output_dir <output_dir> \
    --num_train_epochs 3 \
    --per_device_train_batch_size 4 \
    --per_device_eval_batch_size 4 \
    --gradient_accumulation_steps 8 \
    --evaluation_strategy "no" \
    --save_strategy "steps" \
    --save_steps 2000 \
    --save_total_limit 1 \
    --learning_rate 2e-5 \
    --weight_decay 0. \
    --warmup_ratio 0.03 \
    --lr_scheduler_type "cosine" \
    --logging_steps 1 \
    --fsdp "full_shard auto_wrap" \
    --fsdp_transformer_layer_cls_to_wrap LlamaDecoderLayer \
    --tf32 True
```

Operational notes:

- `--model_name_or_path` must resolve to both model weights/config and a matching tokenizer.
- `--fsdp_transformer_layer_cls_to_wrap LlamaDecoderLayer` is the LLaMA auto-wrap class.
- The trainer adds missing tokenizer special tokens and resizes embeddings before data loading.
- `--model_max_length` defaults to 512; pass a different value only after reviewing truncation and memory impact.

## 3. OPT FSDP full-shard recipe

Use this for OPT-style causal language models. The key difference from the LLaMA command is the model path and FSDP layer class.

```bash
torchrun --nproc_per_node=4 --master_port=<port> scripts/train_alpaca_sft.py \
    --model_name_or_path facebook/opt-6.7b \
    --data_path <validated_alpaca_json> \
    --bf16 True \
    --output_dir <output_dir> \
    --num_train_epochs 3 \
    --per_device_train_batch_size 4 \
    --per_device_eval_batch_size 4 \
    --gradient_accumulation_steps 8 \
    --evaluation_strategy "no" \
    --save_strategy "steps" \
    --save_steps 2000 \
    --save_total_limit 1 \
    --learning_rate 2e-5 \
    --weight_decay 0. \
    --warmup_ratio 0.03 \
    --lr_scheduler_type "cosine" \
    --logging_steps 1 \
    --fsdp "full_shard auto_wrap" \
    --fsdp_transformer_layer_cls_to_wrap OPTDecoderLayer \
    --tf32 True
```

If the model family is not LLaMA or OPT, use the appropriate Transformer block class for `--fsdp_transformer_layer_cls_to_wrap`; otherwise FSDP auto-wrap may miss the intended layers or fail during wrapping.

## 4. FSDP CPU offload memory-reduction recipe

Use FSDP CPU offload when full shard still exceeds VRAM but the user accepts slower host-device transfers.

Change only the FSDP mode:

```bash
--fsdp "full_shard auto_wrap offload"
```

Keep the layer class (`LlamaDecoderLayer` or `OPTDecoderLayer`) aligned with the model family. Offload can reduce VRAM pressure, but it can also substantially slow training and increase CPU memory and PCIe/NVLink traffic.

## 5. DeepSpeed ZeRO-3 CPU offload recipe

Use this when DeepSpeed stage 3 with CPU optimizer and parameter offload is preferred or FSDP offload is still not memory-efficient enough.

Install DeepSpeed in the training environment before launch:

```bash
pip install deepspeed
```

Then launch with the bundled config:

```bash
torchrun --nproc_per_node=4 --master_port=<port> scripts/train_alpaca_sft.py \
    --model_name_or_path <hf_converted_llama_checkpoint_and_tokenizer> \
    --data_path <validated_alpaca_json> \
    --bf16 True \
    --output_dir <output_dir> \
    --num_train_epochs 3 \
    --per_device_train_batch_size 4 \
    --per_device_eval_batch_size 4 \
    --gradient_accumulation_steps 8 \
    --evaluation_strategy "no" \
    --save_strategy "steps" \
    --save_steps 2000 \
    --save_total_limit 1 \
    --learning_rate 2e-5 \
    --weight_decay 0. \
    --warmup_ratio 0.03 \
    --deepspeed scripts/default_offload_opt_param.json \
    --tf32 True
```

Do not combine the DeepSpeed recipe with `--fsdp` flags in the same command. Choose one sharding/offload strategy per run.

## 6. Choosing epochs and learning rate

The README reports these starting points:

| Model target | Global batch | Learning rate | Epochs | Max length | Weight decay |
| --- | ---: | ---: | ---: | ---: | ---: |
| LLaMA-7B | 128 | `2e-5` | 3 | 512 | 0 |
| LLaMA-13B | 128 | `1e-5` | 5 | 512 | 0 |

For OPT or other causal LMs, treat the OPT-6.7B command as a compatibility example, not an optimal hyperparameter claim.

## 7. Output expectations

The trainer calls `trainer.train()`, then `trainer.save_state()`, then `trainer.save_model(output_dir=training_args.output_dir)`. With the documented save settings, checkpoints are written every 2000 steps and `save_total_limit=1` keeps only one checkpoint. Plan output storage accordingly before launching a long run.
