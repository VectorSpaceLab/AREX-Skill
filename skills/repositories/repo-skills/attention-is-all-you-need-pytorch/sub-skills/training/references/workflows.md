# Training Workflows

This reference turns the training source and README examples into safe operating workflows. It intentionally avoids launching full training.

## Preflight checklist

Before a long run:

1. Confirm the runtime has PyTorch, legacy torchtext, dill, NumPy, and tqdm. TensorBoard is only needed when using `-use_tb`.
2. Confirm the data mode and schema described in [cli-reference.md](cli-reference.md#data-schemas-consumed-by-training).
3. Decide CPU or GPU. Use `-no_cuda` unless CUDA has been checked and requested.
4. Choose an output directory. It may be created by `train.py`, but the parent location should be writable.
5. Generate a command with `scripts/build_training_command.py`; inspect it instead of launching it blindly.
6. Optionally run `scripts/training_smoke_check.py --repo-root <checkout>` to verify import, loss, tiny model forward, and `ScheduledOptim` behavior.

## Data-mode workflows

### All-in-one pickle mode

Use this mode for the default preprocessing path that saves train/valid examples and separate `src`/`trg` vocab fields into one pickle.

Safe command-building example:

```bash
python scripts/build_training_command.py \
  --data-pkl DATA.pkl \
  --output-dir output/cpu-check \
  --preset safe-cpu \
  --check-paths
```

Generated command shape:

```bash
python train.py -data_pkl DATA.pkl -output_dir output/cpu-check -epoch 1 -b 256 -warmup 4000 -no_cuda
```

If you set `-embs_share_weight`, the pickle branch asserts that source and target `vocab.stoi` dictionaries are identical. If they differ, either preprocess with shared vocabulary or remove `-embs_share_weight`.

### BPE-prefix mode

Use this mode only when you already have the BPE vocabulary pickle and encoded prefix files. The upstream README marks BPE-related parts as not fully tested, so treat this path as a careful/manual workflow.

Required command inputs:

- `-data_pkl BPE_VOCAB.pkl` containing `settings.max_len` and one shared `vocab` field;
- `-train_path TRAIN_PREFIX` with `TRAIN_PREFIX.src` and `TRAIN_PREFIX.trg`;
- `-val_path VAL_PREFIX` with `VAL_PREFIX.src` and `VAL_PREFIX.trg`;
- `-embs_share_weight`, because the BPE dataloader raises if embedding sharing is not requested.

Command-building example:

```bash
python scripts/build_training_command.py \
  --data-pkl BPE_VOCAB.pkl \
  --bpe-train-prefix bpe_deen/deen-train \
  --bpe-val-prefix bpe_deen/deen-val \
  --output-dir output/bpe-cpu-check \
  --preset readme-shared \
  --epochs 1 \
  --cpu \
  --check-paths
```

## Training helper map

`train.py` helper behavior that matters when debugging or adapting a run:

| Helper | Role | Operational note |
| --- | --- | --- |
| `main()` | Parses flags, sets seeds, creates `-output_dir`, chooses device, loads data, builds `Transformer`, wraps Adam in `ScheduledOptim`, and calls `train`. | Data branch order is BPE when both `-train_path` and `-val_path` are present; otherwise all-in-one pickle when `-data_pkl` is present. Missing both branches raises. |
| `prepare_dataloaders(opt, device)` | Normal pickle branch. | Loads `vocab['src']`, `vocab['trg']`, `train`, and `valid`; asserts identical `stoi` dictionaries if `-embs_share_weight` is set. |
| `prepare_dataloaders_from_bpe_files(opt, device)` | BPE-prefix branch. | Requires `-embs_share_weight`; loads one shared field from `data['vocab']`; uses `TranslationDataset` with `.src`/`.trg` extensions and filters by `settings.max_len`. |
| `patch_src(src, pad_idx)` | Converts torchtext time-major source batches to batch-major tensors. | Transposes from `[time, batch]` to `[batch, time]`; `pad_idx` is accepted but unused. |
| `patch_trg(trg, pad_idx)` | Converts torchtext time-major target batches to decoder input and flattened gold labels. | Transposes to batch-major, returns decoder input without last token and gold labels shifted by one position. |
| `cal_loss` / `cal_performance` | Computes summed cross-entropy/label-smoothed loss and non-pad accuracy counts. | Padding target index is ignored/masked; average loss is computed later by epoch helpers. |
| `train_epoch` | Runs one training epoch over a `BucketIterator`. | Calls model forward, loss backward, and `optimizer.step_and_update_lr()` once per batch. |
| `eval_epoch` | Runs validation without gradients. | Uses no label smoothing in validation metrics. |
| `train` | Runs epochs, writes CSV logs, optional TensorBoard curves, and checkpoints. | It truncates logs at start and has no resume path. |

## Hyperparameter starting points

- Source defaults: `epoch=10`, `batch_size=2048`, `d_model=512`, `d_inner_hid=2048`, `d_k=64`, `d_v=64`, `n_head=8`, `n_layers=6`, `warmup=4000`, `lr_mul=2.0`, `dropout=0.1`, `scale_emb_or_prj=prj`, `save_mode=best`.
- README pickle example: `batch_size=256`, `warmup=128000`, `epoch=400`, shared embeddings, projection sharing, and label smoothing.
- Shell-launcher/performance example: `batch_size=256`, `warmup=4000`, `epoch=200`, `lr_mul=0.5`, `scale_emb_or_prj=emb`, projection sharing, label smoothing, seed 1, TensorBoard enabled.
- For CPU planning, use small epochs and `-no_cuda`; do not infer training quality from a tiny run.

## Loss and label smoothing

`cal_loss(pred, gold, trg_pad_idx, smoothing=False)` flattens `gold`, ignores target padding, and returns a summed loss. With smoothing enabled, it builds a 0.1-smoothed one-hot distribution and masks pad positions after computing token losses.

`cal_performance(pred, gold, trg_pad_idx, smoothing=False)` returns `(loss, n_correct, n_word)` after excluding pad positions. Accuracy in logs is `n_correct / n_word` and is printed as a percentage.

Training and validation epoch functions divide summed loss by non-pad target words, then compute perplexity as `exp(min(loss_per_word, 100))`.

## Optimizer schedule

Training wraps Adam as:

```text
Adam(parameters, betas=(0.9, 0.98), eps=1e-09)
ScheduledOptim(optimizer, lr_mul, d_model, n_warmup_steps)
```

On each training batch, `ScheduledOptim.step_and_update_lr()` increments `n_steps`, computes:

```text
lr = lr_mul * d_model**-0.5 * min(n_steps**-0.5, n_steps * n_warmup_steps**-1.5)
```

and writes that learning rate into every Adam parameter group before stepping.

The code warns when `batch_size < 2048` and `warmup <= 4000`, because the original setting was `(2048, 4000)` and small batches may finish warmup after too little data. The README examples often compensate with much larger warmup such as `128000`.

## Logs, checkpoints, and TensorBoard

At training start, the script creates or truncates:

- `OUTPUT_DIR/train.log` with columns `epoch,loss,ppl,accuracy`;
- `OUTPUT_DIR/valid.log` with columns `epoch,loss,ppl,accuracy`.

For every epoch it prints training and validation perplexity, accuracy, current learning rate, and elapsed minutes. It appends one CSV row per epoch to each log.

Checkpoint behavior:

- `-save_mode best`: writes `OUTPUT_DIR/model.chkpt` whenever validation loss is no worse than the best seen so far. The checkpoint contains `epoch`, `settings`, and `model` keys.
- `-save_mode all`: writes `model_accu_*.chkpt` into the process working directory. Use this only when that location is intentional.

TensorBoard behavior:

- `-use_tb` imports `torch.utils.tensorboard.SummaryWriter`.
- Events go under `OUTPUT_DIR/tensorboard`.
- It records train/validation perplexity, train/validation accuracy, and learning rate.

## What not to do from this sub-skill

- Do not generate or download datasets here; use the data-preparation sub-skill.
- Do not translate checkpoints here; use the translation sub-skill.
- Do not launch 200- or 400-epoch training unless the user explicitly asks and has provided data, output location, device choice, and runtime budget.
