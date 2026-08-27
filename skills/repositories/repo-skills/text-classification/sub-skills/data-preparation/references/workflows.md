# Data Preparation Workflows

These workflows keep preparation separate from training. The bundled helpers read input and write only their own stdout; they never rewrite source files, load TensorFlow, open checkpoints, or deserialize caches.

## 1. Identify the consumer and freeze the contract

Before changing data, record:

- the exact training or prediction script;
- single-label, multi-label, prediction TSV, or relation mode;
- input encoding and label marker;
- word and label dictionary files and their special ids;
- sequence width, label width, and any top-k/fixed-label length;
- whether the downstream path expects raw text, padded arrays, HDF5/pickle caches, or seq2seq label arrays.

Do not normalize all repository datasets to one universal format. Several loaders use incompatible tuple shapes and special-token policies.

## 2. Validate raw lines without mutation

Validate a file in report-only mode:

```bash
python scripts/validate_text_classification_data.py \
  --mode single-label data/sample.txt
```

Make invalid input affect the process status by adding `--strict`:

```bash
python scripts/validate_text_classification_data.py \
  --mode multi-label --strict data/sample.txt
```

Read stdin by using `-` or omitting the path:

```bash
cat data/predict.tsv | python scripts/validate_text_classification_data.py \
  --mode prediction-tsv --strict -
```

For machine-readable output:

```bash
python scripts/validate_text_classification_data.py \
  --mode relation --encoding utf-8 --json relations.txt
```

Use `--label-prefix` only when the source data intentionally uses a different marker. It does not modify the marker or make legacy loaders understand it. `--encoding-errors strict` reports an undecodable physical line as an error and continues with later lines; `replace` decodes with replacement and emits a warning.

The text and JSON summaries are deterministic for identical bytes and arguments. Diagnostics carry physical 1-based line numbers. Without `--strict`, data errors are still reported but the validator returns success so it can be used for exploratory inventory. CLI misuse and I/O failures remain failures.

## 3. Expand adjacent n-grams deterministically

Generate from positional token arguments:

```bash
python scripts/generate_ngrams.py --min-n 1 --max-n 3 a b c
```

Generate from one text argument:

```bash
python scripts/generate_ngrams.py --text "a b c" --separator _
```

Generate one independent output record per file or stdin line:

```bash
python scripts/generate_ngrams.py --file sentences.txt --max-n 3
cat sentences.txt | python scripts/generate_ngrams.py --stdin --max-n 3
```

If no source and no positional tokens are supplied, stdin is the default. File/stdin lines never share a gram. Blank input lines produce blank output lines, preserving record alignment. `--encoding` applies to files and stdin decoding. `--output-separator` controls how generated grams are printed; `--separator` controls how component tokens inside each gram are joined. These are separate choices.

JSON output records the configuration, source, 1-based record number, input tokens, and generated grams:

```bash
python scripts/generate_ngrams.py --text "a b c" --separator "::" --json
```

The reusable `generate_ngrams(tokens, min_n=1, max_n=3, separator="")` function returns a new list and does not mutate `tokens`.

## 4. Build dictionaries once

1. Decide special word ids required by the selected loader (`PAD_ID`, `_PAD`, `UNK`, or relation `EOS`).
2. Build `word2index` and its inverse from the training corpus or the exact pretrained vocabulary expected by the model.
3. Build one `label2index` ordering. If frequency sorting is used, make the tie-breaking and corpus version reproducible.
4. Invert both maps and verify every round trip.
5. Freeze and version the maps before creating any split arrays.
6. Reuse the frozen maps for validation, test, prediction, checkpoint restore, and output decoding.

Unknown words can normally map to the selected unknown id. Unknown labels need an explicit reject/drop policy because silently extending the label map changes logits and checkpoint shapes.

## 5. Create padded inputs and aligned labels

For every split:

1. Tokenize with the same whitespace/token policy used to build the vocabulary.
2. Optionally expand adjacent n-grams using the recorded min/max n and separator.
3. Map tokens to ids, truncate according to the model's policy, and pad every row to the same sequence width.
4. For flat multi-label classification, allocate `[number_of_rows, len(label2index)]` and set mapped label columns to one.
5. For single-label classification, store one integer class id per row only if the model uses a sparse-label placeholder.
6. For fixed label-id lists, apply the exact truncation and padding policy of that consumer; do not pass them to a multi-hot placeholder.
7. Confirm each `X` and `Y` split has the same row count.

Keep label alignment fixed even if a validation or test split contains only a subset of classes. Its `Y` width remains the training width.

## 6. Package coordinated caches

When using the common HDF5/pickle loader:

- write HDF5 datasets with exact keys `train_X`, `train_Y`, `vaild_X`, `valid_Y`, `test_X`, `test_Y`;
- write the trusted binary pickle object `(word2index, label2index)`;
- create both from the same in-memory preprocessing result;
- record dtypes, shapes, sequence length, label count, preprocessing settings, and source checksums externally;
- stage new files and switch consumers only after both are complete.

Do not open an untrusted pickle to “inspect” it. Do not rename the historical `vaild_X` key unless every reader is changed together. Older model-specific pickles can contain four dictionaries or five data objects and must stay tied to their original loader.

## 7. Prepare seq2seq labels

Use the label vocabulary, not the word vocabulary:

1. Reserve `_GO`, `_END`, `_PAD` before ordinary labels.
2. Choose `decoder_length` and retain at most `decoder_length - 1` gold labels.
3. Build `decoder_input = [_GO] + retained_labels`, then pad.
4. Build `target = retained_labels + [_END]`, then pad.
5. Confirm both arrays have identical fixed width and that `num_classes` includes all three special tokens.

Prediction starts with `_GO` and padding, and downstream decoding should filter special tokens and duplicates according to the selected sequence model. Do not add these tokens to ordinary flat-classifier label maps.

## 8. Handoff checklist

Before model work begins, hand off:

- validator mode, arguments, summary, and whether strict status was used;
- immutable source location (the validator never rewrites it);
- tokenization and n-gram settings;
- dictionary artifacts and special ids;
- array shapes and dtypes for every split;
- label width and a few label/index round trips;
- cache key list and pickle tuple contract without loading untrusted data;
- seq2seq shift/truncation policy when applicable.

Only after these contracts match the model placeholders should a model-specific graph inspection or training workflow begin.
