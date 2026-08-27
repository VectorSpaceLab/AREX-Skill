# Schema and Feature Design

This reference is for constructing, validating, and changing `datasets.Features` schemas. It is intentionally focused on feature semantics; use `../../loading-local-hub/SKILL.md` for `load_dataset` source routing and `../../processing-streaming/SKILL.md` for transforms after a dataset exists.

## Core Schema Types

| Need | Feature choice | Notes |
| --- | --- | --- |
| Scalar text, integer, float, bool, timestamp-like Arrow dtype | `Value(dtype)` | Use exact Arrow-compatible dtypes such as `"string"`, `"int32"`, `"int64"`, `"float32"`, `"float64"`, `"bool"`, or date/time dtypes supported by the installed package. |
| Closed set of labels | `ClassLabel(names=[...])` or `ClassLabel(num_classes=n)` | Stores labels as integers. Prefer `names` for stable model/card semantics; use `str2int` and `int2str` for conversion. |
| Variable-length list | `List(feature)` | Best default for arrays of tokens, spans, bounding boxes, message lists, and other repeated values. |
| Fixed-length list | `List(feature, length=n)` | Use when every row must have exactly `n` elements. |
| TFDS-style dict-of-lists compatibility | `Sequence({...})` | A `Sequence` of a dict may be converted to a dict of parallel lists for compatibility. If you need a true list of objects, prefer `List({...})`. |
| Very large list offsets | `LargeList(feature)` | Use when an individual list column may exceed regular Arrow list offset limits. |
| Dense 2D-5D arrays | `Array2D` through `Array5D` | Use fixed rank and dtype. Shape entries can be `None` for variable dimensions where supported. |
| JSON object with flexible keys or mixed nested values | `Json()` | Use when object keys vary too much for a precise `Features` dict. Decode behavior can be disabled with `Json(decode=False)`. |
| Machine translation | `Translation(languages=[...])` or `TranslationVariableLanguages(languages=[...])` | Use fixed languages for parallel pairs; variable languages when each example may contain a different subset. |
| Nested records | Plain nested dict or nested `Features` | Each leaf still needs a feature type. Use this for structured annotations and metadata. |

## Construct Explicit Features

Prefer explicit `Features` when source files include nulls, mixed JSON values, class labels, media paths, nested annotations, or array columns whose intended dtype/shape is not obvious.

```python
from datasets import Features, Value, ClassLabel, List, Array2D

features = Features({
    "id": Value("string"),
    "label": ClassLabel(names=["cat", "dog"]),
    "tokens": List(Value("string")),
    "embedding": Array2D(shape=(None, 768), dtype="float32"),
    "objects": List({
        "bbox": List(Value("float32"), length=4),
        "category": ClassLabel(names=["person", "vehicle", "animal"]),
    }),
})
```

Schema keys must match dataset columns unless you intentionally select/filter columns during loading. When loading a file format with `features=...`, mismatched or extra feature keys usually indicate that the file columns, metadata file, or selected columns are not aligned.

## Cast and Cast Column

Use `cast` when replacing the full feature schema of an existing dataset:

```python
from datasets import Features, Value

ds = ds.cast(Features({"text": Value("string"), "score": Value("float32")}))
```

Use `cast_column(column, feature)` for a single column:

```python
from datasets import Image

ds = ds.cast_column("image", Image(mode="RGB", decode=False))
```

Casting changes the declared Arrow schema and may convert values. It does not fix invalid data. If a value cannot be converted to the requested dtype, repair or normalize the source data first with a transform or by rewriting the source files.

## ClassLabel Rules

`ClassLabel(num_classes=None, names=None, names_file=None)` accepts exactly one of `names`, `names_file`, or enough information to define the class count. Prefer `names=[...]` inside public examples because `names_file` points to a file and is less portable.

```python
label = ds.features["label"]
label_id = label.str2int("positive")
label_name = label.int2str(label_id)
```

Common checks:

- Label strings in data must exactly match `names`, including case and whitespace.
- Integer labels must be in range `0 <= label < num_classes`.
- Do not reorder `names` after training a model, because stored integers will map to different strings.
- Folder-based builders infer `ClassLabel` names from directory names when no metadata overrides labels.

## List, Sequence, and Nested Objects

Use `List({...})` for object-detection annotations, chat messages, tool calls, token spans, and other examples where each row contains a list of records.

```python
features = Features({
    "messages": List({
        "role": Value("string"),
        "content": Value("string"),
        "tool_calls": List(Json()),
    })
})
```

Use `Sequence({...})` only when the desired storage follows the older TensorFlow Datasets convention that turns a sequence of records into parallel lists. For example, `Sequence({"text": Value("string"), "start": Value("int32")})` behaves differently from `List({"text": Value("string"), "start": Value("int32")})`. If examples fail because a list of objects appears as a dict of lists, switch between `Sequence` and `List` intentionally rather than treating them as aliases.

## Array Features

`Array2D`, `Array3D`, `Array4D`, and `Array5D` are for dense fixed-rank numeric arrays. They are useful for matrices, tensors, embeddings, image-like arrays, medical volumes, and scientific data. Choose `List(Value(...))` for ragged nested lists unless the array rank and shape are semantically important.

```python
from datasets import Array3D

features = Features({"volume": Array3D(shape=(None, 128, 128), dtype="float32")})
```

If an HDF5 or other table-like file infers `Array2D`/`Array3D` but a later file has a different shape, either normalize file shapes or choose a less strict list schema.

## JSON Feature

Use `Json()` for arbitrary structured values when keys or nested shapes vary by row. It is useful for agent traces, flexible metadata, and mixed tool-call payloads. If a downstream model or transform needs a stable schema, prefer a precise nested `Features` object instead.

Typical JSON trade-offs:

- Precise nested `Features` catches shape and dtype errors early.
- `Json()` tolerates varying objects but shifts validation to your application code.
- Mixed scalar/object/list values in one column often require `Json()` or source normalization before loading.
- Null-only columns can infer poorly; provide explicit `features` if a later non-null value has an intended type.

## Media and File Features

Path or bytes columns can be cast to `Audio`, `Image`, `Video`, `Pdf`, `Nifti`, or `Mesh`. The encoded storage is usually a struct with `path` and `bytes`; access returns decoded objects when `decode=True` and optional dependencies are installed. Use `decode=False` to keep path/bytes available without importing decoders.

See `format-loaders.md` for constructor arguments and optional extras.

## Validation Workflow

1. Print `ds.features` immediately after loading or casting.
2. Inspect one or two raw examples with `decode=False` for media columns if dependency or path problems are suspected.
3. For nested schemas, validate representative examples before loading a large corpus.
4. Use the bundled smoke script for local example validation: `python ../scripts/feature_schema_smoke.py --case object-detection`.
5. Keep schema examples portable: do not rely on absolute paths, private label files, or machine-specific files.
