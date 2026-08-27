# Configuration

LlamaFactory v0 training arguments are assembled from model, data, training, finetuning, and generation dataclasses. For `train`, the parser combines `ModelArguments`, `DataArguments`, `TrainingArguments`, `FinetuningArguments`, and `GeneratingArguments`.

## YAML/JSON vs CLI Flags

`read_args()` implements three modes:

- `llamafactory-cli train config.yaml key=value nested.key=value`: loads YAML with OmegaConf and merges CLI overrides.
- `llamafactory-cli train config.json key=value`: loads JSON, converts to OmegaConf, and merges CLI overrides.
- `llamafactory-cli train --key value --flag`: parses normal command-line flags through Hugging Face `HfArgumentParser`.

Implications:

- For config files, overrides use `key=value` syntax, not `--key value`.
- For pure CLI runs, use `--key value` or boolean flags such as `--do_train`.
- Unknown pure CLI flags print help and raise an error unless an internal caller explicitly allows extra keys.
- YAML comments and grouping headers are documentation only; the parser consumes flattened keys.

## Command Rendering Without Training

Use the bundled helper to inspect and render safe commands:

```bash
python scripts/render_train_command.py config.yaml output_dir=saves/debug max_steps=1
```

The helper reads YAML/JSON, applies simple `key=value` overrides, warns about likely issues, and prints a shell command. It does not import LlamaFactory, validate all dataclasses, download models, or run training.

## Common Key Groups

### Model Keys

- `model_name_or_path`: required by `ModelArguments`; can be a local path or hub model id.
- `adapter_name_or_path`: comma-separated adapter paths; valid for LoRA/OFT-style adapter loading, not full/freeze training.
- `trust_remote_code`: required by some model families but executes model repo code when loading.
- `cache_dir`: download/cache location.
- `quantization_bit`: enables quantized loading/training for compatible PEFT flows.
- `quantization_method`: selects backend-specific quantization behavior when available.
- `resize_vocab`, `add_tokens`, `add_special_tokens`, `new_special_tokens_config`: tokenizer/vocabulary changes; do not combine `resize_vocab` with quantized training.
- `flash_attn`, `use_unsloth`, `enable_liger_kernel`, `mixture_of_depths`, `use_kt`: optional acceleration/features that require extra packages or compatible hardware.

### Data Keys

- `dataset`: comma-separated training dataset names.
- `eval_dataset`: comma-separated eval dataset names; do not combine with `val_size`.
- `dataset_dir`: dataset registry/source directory; values like `REMOTE:...` and `ONLINE` depend on LlamaFactory data loading.
- `template`: prompt template name; route template/data-format questions to `data-and-templates`.
- `cutoff_len`: tokenized max length; packing may reduce effective value by one internally.
- `max_samples`: debugging truncation; incompatible with `streaming`.
- `val_size`: split size; cannot be used if `dataset` is missing or `eval_dataset` is set.
- `streaming`: streaming dataset mode; fractional `val_size` is rejected.
- `mix_strategy` and `interleave_probs`: interleaved dataset mixing; `interleave_probs` is invalid with `mix_strategy: concat` and must match dataset count.
- `train_on_prompt` and `mask_history`: mutually incompatible.
- `tokenized_path`: save/load pre-tokenized datasets.

### Finetuning Keys

- `stage`: `pt`, `sft`, `rm`, `ppo`, `dpo`, or `kto`.
- `finetuning_type`: `lora`, `oft`, `freeze`, or `full`.
- LoRA: `lora_rank`, `lora_alpha`, `lora_dropout`, `lora_target`, `additional_target`, `loraplus_lr_ratio`, `use_rslora`, `use_dora`, `pissa_init`, `pissa_convert`.
- OFT: `oft_rank`, `oft_block_size`, `oft_target`, `module_dropout`.
- Freeze: `freeze_trainable_layers`, `freeze_trainable_modules`, `freeze_extra_modules`.
- Preference/RLHF: `pref_beta`, `pref_loss`, `pref_ftx`, `dpo_label_smoothing`, `simpo_gamma`, `ref_model`, `reward_model`, `reward_model_type`, `ppo_*`, `kto_*`.
- Optimizer add-ons: `use_galore`, `use_apollo`, `use_badam`, `use_adam_mini`, `use_muon`; do not combine LoRA with GaLore/APOLLO/BAdam.
- Logging/metrics: `compute_accuracy`, `plot_loss`, `include_effective_tokens_per_second`, SwanLab keys.

### Training Keys

LlamaFactory extends Hugging Face `Seq2SeqTrainingArguments`, so standard Trainer keys apply:

- Output/checkpoint: `output_dir`, `overwrite_output_dir`, `save_steps`, `save_strategy`, `save_total_limit`, `save_only_model`, `resume_from_checkpoint`.
- Batches: `per_device_train_batch_size`, `per_device_eval_batch_size`, `gradient_accumulation_steps`, `dataloader_num_workers`.
- Schedule: `learning_rate`, `num_train_epochs`, `max_steps`, `lr_scheduler_type`, `warmup_ratio`, `warmup_steps`.
- Precision: `bf16`, `fp16`, `pure_bf16`, `fp8`, `fp8_backend`.
- Evaluation: `eval_strategy`, `eval_steps`, `metric_for_best_model`, `load_best_model_at_end`.
- Distributed: `ddp_timeout`, `deepspeed`, `fsdp`, FSDP transformer wrap keys, Ray keys.
- Logging: `logging_steps`, `report_to`, `run_name`, `project`, profiler keys.

## Override Examples

YAML/JSON file overrides:

```bash
llamafactory-cli train train.yaml output_dir=saves/debug max_steps=1 report_to=none
llamafactory-cli train train.yaml learning_rate=5.0e-5 dataset=identity,alpaca_en_demo
llamafactory-cli train train.json stage=dpo pref_loss=simpo simpo_gamma=0.5
```

Pure CLI equivalent:

```bash
llamafactory-cli train \
  --model_name_or_path Qwen/Qwen3-4B-Instruct-2507 \
  --trust_remote_code \
  --stage sft \
  --do_train \
  --finetuning_type lora \
  --dataset identity,alpaca_en_demo \
  --template qwen3_nothink \
  --output_dir saves/debug \
  --max_steps 1 \
  --report_to none
```

## Validation Checklist Before Training

- Confirm `model_name_or_path`, `dataset`, `template`, and `output_dir` are intentional.
- Confirm `stage` matches dataset type: pretrain text for `pt`, supervised conversations for `sft`, preference pairs for `dpo`/`rm`, KTO labels for `kto`, reward model for `ppo`.
- Confirm `finetuning_type` matches memory and quantization needs.
- Set `report_to: none` unless the user configured tracker credentials.
- Use `max_steps: 1` or small `max_samples` for smoke testing.
- Use `overwrite_output_dir: true` only when replacing an existing output is intended.
- Keep hub tokens, tracker API keys, and private paths outside reusable public examples.

## Boundary Notes

- Dataset schema and prompt template fixes belong to `data-and-templates` even when a train config references them.
- Export-time options such as `export_dir` and adapter merging belong to `model-loading-and-export`.
- v1 YAML examples often use nested `training`, `model`, or distributed backend structures; route those to `v1-experimental`.
