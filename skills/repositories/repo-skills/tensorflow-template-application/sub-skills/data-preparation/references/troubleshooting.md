# Troubleshooting

## Dense CSV and TFExample shape mismatches

**Symptom**

- Training reports a `FixedLenFeature` or shape error.
- The inspector shows the wrong number of values in `features`.

**Likely cause**

- The CSV row does not match the expected dense feature count.
- The caller used the wrong label position.
- The wrong TFRecord schema was chosen for inspection.

**What to check**

- Confirm whether the CSV is label-last or label-first.
- Re-run the converter with the matching `--label-position`.
- Re-run `inspect_tfrecords.py --schema dense` and confirm the `features` length.
- If `--feature-size` is provided to the inspector, make sure it matches the downstream model.

## Dense vs sparse schema confusion

**Symptom**

- A sparse file is inspected with the dense schema.
- The bundled inspector should report a schema mismatch instead of showing empty fields.

**Likely cause**

- The TFRecord contains `ids` and `values`, not `features`.

**What to check**

- Use `--schema sparse` for LIBSVM-derived files.
- Use `--schema dense` for CSV-derived files.
- Expect dense examples to expose `features` and sparse examples to expose `ids` and `values`.

## Label type and column order mistakes

**Symptom**

- The label looks shifted into the feature vector.
- Classification labels appear as floats when the caller expected ints.
- Regression labels are being forced into integer storage.

**Likely cause**

- The label column order was chosen incorrectly.
- The label type flag was chosen incorrectly.

**What to check**

- For dense CSV, set `--label-position last` for canonical dense rows.
- Use `--label-position first` only when reproducing legacy repo CSV layout.
- Use `--label-type int` for classification labels.
- Use `--label-type float` for regression labels.

## Sparse LIBSVM parse errors

**Symptom**

- The sparse converter fails on an input row.
- The inspector shows mismatched ids and values.

**Likely cause**

- A token is not in `id:value` form.
- A row contains a malformed value.
- A comment or header row was passed to the converter.

**What to check**

- Remove headers and non-data rows before conversion.
- Confirm every feature token contains exactly one `:` separator.
- Confirm the ids and values lists stay aligned.

## DICOM conversion failure

**Symptom**

- A user asks for DICOM conversion and the workflow cannot be made runnable.

**Likely cause**

- The source path depends on `pydicom`.
- The source path also needs `raw_data/stage1_labels.csv`.
- That labels file is not present in this checkout.

**What to check**

- Explain that DICOM is reference-only in this sub-skill.
- Ask the caller to provide the missing labels file if they want to reuse the source script outside this skill.
