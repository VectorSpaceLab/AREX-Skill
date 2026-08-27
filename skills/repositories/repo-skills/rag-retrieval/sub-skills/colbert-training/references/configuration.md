# ColBERT Training Configuration

## Core `train_colbert.py` Arguments

The source training entry point accepts these important arguments:

| Argument | Purpose | Typical value |
| --- | --- | --- |
| `--model_name_or_path` | Hugging Face model id or local saved checkpoint directory | `hfl/chinese-roberta-wwm-ext` or `BAAI/bge-m3` |
| `--dataset` | Triplet JSONL path | `train.jsonl` |
| `--output_dir` | Directory for logs, checkpoints, and final `model/` save | `output/my_colbert_run` |
| `--batch_size` | Query-positive pairs per process batch | `2`-`8`, hardware dependent |
| `--lr` | AdamW learning rate | around `5e-6` for `BAAI/bge-m3` fine-tuning |
| `--epochs` | Number of passes over expanded positives | `1`-`3` for initial runs |
| `--gradient_accumulation_steps` | Accumulation steps passed to `Accelerator` | raise when GPU memory is tight |
| `--temperature` | Contrastive softmax temperature | `0.02` |
| `--query_max_len` | Query tokenizer max length | `128` |
| `--passage_max_len` | Positive/negative passage max length | `512` |
| `--neg_nums` | Hard negatives sampled per query-positive pair | `15` if the data has enough negatives |
| `--colbert_dim` | Output dimension of the ColBERT projection head | `768` for many BERT-like starts, `1024` for `BAAI/bge-m3` ColBERT |
| `--save_on_epoch_end` | Save epoch checkpoints under the run directory | `1` to keep checkpoints |
| `--num_max_checkpoints` | Retention limit for epoch checkpoints | `5` |
| `--log_with` | Accelerate tracker | `wandb`, `tensorboard`, or a tracker available in the environment |
| `--mixed_precision` | Accelerate mixed precision setting | source default is `fp16`; align with hardware/config |
| `--warmup_proportion` | Fraction of total steps used for cosine warmup | `0.05`-`0.1` |
| `--seed` | Random seed | `666` default |

The training script always saves the final model under `output_dir/model`, including the base transformer files and `colbert_linear.pt`.

## `colbert_dim` Selection

`colbert_dim` controls the linear projection from the backbone hidden size into late-interaction token vectors. It must match how the saved ColBERT checkpoint is loaded later.

- For `BAAI/bge-m3` ColBERT-style fine-tuning, use `--colbert_dim 1024` unless you deliberately trained a new projection size from scratch.
- For BERT-like starts such as `hfl/chinese-roberta-wwm-ext`, the README example uses `--colbert_dim 768`.
- Loading a saved checkpoint with the wrong `colbert_dim` can fail when `colbert_linear.pt` shape does not match the new projection layer.

Run the validator to catch the common `BAAI/bge-m3` plus `--colbert_dim 768` mistake before launch:

```bash
python sub-skills/colbert-training/scripts/validate_colbert_training_args.py \
  --data train.jsonl --model-name-or-path BAAI/bge-m3 --colbert-dim 768
```

## Model and FSDP Config Selection

The skill bundles two accelerate FSDP config snapshots:

- BERT-like backbones: wrap `BertLayer` and use this for starts such as `hfl/chinese-roberta-wwm-ext`.
- XLM-RoBERTa-like backbones: wrap `XLMRobertaLayer` and use this for `BAAI/bge-m3` because it is built on a multilingual XLM-RoBERTa family backbone.

Make `num_processes` match the number of GPUs exposed through `CUDA_VISIBLE_DEVICES`. If the launch exposes two GPUs, the accelerate config should use `num_processes: 2`. If a user switches to one GPU, update both the visible devices and the accelerate config.

## Batch, Accumulation, and Memory

The model scores each query against its positive passage and against all negatives from the batch. Larger `batch_size` and larger `neg_nums` both increase compute and memory.

- Reduce `batch_size` first when CUDA memory fails.
- Increase `gradient_accumulation_steps` to preserve an effective batch size after reducing per-device batch size.
- Lower `passage_max_len` if passages are long and memory pressure persists.
- Lower `neg_nums` only if the training objective still has enough hard-negative diversity.

Effective query-positive batch size is approximately:

```text
effective_batch = batch_size * num_processes * gradient_accumulation_steps
```

## Logging and Checkpoints

`Accelerator` initializes trackers with the project name `colbert` and logs loss/lr metrics during training. If the requested tracker is unavailable, choose an installed tracker or disable external logging in the user’s launch environment.

When `--save_on_epoch_end 1`, epoch checkpoints are saved under the run checkpoint directory and pruned by `--num_max_checkpoints`. The final model is saved separately under `output_dir/model` after training completes.
