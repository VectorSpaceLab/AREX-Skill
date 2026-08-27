# Data Preparation Troubleshooting

Start with the raw-format contract and the selected loader. Do not “fix” source data in place: the bundled validator is read-only, and any conversion should write a new, reviewable artifact.

## Validator reports `missing-label-prefix`

**Symptoms**

- A training line is counted invalid.
- A legacy loader later raises unpacking errors around `split('__label__')`.

**Causes and actions**

- The wrong `--mode` was selected. Prediction TSV has no label marker; relation mode has a tab plus a marker.
- The file uses another marker. Confirm it, then validate with `--label-prefix`; remember the original loader still expects its hard-coded marker.
- The text was exported with labels in a separate column. Convert to a new file using an explicit, audited transformation.

## Single-label lines have too many labels

**Symptoms**

- `single-label` reports multiple markers or a label containing whitespace.
- Python raises “too many values to unpack.”

**Action**

Determine whether the dataset is actually multi-label. If so, use `multi-label` validation and a multi-label loader/model. Do not discard later labels just to satisfy a single-label parser.

## Multi-label lines appear valid but labels are wrong

**Symptoms**

- A label includes the marker text.
- Empty or duplicate labels occur.
- One spelling uses repeated markers and another uses a single marker.

**Action**

Validate the raw file in `multi-label` mode. It understands both repository spellings but warns about duplicates. Choose one canonical output spelling for any new converted file, preserve intended order when fixed top-label or seq2seq behavior depends on it, and do not modify the original file.

## Prediction TSV or relation rows have the wrong field count

**Symptoms**

- `prediction-tsv` reports not exactly two fields.
- Relation loading fails at `x, x2 = x.split("\t")`.

**Causes**

- Spaces were used instead of a literal tab.
- Text or an identifier contains an unescaped tab.
- A relation record has more than one tab or label marker.
- Prediction output (`question_id,label1,...`) was mistaken for prediction input TSV.

**Action**

Inspect the line-numbered diagnostic and the upstream export schema. The legacy formats provide no quoting or escaping convention for embedded tabs, so remove or encode them during a separate conversion step.

## Encoding errors or replacement characters

**Symptoms**

- `invalid-encoding` is reported at a physical line.
- `replacement-character` warnings occur with `--encoding-errors replace`.
- The first token contains an unexpected byte-order mark.

**Action**

Identify the real source encoding rather than repeatedly guessing. Use `--encoding utf-8-sig` for an intentional UTF-8 BOM. Prefer `--encoding-errors strict` for acceptance checks: replacement can merge or alter tokens and labels. The validator reports decoding problems but never rewrites bytes.

## Strict mode does not behave as expected

Without `--strict`, format errors are printed and summarized but do not make the process exit nonzero. This is intentional for inventory workflows. Add `--strict` when a pipeline must stop on one or more error diagnostics. Warnings alone do not fail strict mode. Argument, encoding-name, and file-open failures are operational errors and remain nonzero regardless of strict mode.

## N-grams differ from repository examples

**Symptoms**

- Expected `a ab abc b bc c`, but output is grouped by n.
- Generated grams contain underscores or spaces unexpectedly.
- Counts include cross-line or skip-grams.

**Action**

The bundled generator is position-major: for each starting token it emits allowed n in ascending order. It uses only adjacent tokens and resets at every input line. `--separator` joins components inside a gram and defaults to the legacy empty string. `--output-separator` joins emitted grams in plain output and defaults to one space. Record both options.

For `T` tokens and bounds `m..M`, the count is the sum of `max(T - n + 1, 0)` for each n in that range. Empty input produces no grams. The CLI rejects `min_n < 1`, `max_n < 1`, and `min_n > max_n`.

## Empty-separator n-gram collisions

`a` + `bc` and `ab` + `c` both become `abc` when the separator is empty. This matches the legacy helper but loses component boundaries. If the vocabulary was trained with concatenated grams, keep the empty separator. Otherwise choose an explicit separator before building both training and prediction vocabularies; changing it only at prediction time maps grams to the wrong ids.

## Word ids differ across splits or prediction

**Symptoms**

- Known words become unknown during prediction.
- Restored embedding shapes match but predictions are nonsensical.
- A token id decodes to another word.

**Cause**

A word dictionary was rebuilt, sorted differently, or assigned different special ids.

**Action**

Reuse the exact training map. Check forward/reverse round trips and confirm padding, unknown, and relation `EOS` ids against the selected utility. Matching vocabulary size is insufficient; ordering must match.

## Multi-hot width or label columns do not match

**Symptoms**

- Feed errors compare `[batch, C1]` with `[batch, C2]`.
- Predictions decode to unrelated labels.
- Validation/test arrays have fewer columns than training.

**Cause**

A split-specific label map was created, special seq2seq tokens were mixed into a flat map, or fixed label-id lists were passed to a dense multi-hot placeholder.

**Action**

Use one frozen `label2index`. Every multi-hot target and logit matrix must have width `len(label2index)`, even when a split lacks some classes. Confirm `index2label[label2index[x]] == x`. Keep `[batch, max_labels]` fixed id lists separate from `[batch, num_classes]` multi-hot arrays.

## Unknown labels appear after dictionary freeze

Do not silently append them: that changes the classifier projection and invalidates checkpoints and cached `Y` arrays. Determine whether the input belongs to the same task/version. Then reject it, map it under a documented existing policy, or rebuild all maps, arrays, and models as a new coordinated version.

## HDF5 key errors

**Symptoms**

- `KeyError: 'vaild_X'` or `KeyError: 'valid_Y'`.
- Train loads but validation does not.

**Action**

The common loader expects exact keys:

```text
train_X train_Y vaild_X valid_Y test_X test_Y
```

The inconsistent `vaild_X` spelling is historical. Do not assume conventional `valid_X` will work. Verify split row counts and that all `X` arrays share the expected sequence width and all multi-label `Y` arrays share the label width.

## Pickle unpacking errors

**Symptoms**

- “too many values to unpack” or “not enough values to unpack.”
- Dictionaries are returned where arrays were expected.

**Cause**

Repository pickle files have multiple incompatible contracts. The common HDF5 companion expects `(word2index, label2index)`, while older caches may contain paired forward/reverse maps or a five-item data tuple.

**Action**

Trace the exact `pickle.load` assignment in the selected consumer and use only a trusted artifact created for it. File extension and filename are not a schema. Never load an untrusted pickle merely to discover its contents.

## HDF5 and pickle are individually readable but incompatible

**Symptoms**

- Token ids exceed vocabulary size.
- Label width differs from `len(label2index)`.
- Data runs but labels decode incorrectly.

**Action**

Treat the two files as one versioned unit. Recreate or recover a coordinated pair from the same preprocessing run. Check maximum ids and shapes without changing either file. A coincidentally matching shape does not prove ordering alignment.

## Seq2seq labels are shifted incorrectly

**Symptoms**

- The model learns `_GO` as a target.
- `_END` is absent or overwrites an unexpected label.
- Decoder and target widths differ.

**Action**

For fixed length `D`, retain at most `D - 1` ordinary labels:

```text
decoder_input = [_GO] + retained + [_PAD ...]
target        = retained + [_END] + [_PAD ...]
```

Trim/pad both to exactly `D`. Use label-vocabulary ids and include `_GO`, `_END`, `_PAD` in seq2seq `num_classes`. Do not use these tokens in ordinary sigmoid label maps.

## Safe escalation

If raw validation is clean but a model still fails, hand off the immutable input path, validator summary, dictionary version, special ids, array shapes/dtypes, and cache schema to the relevant model sub-skill. Do not start full legacy training as a data-format diagnostic.
