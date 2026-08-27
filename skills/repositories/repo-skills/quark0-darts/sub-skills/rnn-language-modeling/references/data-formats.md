# RNN Data Formats

The recurrent workflows use plain text language-modeling corpora. There is no dataset loader abstraction beyond the local corpus path and the three required text files.

## Required corpus layout

Point `--data` at a directory, not an individual file:

```text
<corpus-root>/
  train.txt
  valid.txt
  test.txt
```

The default PTB path is `../data/penn/`. The WT2 recipe overrides this with `--data ../data/wikitext-2`.

## Tokenization and dictionary behavior

`Corpus(path)` creates one shared `Dictionary` and tokenizes the files in this order: `train.txt`, `valid.txt`, then `test.txt`.

Tokenization rules:

- Each file is read as UTF-8 text.
- Each line is split by Python whitespace splitting: `line.split()`.
- The token `<eos>` is appended to every line after splitting; blank lines therefore contribute one `<eos>` token.
- No lowercasing, punctuation normalization, OOV replacement, vocabulary file, or sentence metadata is used.
- `Dictionary.add_word(word)` assigns an integer id on first sight, increments a per-token counter, and increments the total token count. Because the same dictionary is reused across all splits, tokens first seen in `valid.txt` or `test.txt` are also added to the dictionary.
- `Corpus.tokenize(file_path)` returns a flat `torch.LongTensor` of token ids for that file.

`SentCorpus` mirrors the same tokenization rules but returns a list of one `LongTensor` per line. `BatchSentLoader` can iterate sorted, padded sentence batches, but the PTB/WT2 training and test scripts use the flat `Corpus` path instead.

## Batch shapes

`batchify(data, bsz, args)` is the shape transition from a flat token stream to recurrent minibatches:

1. Compute `nbatch = data.size(0) // bsz`.
2. Trim off leftover tokens with `data.narrow(0, 0, nbatch * bsz)`.
3. Reshape as `data.view(bsz, -1).t().contiguous()`.
4. If `args.cuda` is true, move the resulting tensor to CUDA.

The returned tensor has shape:

```text
[time_steps, batch_size]
```

For a token stream of length `N`, `time_steps = floor(N / batch_size)` after trimming.

`get_batch(source, i, args, seq_len=None, evaluation=False)` slices a BPTT segment:

- `seq_len = min(seq_len or args.bptt, len(source) - 1 - i)`.
- `data = source[i : i + seq_len]` has shape `[seq_len, batch_size]`.
- `target = source[i + 1 : i + 1 + seq_len]` has shape `[seq_len, batch_size]` before callers flatten it.
- Training and evaluation call `targets.view(-1)` before negative log-likelihood loss, yielding length `seq_len * batch_size`.
- `evaluation=True` creates legacy non-gradient variables for validation/test batches.

Hidden state is not encoded in the dataset. The scripts initialize it with `model.init_hidden(batch_size)` or `model.init_hidden(small_batch_size)` and call `repackage_hidden()` between segments so gradients do not span the entire corpus.

## Split usage by workflow

| Workflow | Split usage |
| --- | --- |
| `train_search.py` | `train.txt` trains network weights; `valid.txt` is batched once as `search_data` for architecture updates and once as `val_data` for epoch validation; `test.txt` is loaded but not used for final testing. |
| `train.py` | `train.txt` trains the model; `valid.txt` selects checkpoints and triggers ASGD switching; `test.txt` is evaluated after the best checkpoint is reloaded. |
| `test.py` | Only `test.txt` is batchified for evaluation, but `Corpus` still asserts and tokenizes all three files because it always constructs train/valid/test splits. |

## Validation checklist

Before planning a run, verify these conditions from the user's dataset description or with a safe static check:

- The `--data` value points to the corpus directory.
- `train.txt`, `valid.txt`, and `test.txt` all exist with those exact names.
- Files are text-readable with UTF-8-compatible content.
- Each split has enough tokens after whitespace splitting plus `<eos>` to form at least one batch at the intended `batch_size`.
- The vocabulary size is nonzero, and `<eos>` is present.
- For custom text, the user understands that no OOV mapping is applied; validation/test-only tokens expand the shared dictionary.
- The chosen `batch_size` and `small_batch_size` are compatible: `batch_size % small_batch_size == 0` after defaulting `small_batch_size` to `batch_size`.
- The planned `bptt`, `batch_size`, `small_batch_size`, and hidden dimensions fit the available accelerator memory.
