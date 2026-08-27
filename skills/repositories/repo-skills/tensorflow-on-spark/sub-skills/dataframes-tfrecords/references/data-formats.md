# Data formats

This sub-skill focuses on flat DataFrames that can be expressed as `tf.train.Example` features.

## Canonical Spark ↔ TFRecord mapping

| Spark SQL dtype | TFExample feature | Recovered type | Notes |
|---|---|---|---|
| `float`, `double` | `FloatList` | `DoubleType` | Scalars stay scalar. |
| `boolean`, `tinyint`, `smallint`, `int`, `bigint`, `long` | `Int64List` | `LongType` | Boolean values are stored as integer scalars. |
| `binary`, `string` | `BytesList` | `BinaryType` or `StringType` | `binary_features` decides whether the bytes stay raw or decode as UTF-8 text. |
| `array<float>`, `array<double>` | `FloatList` | `ArrayType(DoubleType)` | Multi-value numeric features become arrays. |
| `array<boolean>`, `array<tinyint>`, `array<smallint>`, `array<int>`, `array<bigint>`, `array<long>` | `Int64List` | `ArrayType(LongType)` | Use only primitive arrays. |

## What is not supported

The conversion helpers are intentionally narrow. Treat the following as out of scope unless you pre-normalize them into supported columns:

- `struct<...>` and nested structs
- maps, arrays of structs, or other nested collections
- decimals, timestamps, dates, and other richer Spark SQL types
- variable schema records where feature names or types change from one row to the next

## Binary vs string ambiguity

TensorFlow stores both textual and binary payloads as `BytesList`. That means the loader cannot tell whether a field should become a Spark `StringType` or `BinaryType` unless you give it a hint.

Use the same feature name list in all of these places:

- `infer_schema(example, binary_features=[...])`
- `fromTFExample(records, binary_features=[...])`
- `loadTFRecords(sc, input_dir, binary_features=[...])`

If you omit the hint, the field is treated as UTF-8 text.

## MNIST row shapes

The MNIST example utilities use two related shapes:

- Raw CSV row: `label,p0,p1,...,p783`
- SavedModel input literal: `[28, 28, 1]`

The row shaping helper converts one CSV line into the nested list form expected by saved-model style input expressions.

## Schema inference behavior

A few details matter when you load TFRecords back into Spark:

- Schema inference reads the first serialized example and assumes later records match it.
- Field names are sorted before schema construction and before row reconstruction.
- Empty repeated fields are treated as null-like values on the way back to Python.

## Practical rule

If you can express a column as a primitive scalar, a primitive array, a UTF-8 string, or raw bytes, it fits this sub-skill. Otherwise, flatten or encode it before calling `saveAsTFRecords`.
