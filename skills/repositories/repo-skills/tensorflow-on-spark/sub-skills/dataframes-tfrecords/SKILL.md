---
name: dataframes-tfrecords
description: "Route Spark DataFrame to/from TFRecord conversion, schema
  inference, and MNIST row-shaping requests."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DataFrames and TFRecords

Use this sub-skill when the request is about:
- `dfutil.saveAsTFRecords`
- `dfutil.loadTFRecords`
- `dfutil.toTFExample`
- `dfutil.infer_schema`
- `dfutil.fromTFExample`
- `binary_features`
- TFRecord Hadoop classpath setup for Spark DataFrames
- the small MNIST CSV row reshaping helper

## What it covers

- Flat Spark DataFrame ↔ `tf.train.Example` conversion
- Spark SQL type mappings for scalars, primitive arrays, strings, and raw bytes
- The TensorFlow Hadoop `TFRecordFileInputFormat` / `TFRecordFileOutputFormat` dependency
- Small MNIST row formatting for `saved_model_cli` or serving-style input examples

## Route elsewhere

Do not use this sub-skill for:
- TensorFlowOnSpark training or inference data feeds
- Spark ML pipeline modeling or estimator workflows
- full MNIST downloads or training recipes

## Start here

1. Read [API reference](references/api-reference.md) for function contracts and signatures.
2. Read [data formats](references/data-formats.md) for supported Spark/TFExample mappings.
3. Read [troubleshooting](references/troubleshooting.md) when classpath, bytes, or dtype errors appear.
4. Run [schema probe](scripts/tfos_tfrecord_schema_probe.py) for a tiny local smoke test.
5. Use [MNIST reshape helper](scripts/mnist_reshape.py) when a single CSV row must become a `[28, 28, 1]` literal.

## Expected signals

- `saveAsTFRecords` writes TFRecord files through the TensorFlow Hadoop output format.
- `loadTFRecords` reconstructs a DataFrame schema from the first serialized example.
- `binary_features` must be supplied whenever a `BytesList` should remain raw bytes instead of UTF-8 text.
- Unsupported Spark dtypes should be normalized before conversion.
- Missing TensorFlow Hadoop classes should be fixed on the Spark classpath before retrying.

## Boundaries

If the user needs model training, inference, or full example conversion, keep the request outside this sub-skill and hand it to the appropriate higher-level sub-skill.
