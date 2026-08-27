# Feature and Format Troubleshooting

Use this when `Features` inference, casting, label encoding, JSON loading, or media decoding fails. For download/auth/path mechanics, route to `../../loading-local-hub/SKILL.md`; for transforms and framework formatting, route to `../../processing-streaming/SKILL.md`.

## First Checks

1. Print `ds.features` and compare every key with the expected columns.
2. Inspect a tiny sample before running expensive transforms: `ds.select(range(min(3, len(ds))))` for map-style datasets or `next(iter(ds))` for iterable datasets.
3. For media columns, recast with `decode=False` to separate path/bytes problems from decoder dependency problems.
4. For file loaders, pass an explicit builder name and explicit `features=` if extension-based inference is ambiguous.
5. Validate a representative nested example with `../scripts/feature_schema_smoke.py` before loading a large corpus.

## Dtype Mismatches

Symptoms include Arrow cast errors, integer overflow, failed conversion from string to number, or columns inferred as `string` when numeric values were expected.

Fixes:

- Choose exact `Value` dtypes and pass `features=` at load time when reading files.
- Normalize source strings such as `""`, `"NA"`, or mixed numeric/text values before casting to numbers.
- Use `float64` or `int64` if source values exceed narrower dtypes.
- For arrays, check rank and shape before choosing `Array2D`-`Array5D`; ragged values usually need `List`.
- If only one column is wrong, use `cast_column`; if several columns changed, use `cast` with a full `Features` object.

## Nullability and Mixed JSON

Symptoms include inconsistent inferred schemas, null-only columns becoming the wrong type, or JSON loader failures when one row has an object and another row has a scalar/list.

Fixes:

- Provide explicit `features=Features(...)` so nulls do not drive inference.
- Use `Json()` for intentionally flexible payloads.
- Rewrite mixed-type JSON columns into a stable shape before loading when downstream code expects a schema.
- For nested top-level JSON, use the loader's `field=` option to select the intended records before feature inference.
- Keep chat/message/tool-call schemas as `List({...})` when every element has a stable record shape; use `List(Json())` only for truly variable payloads.

## ClassLabel Encoding

Symptoms include unknown label strings, labels shifted after reordering, integer labels out of range, or folder labels not matching expected class names.

Fixes:

- Define `ClassLabel(names=[...])` explicitly in stable order.
- Normalize whitespace/case in label strings before loading or casting.
- Convert strings with `str2int` and integers with `int2str` rather than hard-coding assumptions in transforms.
- Check inferred folder names when using media folder builders; directory names become class names when metadata does not override labels.
- Do not reorder class names after model training or after publishing a dataset used by consumers.

## Sequence vs List Surprises

Symptoms include a list of objects appearing as a dict of lists, or annotation records failing validation despite matching field names.

Fixes:

- Use `List({"field": ...})` for a true list of record objects.
- Use `Sequence({"field": ...})` only when you want TFDS-compatible parallel lists.
- For object detection, validate that each annotation has synchronized `bbox` and `category` lengths or a true list of records, depending on your chosen schema.
- Use fixed `List(feature, length=n)` for bounding boxes that must always have four coordinates.

## Decoding Disabled or Decoder Missing

Symptoms include `RuntimeError: Decoding is disabled for this feature`, `ImportError` for optional libraries, or failures when accessing a row rather than when loading.

Fixes:

- If the task only needs paths/bytes, keep `decode=False` and do not call decoder-specific APIs.
- If decoded objects are required, install the relevant optional dependency in the target environment: `torchcodec` and `torch` for audio/video, Pillow for images, `pdfplumber` for PDFs, `nibabel` for NIfTI, and `trimesh` for meshes.
- Recast the column from `Feature(decode=False)` to `Feature(decode=True)` after dependencies are available.
- For audio, set `sampling_rate`, `num_channels`, or `stream_index` only when the decoder environment supports the desired conversion.
- For video, check `dimension_order`, `num_ffmpeg_threads`, `device`, and `seek_mode` if frame access behaves unexpectedly.

## Media Path, Bytes, and Archive Shape

Symptoms include missing files, metadata rows not matching media files, archive members not found, or folder builders creating unexpected labels/splits.

Fixes:

- Confirm whether examples store `path`, `bytes`, or both.
- For archives, metadata paths must match archive-internal paths.
- For folder builders, verify that metadata file names and media file-name columns match builder expectations.
- If labels appear unexpectedly, check whether parent directory names were interpreted as class labels.
- Use `decode=False` to inspect the stored path/bytes without invoking a decoder.
- Route split hierarchy, glob patterns, and archive loading details to `../../loading-local-hub/SKILL.md`.

## Format Inference Problems

Symptoms include the wrong packaged module being selected, unexpected column names, or a builder refusing a file with a nonstandard extension.

Fixes:

- Call `load_dataset` with an explicit builder name such as `"csv"`, `"json"`, `"parquet"`, `"imagefolder"`, or `"audiofolder"`.
- Pass `data_files` explicitly, especially for mixed directories.
- For CSV/TSV, specify delimiter/encoding options rather than relying on defaults.
- For JSON, distinguish JSON lines from a single JSON object/array and use `field=` when needed.
- For HDF5/table formats, inspect inferred array/list/nested features and override with `features=` when the source has ambiguous or variable shapes.

## Object-Detection and Messages Schemas

Difficult nested schemas are easiest to debug with tiny examples.

Object detection pattern:

```python
from datasets import Features, Image, List, Value, ClassLabel

features = Features({
    "image": Image(decode=False),
    "objects": List({
        "bbox": List(Value("float32"), length=4),
        "category": ClassLabel(names=["cat", "dog"]),
    }),
})
```

Messages pattern:

```python
from datasets import Features, List, Value, Json

features = Features({
    "messages": List({
        "role": Value("string"),
        "content": Value("string"),
        "tool_calls": List(Json()),
    })
})
```

Run the bundled helper with `--case object-detection --bad-example` or `--case messages --bad-example` to see common mismatches caught before using a real dataset.
