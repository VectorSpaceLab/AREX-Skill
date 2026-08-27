# Schema and Codecs

## Purpose

Read this when a task needs to define a dataset schema, validate a row, change field shapes, or decode/encode image or ndarray columns.

## Core concepts

- `Unischema` describes the field order, names, shapes, nullability, and codecs for a dataset.
- `UnischemaField` carries `name`, `numpy_dtype`, `shape`, `codec`, and `nullable`.
- `dict_to_spark_row()` validates a dictionary against a `Unischema` before it becomes a Spark row.
- `TransformSpec` mutates the schema and/or rows after they are read.

## Codec summary

| Codec | Purpose | Notes |
| --- | --- | --- |
| `ScalarCodec` | Stores scalar values in a Spark scalar column | Maps NumPy scalars to Spark types |
| `NdarrayCodec` | Stores a NumPy array as binary data | Uses `.npy` encoding |
| `CompressedNdarrayCodec` | Stores a compressed NumPy array | Uses `.npz` encoding |
| `CompressedImageCodec` | Stores an image array as compressed bytes | Requires OpenCV |

## Shape and nullability rules

- `()` means a scalar field.
- `None` in a shape tuple means that dimension is variable length.
- Non-scalar fields need a codec.
- `nullable=False` fields must be present and non-null when rows are written.
- `nullable=True` fields can be filled in later with `insert_explicit_nulls()`.

## Useful schema helpers

- `Unischema.create_schema_view()` selects a subset of fields using exact fields or regex patterns.
- `match_unischema_fields()` resolves regex filters into concrete fields.
- `edit_field()` is a convenience helper for `TransformSpec.edit_fields`.
- `insert_explicit_nulls()` makes missing nullable fields explicit before row validation.

## Public behaviors worth remembering

- The schema field order is significant and preserved by the namedtuple conversion.
- `as_spark_schema()` derives a Spark `StructType` from the schema.
- `make_namedtuple()` and `make_namedtuple_tf()` return schema-shaped records for Python and TensorFlow use.

## Practical example

```python
import numpy as np
from pyspark.sql.types import IntegerType
from petastorm.codecs import ScalarCodec, NdarrayCodec
from petastorm.unischema import Unischema, UnischemaField

ExampleSchema = Unischema("ExampleSchema", [
    UnischemaField("id", np.int32, (), ScalarCodec(IntegerType()), False),
    UnischemaField("vector", np.float32, (4,), NdarrayCodec(), False),
])
```

Use the create-datasets sub-skill when you need to turn a schema into an actual dataset.
