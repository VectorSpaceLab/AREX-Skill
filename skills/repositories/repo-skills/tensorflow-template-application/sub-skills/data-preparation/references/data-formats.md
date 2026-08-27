# Data Formats

## Dense CSV

- Default assumption for this sub-skill: the label is the **last** column.
- Legacy CSV files in this repository are mixed: `cancer` uses label-last, while `iris`, `boston_housing`, and `lung` examples use label-first.
- The bundled CSV converter supports `--label-position first|last` so future agents can match either layout explicitly.
- The bundled CSV converter also supports `--label-type int|float`.

Typical dense row with label last:

```text
5.1,3.5,1.4,0.2,0
```

Interpretation:

- `5.1,3.5,1.4,0.2` -> feature values stored as floats
- `0` -> label stored as either `int64` or `float` depending on `--label-type`

Typical dense row with label first:

```text
0,5.1,3.5,1.4,0.2
```

Use label-first only when the caller explicitly wants legacy repository layout.

## Sparse LIBSVM

- Format: `label id:value id:value ...`
- The label is the first token.
- Each `id` is stored as an int64 value.
- Each `value` is stored as a float value.
- The helper preserves the token order and does not renumber ids.

Example:

```text
1 4:0.2 9:1.0 23:0.5
```

## TFRecords schema: dense

A dense TFExample uses these feature keys:

- `label`
- `features`

Stored types:

- `label` -> `tf.train.Int64List([label])` or `tf.train.FloatList([label])`
- `features` -> `tf.train.FloatList([...])`

The dense schema is invalid if `features` is missing or if sparse-only fields appear instead.

## TFRecords schema: sparse

A sparse TFExample uses these feature keys:

- `label`
- `ids`
- `values`

Stored types:

- `label` -> `tf.train.Int64List([label])` or `tf.train.FloatList([label])`
- `ids` -> `tf.train.Int64List([...])`
- `values` -> `tf.train.FloatList([...])`

The sparse schema is invalid if `ids` and `values` are missing or if their lengths differ.

## Iris tiny fixture

- Generated from `sklearn.datasets.load_iris()`.
- No network access is needed.
- The fixture generator selects a tiny deterministic subset using a fixed seed and per-class counts.
- Output files are `iris_train.csv` and `iris_test.csv` under the requested output directory.
- Use `--label-position last` for the canonical dense CSV layout, or `--label-position first` when you want the legacy repository ordering.

## DICOM caveat

- `convert_dcm_to_csv.py` is reference-only in this skill.
- The source workflow depends on `pydicom`.
- The source workflow also requires an external labels file named `raw_data/stage1_labels.csv`.
- That labels file is not present in this checkout, so do not describe DICOM conversion as a runnable helper here.
