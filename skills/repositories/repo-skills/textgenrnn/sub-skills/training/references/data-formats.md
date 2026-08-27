# Training Data Formats

## Purpose

Read this when choosing between `train_on_texts`, `train_from_file`, `train_from_largetext_file`, contextual training, and word-level training.

## In-memory text lists

Use `train_on_texts(texts, ...)` when the caller already has Python strings:

```python
texts = ["first training string", "second training string"]
textgen.train_on_texts(texts, num_epochs=1, gen_epochs=0)
```

For contextual training, pass `context_labels` with exactly the same length as `texts`:

```python
texts = ["A red example", "A blue example"]
labels = ["red", "blue"]
textgen.train_on_texts(texts, context_labels=labels, num_epochs=1, gen_epochs=0)
```

## Newline-delimited text files

Use `train_from_file(path, header=True, delim="\n", is_csv=False)` for a text file where each row is one training text. The default `header=True` skips the first line.

```text
text
A first example line.
A second example line.
```

If the file has no header row, pass `header=False`.

## One-column CSV files

Use `train_from_file(path, is_csv=True)` when the input is a CSV and the first column contains the text. The parser reads only the first column from each non-empty row and skips the header by default.

```csv
text
"A first example, with punctuation"
"A second example"
```

## Two-column context CSV files

Use `train_from_file(path, context=True)` for contextual training. The file must contain text in column 1 and the context label in column 2. The helper skips the header row by default.

```csv
text,label
"A legal question title","legaladvice"
"A relationship question title","relationships"
```

Context labels are binarized internally. Keep labels stable and meaningful; avoid mixing unrelated label schemes in one file.

## Single large text files

Use `train_from_largetext_file(path, new_model=True, ...)` when the file should be treated as one continuous document rather than independent rows. This sets `single_text=True` in the model config.

Single-large-text training is a different data regime. Keep `max_length` small enough for the corpus and batch size, and do not expect row-level context labels.

## Word-level training

Set `word_level=True` when calling `train_new_model`, `train_on_texts(new_model=True, ...)`, or `train_from_file(..., new_model=True, word_level=True)`. Word-level mode:

- lowercases through the tokenizer path;
- inserts spaces around punctuation before tokenization;
- uses `max_words` to limit vocabulary;
- usually needs a smaller `max_length` than the character-level default.

For word-level context training, combine `context=True` with `word_level=True` and a context CSV.

## Batch-size and sequence-count checks

Training creates many token sequences from the input texts, then asserts that the number of selected sequences is at least `batch_size`. If you see `Fewer tokens than batch_size`, reduce `batch_size`, add more/larger texts, reduce `train_size` only after increasing data, or choose a smaller `max_length` for tiny experiments.

## Artifact naming

Scratch training writes files using the `name` set when constructing the `textgenrnn` object:

```python
textgen = textgenrnn(name="my_model")
textgen.train_new_model(texts, num_epochs=1)
```

Expected artifacts:

- `my_model_config.json`
- `my_model_vocab.json`
- `my_model_weights.hdf5`
- optional `my_model_weights_epoch_<epoch>.hdf5` when `save_epochs > 0`

Keep the config, vocab, and weights files together. Generation from a scratch-trained model needs the matching triplet.
