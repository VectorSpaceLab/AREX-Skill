# Training workflows

These recipes are distilled from the repository's training notes and source behavior.
They are intentionally self-contained so a future agent can complete the common training tasks without reopening the source tree.

## 1) Fine-tune the bundled model on in-memory texts

Use this when you already have a list of strings and want to continue from the packaged pretrained weights.

```python
from textgenrnn import textgenrnn

textgen = textgenrnn()
textgen.train_on_texts(
    texts,
    num_epochs=2,
    gen_epochs=0,
    validation=False,
)
```

Notes:
- `gen_epochs=0` keeps smoke runs fast.
- `validation=False` skips the validation generator when you only need a quick artifact check.
- Use `train_on_texts(..., new_model=False)` for continued fine-tuning.

## 2) Train a scratch model from texts

Use this when you want a new vocabulary, a new config, or a custom architecture.

```python
from textgenrnn import textgenrnn

textgen = textgenrnn(name="my_model")
textgen.train_new_model(
    texts,
    num_epochs=1,
    gen_epochs=0,
    validation=False,
    batch_size=2,
    max_length=20,
    rnn_size=32,
    dim_embeddings=16,
)
```

Notes:
- Scratch training writes the config and vocab before the first epoch runs.
- `word_level=True` is a common scratch-model choice for tokenized prose.
- Reduce `max_length` for word-level inputs so the token windows stay compact.

## 3) Train from a newline file or one-column CSV

Use `train_from_file` when the source data lives on disk.

```python
textgen.train_from_file("data.txt", new_model=True, num_epochs=5, gen_epochs=1)
textgen.train_from_file("data.csv", new_model=True, is_csv=True, num_epochs=5)
```

Notes:
- Plain text mode splits on `delim`, which defaults to newline.
- `header=True` is the default, so the first row is skipped.
- `is_csv=True` reads the first column from a one-column CSV export.

## 4) Train with context labels

Use this when a second label stream should influence training.

### In memory

```python
textgen.train_new_model(
    texts,
    context_labels=labels,
    num_epochs=10,
    gen_epochs=5,
    max_length=5,
)
```

### Two-column CSV

```python
textgen.train_from_file(
    "context.csv",
    new_model=True,
    context=True,
    num_epochs=10,
    gen_epochs=5,
)
```

Notes:
- `context_labels` must align one-for-one with `texts`.
- The CSV reader expects text in column 1 and label in column 2.
- Context training still writes the same scratch-model artifact set.

## 5) Train on a single large text block

Use this for one-document corpora or classic char-RNN style training.

```python
textgen.train_from_largetext_file(
    "novel.txt",
    new_model=True,
    num_epochs=1,
    max_gen_length=50,
    word_level=True,
    max_length=10,
    max_words=5000,
)
```

Notes:
- The file is loaded as one document and passed through with `single_text=True`.
- This path is the right fit for long-form prose, lyrics, or logs.
- Smaller `max_length` values usually work better in word-level mode.

## 6) Transfer learning from an existing model

Use this when you want to continue training on a different corpus after an initial run.

```python
textgen.train_from_file("corpus_a.txt", new_model=True, num_epochs=10, gen_epochs=10)
textgen.train_from_file("corpus_b.txt", num_epochs=5, gen_epochs=1)
```

Notes:
- The second call keeps the current model instead of resetting it.
- When you want to reload a scratch model later, load the matching weights, vocab, and config together.
- A shorter second run is usually enough for transfer learning.

## 7) Control overfitting and save checkpoints

Use this when you want a validation split or periodic weight snapshots.

```python
textgen.train_from_file(
    "data.txt",
    new_model=True,
    num_epochs=5,
    gen_epochs=5,
    train_size=0.8,
    dropout=0.2,
    save_epochs=5,
)
```

Notes:
- `train_size=0.8` holds out the remaining sequences for validation when `validation=True`.
- `dropout` can help on small corpora, but too much dropout slows or harms convergence.
- `save_epochs` is useful when you want intermediate checkpoints during long runs.

## 8) Optional multi-GPU acceleration

Use this only when TensorFlow sees multiple GPUs and you want faster training throughput.

```python
textgen.train_new_model(texts, multi_gpu=True, batch_size=32, num_epochs=5)
```

Notes:
- CPU training is still a valid backend for correctness checks.
- The implementation scales the batch size by the visible GPU count.
- Leave `multi_gpu=False` unless you have a verified GPU backend.

## Quick artifact checklist

- Scratch runs should produce `name_config.json`, `name_vocab.json`, and `name_weights.hdf5`.
- Snapshot runs add `name_weights_epoch_<epoch>.hdf5` files.
- A smoke run with `gen_epochs=0` and `validation=False` is for correctness, not output quality.
- Poor sample quality on a tiny fixture is expected; use a larger corpus or more epochs for a real training run.
