# Training CLI Reference

## Model Arguments

Common training-related fields:

- `model_name_or_path`
- `lora_model_path`
- `arch_type`
- `trust_remote_code`
- `torch_dtype`
- `use_lora`
- `use_qlora`
- `quant_bit`
- `use_dora`
- `use_ram_optimized_load`

## Dataset Arguments

Fields that often matter for training:

- `dataset_path`
- `conversation_template`
- `disable_group_texts`
- `block_size`
- `validation_split_percentage`
- `preprocessing_num_workers`
- `dataset_cache_dir`
- `overwrite_cache`

## Finetuner Arguments

Important fields from `FinetunerArguments`:

- `output_dir`
- `overwrite_output_dir`
- `num_train_epochs`
- `learning_rate`
- `per_device_train_batch_size`
- `gradient_accumulation_steps`
- `lr_scheduler_type`
- `bf16`
- `seed`
- `logging_steps`
- `save_steps`
- `report_to`
- `do_train`
- `use_lisa`
- `lisa_activated_layers`
- `lisa_interval_steps`
- `use_customized_optim`
- `customized_optim`

## Practical Notes

- `conversation_template` should be aligned with the dataset content.
- `report_to` should be set to `none` when W&B is intentionally disabled.
- `num_train_epochs`, `save_steps`, and batch size should be chosen together with available memory.
- `overwrite_output_dir` is a deliberate choice, not a default.
