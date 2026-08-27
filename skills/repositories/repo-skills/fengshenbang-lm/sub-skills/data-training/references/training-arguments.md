# Training arguments and parser groups

This reference separates the flags that belong to model/optimizer logic, data loading, checkpointing, and trainer runtime. When you are turning a shell script into a safer command plan, classify flags before editing them.

## Compose parsers in this order

Most repo entry points follow some variation of:

1. data arguments
2. Lightning trainer arguments
3. checkpoint arguments
4. module / optimizer / scheduler arguments
5. task-specific model arguments

The order matters only when flags collide. Add all providers before `parse_args()` and avoid duplicate option strings.

## Core providers

| Provider | Typical group title | Key flags | Notes |
|---|---|---|---|
| `fengshen.models.model_utils.add_module_args` | `Basic Module` | `learning_rate`, `min_learning_rate`, `lr_decay_steps`, `lr_decay_ratio`, `warmup_steps`, `warmup_ratio`, `weight_decay`, `adam_beta1`, `adam_beta2`, `adam_epsilon`, `model_path`, `scheduler_type` | Shared optimizer/scheduler flags used by many examples. |
| `fengshen.models.model_utils.add_inverse_square_args` | `Basic Module` | `warmup_min_lr`, `warmup_max_lr` | Only needed when `scheduler_type=inverse_sqrt`. |
| `fengshen.data.universal_datamodule.UniversalDataModule.add_data_specific_args` | `Universal DataModule` | `num_workers`, `dataloader_workers`, `train_batchsize`, `val_batchsize`, `test_batchsize`, `datasets_name`, `train_datasets_field`, `val_datasets_field`, `test_datasets_field`, `train_file`, `val_file`, `test_file`, `raw_file_type`, `sampler_type`, `use_mpu` | Supports HF datasets, local JSON/JSONL, and custom pretraining samplers. |
| `fengshen.data.mmap_dataloader.mmap_datamodule.MMapDataModule.add_data_specific_args` | `MMAP DataModule` | `train_datas`, `valid_datas`, `test_datas`, `input_tensor_name`, `train_batchsize`, `eval_batchsize`, `test_batchsize` | For memory-mapped tensor files, not JSON. |
| `fengshen.data.bert_dataloader.load.BertDataModule.add_data_specific_args` | `Universal DataModule` | `datasets_name`, `train_datasets_field`, `val_datasets_field`, `test_datasets_field`, `train_batchsize`, `val_batchsize`, `test_batchsize` | Uses cached HF datasets created by the BERT preprocessing pipeline. |
| `fengshen.data.task_dataloader.task_datasets.LCSTSDataModel.add_data_specific_args` | `LCSTSDataModel` | `data_dir`, `train_data`, `valid_data`, `test_data`, `train_batchsize`, `valid_batchsize`, `max_enc_length`, `max_dec_length`, `prompt` | Summary fine-tuning and evaluation. |
| `fengshen.data.task_dataloader.medicalQADataset.GPT2QADataModel.add_data_specific_args` | `GPT2QADataModel` | `data_dir`, `train_data`, `valid_data`, `test_data`, `train_batchsize`, `valid_batchsize`, `max_seq_length` | Legacy trusted-dict line reader for causal QA. |
| `fengshen.data.t5_dataloader.t5_datasets.UnsuperviseT5DataModel.add_data_specific_args` | `UnsuperviseT5DataModel` | `dataset_num_workers`, `dataloader_num_workers`, `train_data_path`, `train_batchsize`, `valid_batchsize`, `train_split_size`, `tokenizer_type`, `text_column_name`, `remove_columns` | Unsupervised T5 span-corruption pretraining. |
| `fengshen.data.t5_dataloader.t5_datasets.TaskT5DataModel.add_data_specific_args` | `TaskT5DataModel` | `dataset_num_workers`, `dataloader_num_workers`, `train_data_path`, `valid_data_path`, `train_batchsize`, `valid_batchsize`, `train_split_size`, `tokenizer_type`, `text_column_name`, `remove_columns` | Supervised T5 task data and choice-based generation. |
| `fengshen.data.t5_dataloader.t5_gen_datasets.DialogDataModel.add_data_specific_args` | `SuperviseT5DataModel` | `dataset_num_workers`, `dataloader_num_workers`, `train_data_path`, `valid_data_path`, `train_batchsize`, `valid_batchsize`, `max_seq_length`, `max_knowledge_length`, `max_target_length` | Dialog / knowledge-grounded generation. |
| `fengshen.utils.universal_checkpoint.UniversalCheckpoint.add_argparse_args` | `universal checkpoint callback` | `monitor`, `mode`, `save_ckpt_path`, `load_ckpt_path`, `filename`, `save_last`, `save_top_k`, `every_n_train_steps`, `save_weights_only`, `every_n_epochs`, `save_on_train_epoch_end` | Checkpoint policy and resume path handling. |
| `pytorch_lightning.Trainer.add_argparse_args` | Lightning trainer groups | `max_epochs`, `gpus`, `num_nodes`, `strategy`, `precision`, `accumulate_grad_batches`, `gradient_clip_val`, `default_root_dir`, `replace_sampler_ddp`, `val_check_interval`, `check_val_every_n_epoch`, `log_every_n_steps`, `resume_from_checkpoint` | Old-style parser used throughout this repo. |

## Task-specific model args that often travel with the trainer

| Workflow | Flags you usually keep together | Why |
|---|---|---|
| Sequence tagging | `max_seq_length`, `model_type`, `decode_type`, `loss_type`, `data_dir` | Selects collator, label inventory, and evaluation path. |
| BERT-style pretraining | `masked_lm_prob`, `max_seq_length`, `sample_content_key`, `learning_rate`, `weight_decay`, `warmup` | Drives the masking collator and optimizer schedule. |
| Randeng / BART denoising | `masked_lm_prob`, `max_seq_length`, `sample_content_key`, `permute_sentence_ratio` | Controls text infilling and sentence shuffling. |
| T5 pretraining | `pretrained_model_path`, `new_vocab_path`, `keep_tokens_path`, `max_seq_length`, `train_split_size`, `tokenizer_type` | Shapes tokenizer resizing and span-corruption inputs. |
| QA / summary generation | `max_enc_length`, `max_dec_length`, `prompt`, `formator`, `prediction_res_path`, `decode_strategy` | Controls source/target formatting and evaluation output. |

## How to classify shell flags

When you see a shell script, sort its flags into these buckets:

### Data preparation

- dataset roots: `data_dir`, `train_data_path`, `valid_data_path`, `test_data_path`, `datasets_name`
- file names: `train_file`, `val_file`, `test_file`, `train_data`, `valid_data`, `test_data`
- preprocessing shape: `max_seq_length`, `max_enc_length`, `max_dec_length`, `train_split_size`, `remove_columns`
- worker counts: `num_workers`, `dataloader_workers`, `dataset_num_workers`, `preprocessing_num_workers`

### Runtime and distribution

- `gpus`, `num_nodes`, `strategy`, `precision`, `accumulate_grad_batches`, `gradient_clip_val`
- `default_root_dir`, `val_check_interval`, `check_val_every_n_epoch`, `log_every_n_steps`
- `replace_sampler_ddp=False` when a custom sampler is required

### Optimizer and scheduler

- `learning_rate`, `weight_decay`, `adam_beta1`, `adam_beta2`, `adam_epsilon`
- `warmup_steps`, `warmup_ratio`, `lr_decay_steps`, `lr_decay_ratio`
- `scheduler_type`, `min_learning_rate`, `warmup_min_lr`, `warmup_max_lr`

### Checkpointing and resume

- `monitor`, `mode`, `save_top_k`, `save_last`, `every_n_train_steps`
- `save_ckpt_path`, `load_ckpt_path`, `filename`, `resume_from_checkpoint`

### Task-specific model / collator

- `decode_type`, `loss_type`, `model_type`, `tokenizer_type`, `prompt`, `formator`, `sample_content_key`

### DeepSpeed runtime plumbing

- `--strategy deepspeed_stage_1|2|3`
- `--deepspeed <config.json>` in older scripts
- `PL_DEEPSPEED_CONFIG_PATH` in the environment

## Practical edits

- If a script says `--max_epoch`, convert it to `--max_epochs` for Lightning.
- If a script says `--sheduler_type`, correct it to `--scheduler_type`.
- If a script uses a custom sampler, keep `replace_sampler_ddp=False` and make sure the data module still owns the batch sampler.
- If a script resumes training, keep the checkpoint path and the data-loader resume state together; do not edit only one side.

## Inspector script

Run [../scripts/inspect_training_args.py](../scripts/inspect_training_args.py) to print the concrete destinations currently available in your environment.
