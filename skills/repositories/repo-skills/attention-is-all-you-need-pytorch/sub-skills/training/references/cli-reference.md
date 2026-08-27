# Training CLI Reference

`train.py` is the training entry point. It parses command-line flags, prepares one of two dataloader branches, constructs `Transformer`, wraps Adam in `ScheduledOptim`, and starts the epoch loop.

The script does not provide a `--dry-run` flag and does not resume from existing checkpoints. Generate and inspect commands before launching them.

## Minimal command shapes

These examples call `python train.py` because `train.py` lives in a source checkout, not in an installed console entry point. Run the command from the checkout root or replace `train.py` with the path to the script.

All-in-one torchtext pickle:

```bash
python train.py \
  -data_pkl DATA.pkl \
  -output_dir output/run-name \
  -epoch 1 \
  -b 256 \
  -no_cuda
```

BPE-prefix files:

```bash
python train.py \
  -data_pkl BPE_VOCAB.pkl \
  -train_path DATA_PREFIX/train-prefix \
  -val_path DATA_PREFIX/val-prefix \
  -embs_share_weight \
  -proj_share_weight \
  -label_smoothing \
  -output_dir output/bpe-run \
  -epoch 1 \
  -b 256 \
  -warmup 128000 \
  -no_cuda
```

For BPE mode, `-train_path` and `-val_path` are prefixes; torchtext appends `.src` and `.trg`. Both prefixes must therefore have sibling files such as `train-prefix.src`, `train-prefix.trg`, `val-prefix.src`, and `val-prefix.trg`.

## Flags by responsibility

| Flag | Default | Use |
| --- | --- | --- |
| `-data_pkl DATA_PKL` | `None` | Required for normal pickle training. Also required for BPE training because the BPE branch loads vocabulary/settings from this pickle. |
| `-train_path TRAIN_PATH` | `None` | Enables BPE training when used together with `-val_path`. This is a path prefix, not a single file. |
| `-val_path VAL_PATH` | `None` | Validation prefix for BPE training. Must be supplied with `-train_path`. |
| `-output_dir OUTPUT_DIR` | `None` | Required. Created when missing. Logs and `save_mode=best` checkpoint are written here. |
| `-epoch EPOCH` | `10` | Number of full training epochs. README examples use 200 or 400, which are long runs. |
| `-b`, `--batch_size` | `2048` | Batch size passed to torchtext `BucketIterator`. README examples use 256. |
| `-warmup`, `--n_warmup_steps` | `4000` | Warmup steps used by `ScheduledOptim`. A warning is printed when batch size is below 2048 and warmup is at most 4000. |
| `-lr_mul LR_MUL` | `2.0` | Multiplier applied to the Transformer learning-rate schedule. The provided shell launcher documents `0.5` with `scale_emb_or_prj=emb` as a better setting. |
| `-seed SEED` | `None` | Seeds PyTorch, NumPy, and Python `random`; also disables cuDNN benchmark. |
| `-no_cuda` | off | Forces CPU. Without this flag, the script selects `cuda` even on hosts where CUDA may not be usable. |
| `-use_tb` | off | Imports `torch.utils.tensorboard.SummaryWriter` and writes TensorBoard events below `OUTPUT_DIR/tensorboard`. Requires TensorBoard support in the runtime environment. |
| `-save_mode {best,all}` | `best` | `best` writes `OUTPUT_DIR/model.chkpt` when validation loss improves. `all` writes `model_accu_*.chkpt` in the process working directory. |
| `-label_smoothing` | off | Enables 0.1 label smoothing in `cal_loss`. |

## Model construction flags

`train.py` sets `opt.d_word_vec = opt.d_model`, then constructs `Transformer` with the following training-facing arguments:

| Flag | Transformer argument | Default | Note |
| --- | --- | --- | --- |
| `-d_model` | `d_model`, `d_word_vec` | `512` | Must match embedding dimension because the model asserts `d_model == d_word_vec`. |
| `-d_inner_hid` | `d_inner` | `2048` | Feed-forward hidden width. |
| `-d_k` | `d_k` | `64` | Per-head key/query width. |
| `-d_v` | `d_v` | `64` | Per-head value width. |
| `-n_head` | `n_head` | `8` | Number of attention heads. |
| `-n_layers` | `n_layers` | `6` | Encoder and decoder layer count. |
| `-dropout` | `dropout` | `0.1` | Dropout throughout the model. |
| `-proj_share_weight` | `trg_emb_prj_weight_sharing` | `False` | Ties target embedding and output projection. Usually safe when target vocabulary is fixed. |
| `-embs_share_weight` | `emb_src_trg_weight_sharing` | `False` | Ties source and target embeddings. Normal pickle mode asserts identical source/target vocabulary maps when this is set. BPE mode requires it. |
| `-scale_emb_or_prj` | `scale_emb_or_prj` | `prj` | Must be one of `emb`, `prj`, or `none` at model construction time. Scaling only applies when projection weight sharing is enabled. |

## Data schemas consumed by training

Normal pickle mode expects `-data_pkl` to load a dictionary with:

- `settings.max_len`;
- `vocab['src']` and `vocab['trg']`, each a torchtext `Field` with a `.vocab` object;
- `vocab['src'].vocab.stoi['<blank>']` and `vocab['trg'].vocab.stoi['<blank>']` for padding;
- `train` and `valid` example lists compatible with `torchtext.data.Dataset` fields `src` and `trg`.

BPE mode expects `-data_pkl` to load a dictionary with:

- `settings.max_len`;
- `vocab`, a single torchtext `Field` shared by source and target;
- prefix files `TRAIN_PREFIX.src`, `TRAIN_PREFIX.trg`, `VAL_PREFIX.src`, and `VAL_PREFIX.trg`.

The padding token is `'<blank>'`.

## README and launcher adaptations

The README training examples document the intended workflows but include a stale `-log` flag that the current parser does not accept. Drop `-log` when building commands.

The repository shell launcher corresponds to this shape:

```bash
CUDA_VISIBLE_DEVICES=0 python train.py \
  -data_pkl multi30k_de_en.pkl \
  -label_smoothing \
  -proj_share_weight \
  -scale_emb_or_prj emb \
  -lr_mul 0.5 \
  -b 256 \
  -warmup 4000 \
  -epoch 200 \
  -seed 1 \
  -output_dir output/lr_mul_0.5-scale_emb \
  -use_tb
```

Use `scripts/build_training_command.py` to generate this safely instead of copying a shell command that may hide GPUs or omit CPU flags.
