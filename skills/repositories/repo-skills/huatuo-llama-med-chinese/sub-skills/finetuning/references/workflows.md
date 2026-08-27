# LoRA fine-tuning workflows

This reference distills the repository-compatible LoRA instruction fine-tuning workflow for Chinese medical QA data. It is operational guidance, not a request to run training immediately.

## What the training workflow does

The training entrypoint exposes a `train()` function through Python Fire. It:

1. Prints the resolved training, LoRA, W&B, resume, and prompt-template parameters on rank 0.
2. Requires a non-empty `base_model` value.
3. Computes `gradient_accumulation_steps = batch_size // micro_batch_size`; under DDP it divides that value again by `WORLD_SIZE`.
4. Builds prompts from each record's `instruction`, `input`, and `output` using the selected prompt template.
5. Loads the base causal LM in fp16 with `load_in_8bit=True` and `device_map="auto"` unless DDP maps the model to `LOCAL_RANK`.
6. Prepares the model for int8 training, attaches LoRA adapters, tokenizes the dataset, and trains with the Transformers `Trainer`.
7. Saves PEFT adapter checkpoints during training and a final adapter in `output_dir`.

Actual training requires compatible model weights, CUDA-capable hardware in practice for the 7B/int8 workflow, and the legacy ML dependency stack.

## Canonical command-building flow

Use the bundled dry-run builder first:

```bash
python sub-skills/finetuning/scripts/build_finetune_command.py \
  --base-model BASE_MODEL_OR_LOCAL_PATH \
  --data-path data/medical_qa.jsonl \
  --output-dir outputs/lora-med-run \
  --prompt-template-name med_template \
  --batch-size 32 \
  --micro-batch-size 2 \
  --epochs 10 \
  --validate-data \
  --disable-wandb
```

The builder prints a command shaped for the compatible training interface and exits without importing `torch`, loading models, downloading assets, or starting training.

## Defaults and repository shell example

The training function defaults are:

| Parameter | Default | Notes |
|---|---:|---|
| `base_model` | `""` | Asserted as required before model loading. |
| `data_path` | `yahma/alpaca-cleaned` | Local `.json` or `.jsonl` paths use the Datasets JSON loader. |
| `output_dir` | `./lora-alpaca` | Final adapter is saved here. |
| `batch_size` | `128` | Global/effective batch target before DDP division. |
| `micro_batch_size` | `8` | Per-device train batch size. Lower this first for memory pressure. |
| `num_epochs` | `10` | README resource notes also used 10 epochs. |
| `learning_rate` | `3e-4` | Passed to `TrainingArguments`. |
| `cutoff_len` | `256` | Max tokenized prompt length. |
| `val_set_size` | `500` | If positive, uses a train/test split and step evaluation. |
| `lora_r` | `8` | LoRA rank. |
| `lora_alpha` | `16` | LoRA scaling alpha. |
| `lora_dropout` | `0.05` | LoRA dropout. |
| `lora_target_modules` | `q_proj`, `v_proj` | LLaMA/Alpaca-style attention projection names. |
| `train_on_inputs` | `False` | Masks user prompt tokens from the loss. |
| `group_by_length` | `False` | Can be faster but changes loss-curve shape. |
| `wandb_project` | `llama_med` | Enables W&B unless explicitly disabled or emptied. |
| `wandb_run_name` | `""` | Optional run display name. |
| `wandb_watch` | `""` | Optional W&B watch setting. |
| `wandb_log_model` | `""` | Optional W&B model logging setting. |
| `resume_from_checkpoint` | `None` | May point to a Trainer checkpoint or adapter directory. |
| `prompt_template_name` | `alpaca` | The repository shell example overrides this to `med_template`. |

The maintained shell recipe used an experiment tag, local medical training data, `med_template`, `batch_size=128`, `micro_batch_size=128`, and a W&B run name. Treat that as an A100-class example, not a universal setting. The README reports LLaMA fine-tuning on one A100-SXM-80GB for 10 epochs in about 2h17m, with `batch_size=128` using about 40GB GPU memory; 24GB GPUs such as 3090/4090-class devices require batch-size adjustment.

## Dataset validation expectations

Training data should be JSONL: one JSON object per line. Each object should contain:

```json
{"instruction": "中文医学问题或指令", "input": "", "output": "目标回答"}
```

Rules for this implementation:

- `instruction` is required and should be a string.
- `input` is required for compatibility even when empty; use `""` for no extra context.
- `output` is required and should be the target answer string.
- The loader accepts files ending in `.json` or `.jsonl`; the provided training data is newline-delimited JSON despite using a `.json` suffix.
- Prompt-template schema and data conversion details are owned by `prompt-data-formats`.

## W&B behavior

The source logic enables W&B when `wandb_project` is non-empty or when `WANDB_PROJECT` is set in the environment. Because the default project is `llama_med`, W&B is enabled by default when the `wandb` package is present.

To keep a dry or private run from contacting W&B:

- Use the bundled builder's `--disable-wandb`, which emits an empty `wandb_project` and disables W&B-related environment variables in the printed command.
- Also clear any inherited `WANDB_PROJECT` in the execution environment before an actual run.
- Provide `--wandb-run-name` only when W&B logging is intentionally enabled.

## DDP behavior

DDP is detected from `WORLD_SIZE`:

- `WORLD_SIZE == 1` means non-DDP; the model uses `device_map="auto"`.
- `WORLD_SIZE != 1` maps the model to `LOCAL_RANK` and sets `ddp_find_unused_parameters=False`.
- Gradient accumulation is computed as `(batch_size // micro_batch_size) // WORLD_SIZE`.

Before launching DDP, ensure the final accumulation value is at least 1. If `batch_size` is too small relative to `micro_batch_size * WORLD_SIZE`, increase `batch_size`, reduce `micro_batch_size`, or reduce process count.

## Checkpoint save and resume expectations

During Trainer saves, a PEFT save callback writes adapter files into `output_dir/checkpoint-<global_step>/` and removes a full `pytorch_model.bin` if one appears there. This keeps checkpoint directories adapter-focused. At the end, the model saves a final adapter into `output_dir`.

Resume behavior:

- If `resume_from_checkpoint` contains `pytorch_model.bin`, it is treated as a full checkpoint and Trainer resume remains active.
- If it contains `adapter_model.bin`, adapter weights are loaded into the PEFT model and Trainer resume is disabled so only the adapter state is reused.
- If neither file exists, the run prints a checkpoint-not-found message and starts without loading adapter state.
- The LoRA configuration (`r`, `alpha`, target modules, base model family) must match the checkpointed adapter.

## 24GB GPU adaptation pattern

For a 24GB GPU, start conservatively:

```bash
python sub-skills/finetuning/scripts/build_finetune_command.py \
  --base-model BASE_MODEL_OR_LOCAL_PATH \
  --data-path data/medical_qa.jsonl \
  --output-dir outputs/lora-med-24gb \
  --batch-size 16 \
  --micro-batch-size 1 \
  --cutoff-len 256 \
  --epochs 10 \
  --prompt-template-name med_template \
  --validate-data \
  --disable-wandb
```

If memory is still insufficient, try `--cutoff-len 128`, keep `micro_batch_size=1`, and increase global `batch_size` only when gradient accumulation remains stable. Avoid copying the shell example's `micro_batch_size=128` onto 24GB hardware.
