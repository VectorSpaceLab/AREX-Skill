# CLI Reference

## Commands

| Command | Entry point | Purpose | Safe checks |
| --- | --- | --- | --- |
| `bert-vocab` | `bert_pytorch.dataset.vocab:build` | Build a pickled vocabulary from a corpus file. | `--help`, tiny corpus smoke |
| `bert` | `bert_pytorch.__main__:train` | Train a BERT model and save checkpoints. | `--help`, tiny corpus/vocab smoke |

## `bert-vocab` flags

| Flag | Meaning | Default | Notes |
| --- | --- | --- | --- |
| `-c`, `--corpus_path` | Input corpus file | required | Each line should contain two sentences separated by a tab. |
| `-o`, `--output_path` | Output vocabulary file | required | The file is a pickle, not plain text. |
| `-s`, `--vocab_size` | Maximum vocab size | `None` | Optional cap before the special tokens are prepended. |
| `-e`, `--encoding` | File encoding | `utf-8` | Use a matching encoding for your corpus. |
| `-m`, `--min_freq` | Minimum token frequency | `1` | Tokens below this frequency are dropped. |

## `bert` flags

| Flag | Meaning | Default | Notes |
| --- | --- | --- | --- |
| `-c`, `--train_dataset` | Training corpus file | required | Same two-sentences-per-line layout as `bert-vocab`. |
| `-t`, `--test_dataset` | Optional evaluation corpus | `None` | If present, `trainer.test(epoch)` runs after each epoch. |
| `-v`, `--vocab_path` | Pickled vocabulary file | required | Build it first with `bert-vocab` or the bundled smoke script. |
| `-o`, `--output_path` | Checkpoint prefix | required | `trainer.save(epoch, output_path)` appends `.ep{epoch}`. |
| `-hs`, `--hidden` | Hidden size | `256` | Must be divisible by `--attn_heads`. |
| `-l`, `--layers` | Transformer layers | `8` | Larger values raise compute and memory cost. |
| `-a`, `--attn_heads` | Attention heads | `8` | Must divide `--hidden`. |
| `-s`, `--seq_len` | Maximum sequence length | `20` | Longer sequences increase memory use. |
| `-b`, `--batch_size` | Batch size | `64` | Reduce for small memory budgets or smoke runs. |
| `-e`, `--epochs` | Epoch count | `10` | Use `1` for smoke checks. |
| `-w`, `--num_workers` | DataLoader workers | `5` | Use `0` for deterministic smoke runs. |
| `--with_cuda` | Train with CUDA when available | `True` | Parsed with `type=bool`; do not rely on `False` strings to disable it. Use the bundled training helper for explicit device selection. |
| `--log_freq` | Print frequency | `10` | Lower it for tiny smoke runs. |
| `--corpus_lines` | Corpus line count | `None` | Needed when using streaming mode. |
| `--cuda_devices` | CUDA device IDs | `None` | Only relevant when multiple GPUs are visible. |
| `--on_memory` | Load corpus into memory | `True` | Parsed with `type=bool`; use the helper script or Python API if you need an explicit streaming run. |
| `--lr` | Adam learning rate | `1e-3` | Smaller values may stabilize smoke runs. |
| `--adam_weight_decay` | Adam weight decay | `0.01` | Standard optimizer regularization. |
| `--adam_beta1` | Adam beta 1 | `0.9` | Passed to the optimizer. |
| `--adam_beta2` | Adam beta 2 | `0.999` | Passed to the optimizer. |

## Example CLI pattern

Use the bundled tiny corpus helper first, then build a vocab. If you specifically want to exercise the raw CLI, the following syntax matches the documented entry points; for a more robust tiny-data smoke run, prefer `sub-skills/training/scripts/train_smoke.py`.

```bash
python scripts/make_tiny_corpus.py --output /tmp/bert-pytorch-corpus.txt
bert-vocab -c /tmp/bert-pytorch-corpus.txt -o /tmp/bert-pytorch-vocab.pkl
bert -c /tmp/bert-pytorch-corpus.txt -v /tmp/bert-pytorch-vocab.pkl -o /tmp/bert-pytorch-model -e 1 -b 2 -s 8 -w 0
```

For an explicit CPU or CUDA smoke, prefer `sub-skills/training/scripts/train_smoke.py` instead of the raw CLI when you need to avoid the boolean-flag caveat.
