# Workflows

## 1) Convert dense CSV to TFRecords

Use this when the input is a comma-separated dense table.

```bash
python scripts/convert_csv_to_tfrecords.py \
  --input data/cancer/cancer_train.csv \
  --output /tmp/cancer_train.tfrecords \
  --label-position last \
  --label-type int
```

For legacy label-first CSVs:

```bash
python scripts/convert_csv_to_tfrecords.py \
  --input /tmp/legacy.csv \
  --output /tmp/legacy.tfrecords \
  --label-position first \
  --label-type float
```

## 2) Convert sparse LIBSVM to TFRecords

Use this when the input is `label id:value id:value ...`.

```bash
python scripts/convert_libsvm_to_tfrecords.py \
  --input data/a8a/a8a_train.libsvm \
  --output /tmp/a8a_train.tfrecords \
  --label-type int
```

## 3) Inspect a dense TFRecord

Inspect the generated file before handing it to training.

```bash
python scripts/inspect_tfrecords.py \
  --input /tmp/cancer_train.tfrecords \
  --schema dense \
  --feature-size 9 \
  --max-records 3
```

If the file is actually sparse, this command should fail with a schema mismatch instead of printing blank feature fields.

## 4) Inspect a sparse TFRecord

```bash
python scripts/inspect_tfrecords.py \
  --input /tmp/a8a_train.tfrecords \
  --schema sparse \
  --feature-size 124 \
  --max-records 3
```

## 5) Create a tiny iris fixture

Generate a small, deterministic CSV pair from the local sklearn dataset.

```bash
python scripts/create_iris_csv_fixture.py \
  --output-dir /tmp/iris-fixture \
  --seed 13 \
  --train-per-class 2 \
  --test-per-class 1
```

Then convert the generated files with the dense CSV helper:

```bash
python scripts/convert_csv_to_tfrecords.py \
  --input /tmp/iris-fixture/iris_train.csv \
  --output /tmp/iris-fixture/iris_train.tfrecords \
  --label-position last \
  --label-type int
```

## 6) DICOM questions

If a user asks about DICOM conversion, answer with the caveat first:

- the source script depends on `pydicom`
- the source script also needs `raw_data/stage1_labels.csv`
- that labels file is absent here, so the path is reference-only unless the caller provides external labels

Do not present DICOM conversion as a bundled runnable helper in this sub-skill.
