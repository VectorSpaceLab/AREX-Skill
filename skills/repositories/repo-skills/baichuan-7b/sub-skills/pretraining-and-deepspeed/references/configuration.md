# Pretraining Configuration Reference

Baichuan-7B's demo pretraining path is intentionally small in code but assumes a real DeepSpeed cluster, GPU-capable dependencies, a SentencePiece tokenizer, and pre-sharded UTF-8 corpus files. This reference distills the configuration surfaces future agents need without reopening the source checkout.

## Source defaults

| Surface | Default / source value | Operational meaning |
|---|---:|---|
| Corpus directory | `data_dir` | Directory of UTF-8 text shard files consumed by all ranks. |
| Tokenizer path | `tokenizer.model` | SentencePiece model loaded before data tokenization. |
| Max sequence length | `4096` | `train.py` reshapes token IDs into `micro_batch_size x (max_length + 1)` and uses the shifted sequence for causal LM labels. |
| Steps per epoch | `4096` | Number of optimization steps between checkpoint saves. |
| Checkpoint path | `checkpoints` | DeepSpeed `save_checkpoint` output root. |
| EOS token id | `2` | Appended after each accepted input line in `DataEngine.load_data()`. |
| Minimum tokenized line length | `20` | Lines tokenizing to fewer than 20 IDs after EOS are discarded. |

## Corpus layout and sharding

The README says to divide the training corpus into multiple UTF-8 text files evenly according to a multiple of the total rank count, then place them under the corpus directory. `train.py` reads `os.listdir(data_dir)`, assigns files by index modulo `dist.get_world_size()`, and each rank loads its assigned files fully into memory before training.

Practical checks:

1. The corpus directory must contain regular text files only; nested directories can be selected by `os.listdir()` and then fail when opened as files.
2. File count should be at least the total rank count and normally a multiple of total ranks.
3. Shard sizes should be roughly balanced. Rank assignment is index-based, not size-aware.
4. Files should be UTF-8. The source opens with `errors="ignore"`, but silent byte dropping is dangerous for production data.
5. Each rank needs enough accepted token IDs to produce complete chunks of `train_micro_batch_size_per_gpu * (max_length + 1)` IDs for every training step before the next checkpoint.

Useful formula:

```text
token_ids_needed_per_rank_per_checkpoint_interval =
  train_micro_batch_size_per_gpu * steps_per_epoch * (max_length + 1)
```

The validator reports this formula but cannot prove exact token counts unless the real tokenizer and full corpus are sampled or processed.

## Tokenizer placement

The README instructs users to download `tokenizer.model` from the Baichuan-7B model release and place it at the repository root. The training parser default is also `tokenizer.model`, but users may pass another path with `--tokenizer_path`.

Preflight expectations:

- Path exists and is a non-empty file.
- When `sentencepiece` is available, the file should load as a SentencePiece model.
- The tokenizer vocabulary must contain token id `2`, because the training code appends EOS id `2` directly.
- Missing tokenizer failures occur before training data can be prepared.

## DeepSpeed JSON semantics

The source `config/deepspeed.json` contains these important settings:

| Key | Source value | Why it matters |
|---|---:|---|
| `train_micro_batch_size_per_gpu` | `1` | Read directly by `prepare_data()` to decide token chunk shape. Missing or non-positive values break data preparation. |
| `gradient_accumulation_steps` | `1` | Contributes to global batch size and optimizer cadence. |
| `optimizer.type` | `AdamW` | Used by DeepSpeed because `deepspeed.initialize(..., optimizer=None)` delegates optimizer construction to config. |
| `optimizer.params.lr` | `1e-8` | Demo learning rate; not validated as a best production schedule. |
| `zero_optimization.stage` | `2` | Demo uses ZeRO stage 2 with reduce-scatter and overlap communication. |
| `bf16.enabled` | `true` | Real training expects bf16-capable accelerator support. CPU-only checks do not validate this. |
| `tensorboard.output_path` | `logs/` | TensorBoard output directory in the active training workspace. |
| `steps_per_print` | `16` | DeepSpeed logging interval. |
| `gradient_clipping` | `1.0` | Optimizer stability setting. |

If a user changes ZeRO stage, precision, optimizer, or bucket sizes, treat the run as a new cluster-specific training configuration. Validate JSON shape and resource expectations, but do not claim the changed config reproduces the Baichuan training run.

## Hostfile format

The launcher uses:

```bash
deepspeed --hostfile config/hostfile --force_multi train.py --deepspeed --deepspeed_config config/deepspeed.json
```

DeepSpeed hostfile lines should use real reachable hostnames or IP addresses and a positive slot count:

```text
worker-a slots=8
worker-b slots=8
```

The repository's placeholder hostfile illustrates the shape with bracketed placeholders and an ellipsis; those placeholders are not runnable. Replace them before launch.

The total rank count is the sum of `slots=N` over runnable hostfile entries. Use that count for corpus shard validation and global-batch estimates:

```text
effective_global_batch = train_micro_batch_size_per_gpu * gradient_accumulation_steps * total_slots
```

## Training parser arguments

The source parser accepts these training-specific arguments before DeepSpeed adds its own config arguments:

| Argument | Default | Notes |
|---|---:|---|
| `--data_dir` | `data_dir` | UTF-8 corpus shard directory. |
| `--tokenizer_path` | `tokenizer.model` | SentencePiece tokenizer model path. |
| `--max_length` | `4096` | Maximum token sequence length per sample. |
| `--steps_per_epoch` | `4096` | Checkpoint interval in training steps. |
| `--checkpoint_saving_path` | `checkpoints` | Root directory for checkpoint tags. |
| `--local_rank` | `-1` | Reserved for DeepSpeed launcher injection. |
| `--deepspeed_config` | supplied by DeepSpeed args | Required by `prepare_data()` and `zero.Init(...)`. |

Use the renderer script to make these defaults explicit instead of relying on implicit path assumptions.
