# Fine-tuning API reference

This page records the distilled interface and runtime behavior of the repository-compatible fine-tuning function.

## `train()` signature

```python
def train(
    base_model: str = "",
    data_path: str = "yahma/alpaca-cleaned",
    output_dir: str = "./lora-alpaca",
    batch_size: int = 128,
    micro_batch_size: int = 8,
    num_epochs: int = 10,
    learning_rate: float = 3e-4,
    cutoff_len: int = 256,
    val_set_size: int = 500,
    lora_r: int = 8,
    lora_alpha: int = 16,
    lora_dropout: float = 0.05,
    lora_target_modules: list[str] = ["q_proj", "v_proj"],
    train_on_inputs: bool = False,
    group_by_length: bool = False,
    wandb_project: str = "llama_med",
    wandb_run_name: str = "",
    wandb_watch: str = "",
    wandb_log_model: str = "",
    resume_from_checkpoint: str | None = None,
    prompt_template_name: str = "alpaca",
): ...
```

The command-line interface is exposed through Python Fire, so command arguments use the same parameter names, for example `--base_model`, `--data_path`, and `--prompt_template_name`.

## Required and high-impact parameters

| Parameter | Required? | Effect |
|---|---:|---|
| `base_model` | Yes | Hugging Face model id or local base-model path. The function asserts this is non-empty before loading. |
| `data_path` | Usually | Local `.json`/`.jsonl` path or a dataset name accepted by Datasets. Local medical fine-tuning should use JSONL records with `instruction`, `input`, `output`. |
| `output_dir` | Recommended | Adapter checkpoints and final LoRA adapter are written here. |
| `prompt_template_name` | Recommended | Selects the prompt renderer. Use `med_template` for the medical-knowledge LLaMA/Alpaca recipe unless another compatible template is deliberate. |
| `batch_size` | Yes for planning | Global/effective batch target; used to compute gradient accumulation. |
| `micro_batch_size` | Yes for memory | Per-device batch; lower this to reduce GPU memory. |
| `cutoff_len` | Yes for memory/quality | Maximum prompt length; lower for memory, raise only when context needs it. |
| `resume_from_checkpoint` | Optional | Loads compatible full checkpoint or PEFT adapter state. |

## Internal data path behavior

- Paths ending in `.json` or `.jsonl` use `load_dataset("json", data_files=data_path)`.
- Other `data_path` values are passed to `load_dataset(data_path)` as dataset identifiers.
- When `val_set_size > 0`, the train split is divided with `train_test_split(test_size=val_set_size, shuffle=True, seed=2023)`.
- When `val_set_size == 0`, no eval dataset is created and evaluation strategy is disabled.
- Each mapped sample must support `data_point["instruction"]`, `data_point["input"]`, and `data_point["output"]`.

## Prompt/tokenization behavior

For each record:

1. The full prompt is built from instruction, input, and output.
2. The tokenizer truncates to `cutoff_len`, does not pad during preprocessing, and appends EOS when there is room and the prompt does not already end with EOS.
3. `labels` start as a copy of `input_ids`.
4. If `train_on_inputs=False`, the user prompt portion is replaced with `-100` labels so the loss is applied only to the answer portion.

The tokenizer then uses `pad_token_id = 0` and `padding_side = "left"`; the Trainer data collator pads batches to a multiple of 8.

## Model and PEFT setup

The training logic loads:

```python
AutoModelForCausalLM.from_pretrained(
    base_model,
    load_in_8bit=True,
    torch_dtype=torch.float16,
    device_map=device_map,
)
AutoTokenizer.from_pretrained(base_model)
```

Then it calls the PEFT int8-preparation helper, configures LoRA as:

```python
LoraConfig(
    r=lora_r,
    lora_alpha=lora_alpha,
    target_modules=lora_target_modules,
    lora_dropout=lora_dropout,
    bias="none",
    task_type="CAUSAL_LM",
)
```

This target-module default is appropriate for LLaMA/Alpaca-style attention projections. For other model families, confirm the module names before launching training.

## Trainer settings

Key `TrainingArguments` values:

| Setting | Value |
|---|---|
| `per_device_train_batch_size` | `micro_batch_size` |
| `gradient_accumulation_steps` | `batch_size // micro_batch_size`, divided by `WORLD_SIZE` under DDP |
| `warmup_ratio` | `0.1` |
| `num_train_epochs` | `num_epochs` |
| `learning_rate` | `learning_rate` |
| `fp16` | `True` |
| `logging_steps` | `8` |
| `optim` | `adamw_torch` |
| `evaluation_strategy` | `steps` when validation is enabled, else `no` |
| `eval_steps` | `32` when validation is enabled |
| `save_strategy` | `steps` |
| `save_steps` | `32` |
| `save_total_limit` | `5` |
| `load_best_model_at_end` | `True` when validation is enabled |
| `group_by_length` | passed from argument |
| `report_to` | `wandb` when W&B is enabled, else `None` |
| `run_name` | `wandb_run_name` when W&B is enabled |

If multiple CUDA devices are visible but DDP is not active, the model is marked `is_parallelizable=True` and `model_parallel=True` to prevent Trainer from attempting DataParallel.

## Checkpoint format

The save callback writes PEFT adapter checkpoints into `checkpoint-<step>` directories and removes full-model `pytorch_model.bin` files from those checkpoint directories when present. A final adapter save is written to `output_dir` after `trainer.train()`.

Expected adapter-oriented files after a successful PEFT save usually include:

- `adapter_config.json`
- `adapter_model.bin` or equivalent adapter weight file, depending on PEFT version

Use `checkpoint-export` when the task is to merge or export adapter weights.

## Bundled command builder interface

The bundled builder accepts safe, hyphenated arguments and prints a compatible Python Fire command. Important options:

```text
--base-model BASE_MODEL_OR_PATH        required
--data-path DATA_PATH                  default placeholder
--output-dir OUTPUT_DIR                default ./lora-llama-med
--batch-size N                         default 128
--micro-batch-size N                   default 8
--epochs N                             maps to num_epochs
--lr FLOAT                             maps to learning_rate
--cutoff-len N                         default 256
--val-size N                           maps to val_set_size
--lora-r N --lora-alpha N --lora-dropout FLOAT
--lora-target-modules q_proj v_proj
--prompt-template-name med_template
--wandb-run-name NAME
--disable-wandb
--resume-from-checkpoint PATH
--validate-data
```

The builder is intentionally dry-run only. It may validate local JSONL shape with the Python standard library, but it never imports model-training dependencies.
