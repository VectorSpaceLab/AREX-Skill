# Data Formats

This repository uses several similar-looking line formats. Choose the consumer first and do not silently convert one format into another. All examples below are one logical record per line and use UTF-8 unless the caller explicitly selects another encoding.

## Raw single-label classification

Canonical form:

```text
word1 word2 word3 __label__label_id
```

The text is everything before the first `__label__` marker. The label is the single, nonempty token after it. Keep whitespace between the text and marker; several source loaders call `split('__label__')`, so a missing marker, an extra marker, or whitespace inside the label changes the expected two-field result.

Use the validator's `single-label` mode for this contract. `--label-prefix` can name a different marker, but changing the marker only validates that alternate input; it does not change the repository loaders.

## Raw multi-label classification

The repository contains both common spellings:

```text
word1 word2 word3 __label__L1 __label__L2 __label__L3
word1 word2 word3 __label__L1 L2 L3
```

Both mean one text with labels `L1`, `L2`, and `L3`. The first marker separates text from labels. Later labels may repeat the marker or may be whitespace-separated after a single marker. Labels must be nonempty tokens. Preserve their order if a sequence model or a fixed top-label policy uses it; a flat multi-hot classifier otherwise treats them as an unordered set. Duplicate labels should be removed deliberately rather than accidentally changing label counts.

Use `multi-label` mode. Do not feed a multi-label line to a loader that performs exactly `x, y = line.split('__label__')` unless that loader explicitly splits the remaining label string.

## Prediction input TSV

Prediction loaders expect exactly two tab-separated fields:

```text
question_id<TAB>word1 word2 word3
```

`question_id` is an opaque, nonempty identifier and the text field is nonempty. Spaces do not replace the tab. An embedded tab creates a third field and is invalid for the repository's `question_id, question_string = line.split("\t")` pattern. This is input to prediction; repository prediction output is commonly comma-separated as `question_id,label1,label2,...`, not this TSV format.

Use `prediction-tsv` mode.

## Two-sentence relation rows

Relation loaders expect one tab in the text portion and one label marker:

```text
sentence one tokens<TAB>sentence two tokens __label__relation_label
```

Both sentences and the single relation label must be nonempty. The legacy loader first separates the label and then performs `x, x2 = x.split("\t")`. Extra tabs or markers therefore break its tuple unpacking. Use `relation` mode.

## Word and label dictionaries

Legacy utilities generally maintain paired mappings:

- `word2index`: token string to integer id.
- `index2word`: integer id to token string.
- `label2index`: label string to integer class id.
- `index2label`: integer class id to label string.

The forward and reverse maps must be exact inverses for every active entry. Indices used as dense tensor columns should be unique, nonnegative, and normally contiguous. Do not rebuild a label dictionary independently for train, validation, test, or prediction: column `i` in every multi-hot array and logit matrix must always represent the same label.

Word-vocabulary special ids vary by utility. Common paths reserve padding at `0` (`PAD_ID` or `_PAD`) and unknown at `1` (`UNK`), while word2vec-backed paths may reserve only padding and optionally `EOS` for relation text. Inspect the selected loader and checkpoint before assuming ids.

Label vocabularies are often frequency-sorted. That ordering is part of the model/cache contract, not presentation metadata. A checkpoint trained with one label ordering cannot safely use a newly sorted map.

## HDF5 and pickle caches

The common cache loader expects two coordinated files:

1. An HDF5 file with the exact, case-sensitive keys `train_X`, `train_Y`, `vaild_X`, `valid_Y`, `test_X`, and `test_Y`. Note the historical spelling `vaild_X` but `valid_Y`.
2. A binary pickle whose first object is exactly the two-item tuple `(word2index, label2index)`.

`*_X` arrays are normally rank-2 padded token-id arrays with a shared sequence width. For flat multi-label models, `*_Y` arrays are rank-2 multi-hot arrays whose second dimension is `len(label2index)`. Row counts must match within each split. Some older, model-specific pickle caches use different tuples, such as paired forward/reverse dictionaries or `(trainX, trainY, testX, testY, index2word)`; never infer interchangeability from the `.pkl`/`.pik` extension.

Pickle is executable serialization. Load only trusted caches. HDF5 and pickle files must come from the same preprocessing run so token ids, label columns, row order, and shapes remain aligned. The validator in this sub-skill checks raw text lines only; it intentionally does not deserialize either cache type.

## Adjacent n-grams

The repository helper expands tokens in position-major order, with n increasing at each position. For tokens `a b c`, minimum 1, maximum 3, and an empty join separator, the result is:

```text
a ab abc b bc c
```

Only adjacent tokens participate; no skip-grams, sorting, deduplication, or cross-line grams are used. The bundled generator exposes the join separator explicitly. With `--separator _`, the same record becomes `a a_b a_b_c b b_c c`. Empty separator matches the legacy concatenation but can create collisions (`a` + `bc` versus `ab` + `c`), so record the setting with generated data.

## Multi-hot and fixed-label alignment

For a label map of width `C`, every flat multi-label target is a length-`C` vector. Set column `label2index[label]` to `1` for each active label and leave other columns `0`. Unknown labels must be rejected or handled by an explicit policy; never append a new column to only one split.

Some legacy sampled-loss or seq2seq paths also keep a fixed-length list of label ids. Padding by repeating a label, padding with a reserved id, and truncating to a top-k list are distinct contracts. Do not substitute such a fixed label-id matrix for the dense multi-hot placeholder (`labels_l1999` or `input_y_multilabel`). For predictions, invert the same training `label2index` map before writing top labels.

## Seq2seq label tokens

When `use_seq2seq=True`, the label vocabulary reserves `_GO`, `_END`, and `_PAD` (commonly ids 0, 1, and 2) before ordinary labels. These are label-vocabulary tokens, not word-vocabulary tokens.

For decoder length 6 and labels `L1 L2 L3`:

```text
decoder_input: [_GO, L1, L2, L3, _PAD, _PAD]
target:        [L1, L2, L3, _END, _PAD, _PAD]
```

Retain at most `decoder_length - 1` ordinary labels, reserve a target position for `_END`, and pad both arrays to exactly the configured length. Flat sigmoid classifiers do not use these three special label tokens and should not include them in `num_classes` unless their specific source contract says otherwise.
