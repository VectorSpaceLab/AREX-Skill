# Finetuning Workflows

The 2.5 finetuning entrypoint is `finetune.py`. The checked-in shell templates wrap it with `torchrun`, set distributed rendezvous variables, and pass Hugging Face `TrainingArguments` plus repo-specific data and LoRA arguments.

## Pre-flight order

1. Validate `data.json` or `data.txt` with `scripts/validate_finetune_data.py`.
2. Choose full-parameter or LoRA mode.
3. Choose one backend strategy: DeepSpeed or FSDP, not both.
4. Render an editable command with `scripts/render_finetune_command.py`.
5. Confirm model/checkpoint path, data paths, GPU count, output directory, and package versions before execution.

## Bundled self-contained training bundle

Use `entrypoints/xcomposer25/` for approved execution. It contains the source-derived `finetune.py`, local imports (`data_mix.py`, `ixc_utils.py`), `ds_config_zero2.json`, PEFT merge script, source-format example data, and launch wrappers. This is the preferred self-contained path because it does not require the original checkout.

```bash
# From the finetuning sub-skill root, validate bundled example format.
python scripts/validate_finetune_data.py entrypoints/xcomposer25/data.txt --family 2.5

# Real LoRA training after explicit model/data/GPU approval.
cd entrypoints/xcomposer25
MODEL=/models/internlm-xcomposer2d5-7b DATA=/data/my_data.txt GPUS_PER_NODE=8 OUTPUT_DIR=/runs/ixc_lora ./launch_lora.sh

# Real full-parameter training after explicit approval.
MODEL=/models/internlm-xcomposer2d5-7b DATA=/data/my_data.txt GPUS_PER_NODE=8 OUTPUT_DIR=/runs/ixc_full ./launch_full.sh
```

The wrappers resolve the bundled `finetune.py` and `ds_config_zero2.json` using their own directory. If `DATA` is a relative manifest path, it is resolved after the wrapper changes into the bundle directory; prefer absolute data paths for real runs.

### Bundled PEFT adapter merge

After LoRA training, merge with the bundled script rather than reopening source files:

```bash
cd entrypoints/xcomposer25
python merge_peft_adapter.py \
  --adapter_model_name /runs/ixc_lora \
  --base_model_name /models/internlm-xcomposer2d5-7b \
  --output_name /runs/ixc_lora_merged
```

This loads both base and adapter checkpoints and writes a merged model directory. Keep outputs outside the runtime skill tree.

## Launcher families

### Source-equivalent DeepSpeed path

The official 2.5 shell templates use `torchrun` for process launch and `--deepspeed ds_config_zero2.json` for ZeRO-2 optimizer/state handling:

```bash
torchrun \
  --nproc_per_node 8 \
  --nnodes 1 \
  --node_rank 0 \
  --master_addr localhost \
  --master_port 6001 \
  finetune.py \
  --model_name_or_path <model> \
  --data_path data.txt \
  --given_num True \
  --deepspeed ds_config_zero2.json
```

Use this path when you want to stay closest to the repository scripts.

### Manual FSDP path

The project README advertises DeepSpeed and FSDP support, but the visible shell templates are DeepSpeed templates. To use FSDP, keep the same `torchrun` process launcher and replace `--deepspeed ...` with Hugging Face Trainer FSDP flags:

```bash
torchrun \
  --nproc_per_node <gpus> \
  --nnodes <nodes> \
  --node_rank <rank> \
  --master_addr <addr> \
  --master_port <port> \
  finetune.py \
  --model_name_or_path <model> \
  --data_path data.txt \
  --given_num True \
  --fsdp "full_shard auto_wrap"
```

Treat the FSDP string as an editable Trainer argument. Add any model-specific wrap-class options only after confirming them in the target runtime.

### Single-GPU or tiny-fixture dry planning

For command review against a tiny fixture, render a one-process command and edit it before running:

```bash
python scripts/render_finetune_command.py \
  --mode lora \
  --backend deepspeed \
  --model /models/internlm-xcomposer2d5-7b \
  --data data.txt \
  --output-dir output/tiny_lora \
  --gpus 1 \
  --batch-size 1 \
  --gradient-accumulation-steps 1 \
  --max-length 512
```

The helper only prints a command; it never imports torch, starts training, or touches model files.

## Full-parameter workflow

Use full-parameter mode when you intend to update the language model and vision projection parameters, and you have enough GPU memory for the selected `hd_num` and `max_length`.

Key source-template settings:

- `--use_lora False`
- `--fix_vit False`
- `--fix_sampler False`
- `--bf16 True`
- `--hd_num 18`
- `--max_length 16384` in the shell template
- `--learning_rate 1e-5`
- `--per_device_train_batch_size 1`
- `--gradient_accumulation_steps 8`
- `--deepspeed ds_config_zero2.json` for the source-equivalent launcher

`fix_vit False` unfreezes the ViT side and replaces the vision tower post-layernorm with an identity module in the 2.5 training code. If memory is tight, prefer LoRA or reduce `hd_num` / `max_length` before unfreezing more components.

## LoRA workflow

Use LoRA mode for adapter-only tuning. The source LoRA shell template freezes the visual components and the language model base weights, then applies PEFT LoRA modules to selected transformer layers.

Key source-template settings:

- `--use_lora True`
- `--fix_vit True`
- `--fix_sampler True`
- `--learning_rate 5e-5`
- `--output_dir output/finetune_lora`
- same `torchrun`, `--given_num True`, DeepSpeed, `hd_num`, and gradient-checkpointing pattern as full mode

Default LoRA arguments from the trainer:

```text
lora_r = 64
lora_alpha = 64
lora_dropout = 0.05
lora_target_modules = attention.wqkv, attention.wo, feed_forward.w1, feed_forward.w2, feed_forward.w3
lora_bias = none
```

The parser also exposes `lora_weight_path`, but the current training path does not load it. Do not rely on that flag to resume or initialize LoRA weights unless you have patched the trainer.

## Loading or merging a LoRA adapter

After LoRA training, the adapter output can be loaded directly with PEFT:

```python
from peft import AutoPeftModelForCausalLM

model = AutoPeftModelForCausalLM.from_pretrained(
    path_to_adapter,
    device_map="auto",
    trust_remote_code=True,
).eval()
```

To produce a merged model directory, use the repository's `merge_peft_adapter.py` behavior:

```bash
python merge_peft_adapter.py \
  --adapter_model_name <adapter-output-dir> \
  --base_model_name <base-model-dir-or-id> \
  --output_name <merged-output-dir>
```

The merge script loads the base model with `trust_remote_code=True` and `torch_dtype=torch.bfloat16`, loads the PEFT adapter, calls `merge_and_unload()`, then saves the merged model and tokenizer. Use absolute paths for the base model and adapter when the adapter config may be moved across machines.

## Data-mixing workflow implications

The data mixer affects what a training epoch means:

- `data.txt` sampling first up/down-samples each JSON list according to `--given_num` or ratio mode.
- `Mix_dataset` then splits the loaded files into text and image pools by looking only at the first sample in each file.
- Selection across files is weighted by loaded file length inside each pool.
- `Sample_dataset.get_item()` randomly draws `batch_size` examples from the selected file, so repeated up-sampled examples can appear more often in an epoch.
- The internal `use_multi` counter makes image-bearing batches appear preferentially until the counter exceeds `batch_size * 2`, then resets.
- Keep `per_device_train_batch_size=1` unless the model forward path and data collator have been audited for larger Trainer batches.

For tiny usability checks, use a direct JSON file or a manifest with one text file and one image file. Keep the actual image paths optional during command rendering, but validate them with `--check-paths` before a real training run.
