# API reference

The signatures and behaviors below were verified from the installed `tensorflowonspark.dfutil` module and cross-checked against repository tests and example workflows.

## Core functions

| Function | Signature | Role | Inputs | Output | Key notes |
|---|---|---|---|---|---|
| `saveAsTFRecords` | `(df, output_dir)` | Convert a Spark DataFrame into TFRecord files. | Flat DataFrame rows plus an output directory. | TFRecord files written with the TensorFlow Hadoop output format. | Uses `df.rdd.mapPartitions(toTFExample(df.dtypes))` and `saveAsNewAPIHadoopFile`. Requires the TensorFlow Hadoop output format class on the Spark classpath. |
| `loadTFRecords` | `(sc, input_dir, binary_features=[])` | Load TFRecords from disk into a Spark DataFrame. | SparkContext, TFRecord directory, and optional binary feature names. | DataFrame reconstructed from the first serialized example. | Reads with `TFRecordFileInputFormat`, infers schema from the first record, and then applies `fromTFExample`. Fails early on empty input because it probes the first record. |
| `toTFExample` | `(dtypes)` | Build a partition mapper that serializes rows to `tf.train.Example`. | Spark `DataFrame.dtypes` pairs. | A function that accepts an iterator of rows and returns serialized examples. | Supported Spark dtypes are mapped into FloatList, Int64List, or BytesList. Unsupported dtypes raise `Unsupported dtype: ...`. |
| `infer_schema` | `(example, binary_features=[])` | Infer a Spark schema from one `tf.train.Example`. | A parsed `tf.train.Example` and optional binary feature names. | `StructType`. | `BytesList` is ambiguous; `binary_features` forces `BinaryType` instead of `StringType`. Multi-value features become `ArrayType`. |
| `fromTFExample` | `(iter, binary_features=[])` | Build Spark rows from serialized examples. | Partition iterator of `(bytes, None)` records and optional binary feature names. | Iterable of `Row` objects. | Bytes decode as UTF-8 strings unless the feature name is listed in `binary_features`, in which case the value remains raw bytes. |

## Supported type families

The module converts only flat or primitive-array columns. Use `references/data-formats.md` for the complete mapping table.

## MNIST row shaping helper

The MNIST example utilities use a simple row format:

- CSV input: `label,pixel0,pixel1,...,pixel783`
- SavedModel input shape: `[28, 28, 1]`
- Helper output: a single Python list literal suitable for `saved_model_cli` or similar input-expression workflows

Use [MNIST reshape helper](../scripts/mnist_reshape.py) for that conversion.

## Tiny smoke probe

Use [schema probe](../scripts/tfos_tfrecord_schema_probe.py) to verify:

- supported dtype round-trip
- binary/string ambiguity handling
- unsupported dtype failure mode
- optional Spark TFRecord classpath round-trip
