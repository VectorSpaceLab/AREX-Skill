# Feature connector reference

Feature connectors define the structure users receive from `builder.as_dataset()` or `tfds.load()`, and they encode raw examples from `_generate_examples` into the serialized dataset representation.

## Core pattern

Declare a nested `tfds.features.FeaturesDict` in `_info`:

```python
return self.dataset_info_from_configs(
    features=tfds.features.FeaturesDict({
        "image": tfds.features.Image(shape=(28, 28, 1), doc="Input image."),
        "label": tfds.features.ClassLabel(names=["zero", "one"]),
        "metadata": {
            "id": tfds.features.Text(),
            "source": tfds.features.Text(),
        },
    }),
    supervised_keys=("image", "label"),
)
```

Then yield examples with the same nested keys:

```python
yield example_id, {
    "image": image_path,
    "label": "zero",
    "metadata": {"id": example_id, "source": "provider-a"},
}
```

## Installed connector signatures

The inspected package exposes these common constructors:

```text
tfds.features.FeaturesDict(feature_dict, *, doc=None)
tfds.features.Image(*, shape=None, dtype=None, encoding_format=None, use_colormap=False, doc=None)
tfds.features.ClassLabel(*, num_classes=None, names=None, names_file=None, doc=None)
tfds.features.Text(encoder=None, encoder_config=None, *, doc=None, optional=False)
tfds.features.Tensor(*, shape, dtype, encoding='none', doc=None, serialized_dtype=None, serialized_shape=None, minimum=None, maximum=None, optional=False)
tfds.features.Scalar(dtype, *, doc=None, optional=False)
tfds.features.Sequence(feature, length=None, *, doc=None)
tfds.features.Audio(*, file_format=None, shape=(None,), dtype=np.int64, sample_rate=None, encoding='none', doc=None, lazy_decode=False)
tfds.features.Video(shape=None, encoding_format='png', ffmpeg_extra_args=(), use_colormap=False, dtype=np.uint8, doc=None)
tfds.features.BBox(ymin, xmin, ymax, xmax)
tfds.features.BBoxFeature(*, doc=None, bbox_format='REL_YXYX')
tfds.features.Translation(languages, encoder=None, encoder_config=None, *, doc=None)
tfds.features.TranslationVariableLanguages(languages=None, *, doc=None)
```

Use the most specific connector that matches the data. Specific connectors expose metadata and allow better visualization/validation than a generic tensor.

## Choosing connectors

| Data type | Prefer | Notes |
|---|---|---|
| Class/category labels | `ClassLabel(names=[...])` or `ClassLabel(names_file=...)` | Prefer human-readable names over `num_classes`; labels can then be yielded as strings. |
| Fixed-shape image | `Image(shape=(height, width, channels))` | Set shape when known. Unknown image shapes make batching harder. |
| Variable-shape image | `Image(shape=(None, None, channels))` | Use only when dimensions truly vary; document preprocessing expectations. |
| Text strings | `Text()` or plain string dtype inside a feature dict | Use `Text` when TFDS text feature behavior is desired. |
| Scalars | `Scalar(dtype)` or dtype shorthand | Use `Scalar` when documentation or optionality matters. |
| Dense numeric arrays | `Tensor(shape=..., dtype=...)` | Specify exact shape and dtype. Use `minimum`/`maximum` for useful validation metadata. |
| Sequences/lists | `Sequence(feature, length=None)` | Use fixed `length` only when every example has the same length. |
| Audio | `Audio(sample_rate=..., shape=..., dtype=...)` | Declare sample rate when known. Be careful with optional audio dependencies. |
| Video | `Video(shape=(frames, height, width, channels))` | Video generation may require media dependencies; keep dummy data small. |
| Bounding boxes | `BBoxFeature()` plus label fields | Use normalized coordinates matching the chosen format. |
| Multilingual translation | `Translation([...])` or `TranslationVariableLanguages` | Make language keys explicit and stable. |

## Documentation on features

Every connector accepts either a simple string doc or a richer documentation object where supported. Add docs for ambiguous fields:

```python
"timestamp": tfds.features.Scalar(
    tf.int64,
    doc="Seconds since Unix epoch in the source metadata.",
)
```

Good feature docs explain units, value ranges, normalization, optionality, and class semantics. They do not restate the key name.

## Encoding expectations in `_generate_examples`

Feature connectors convert raw yielded values into serialized data. Common accepted values:

- `Image`: path-like objects, arrays, bytes, or file objects depending on encoding.
- `ClassLabel`: integer IDs or label strings when names are provided.
- `Text`: Python strings.
- `Tensor`/`Scalar`: NumPy arrays, Python numbers, or tensor-like values matching shape and dtype.
- `Sequence`: lists or nested structures with lengths compatible with the declared connector.

Checklist:

- The yielded example keys must exactly match `FeaturesDict` keys.
- Nested dictionaries must preserve the same nesting as `_info`.
- Dtypes should be stable and not depend on platform defaults when this matters.
- If a connector expects paths, use path-like objects returned by the download manager or `pathlib`/`epath` style operations; do not hard-code local absolute paths.
- If a field is optional, use connector support for optionality when available rather than omitting keys unpredictably.

## Class labels

Prefer:

```python
"label": tfds.features.ClassLabel(names=["negative", "positive"])
```

Avoid when names are known:

```python
"label": tfds.features.ClassLabel(num_classes=2)
```

Why names matter:

- `_generate_examples` can yield label strings directly.
- Users can inspect `info.features["label"].names`.
- Helpers can display meaningful class names.
- Conversion helpers such as `str2int` become available.

If a dataset's label list is long or maintained separately, use `names_file` and ensure that file is packaged with the dataset folder.

## Images, video, and shapes

Static shapes should be explicit:

```python
"image": tfds.features.Image(shape=(224, 224, 3))
```

Use unknown dimensions only when they genuinely vary:

```python
"image": tfds.features.Image(shape=(None, None, 3))
```

Gotchas:

- Unknown shape images often cannot be batched without resizing.
- Use channel counts consistently. If data can be grayscale or RGB, normalize it or document the distinction.
- For video, tiny dummy clips are enough for tests. Do not require real large videos in dummy data.
- For audio, declare sample rate when the source defines it.

## Nested and sequence features

Use dictionaries for structured metadata and `Sequence` for variable-length repeated items:

```python
features = tfds.features.FeaturesDict({
    "tokens": tfds.features.Sequence(tfds.features.Text()),
    "boxes": tfds.features.Sequence({
        "bbox": tfds.features.BBoxFeature(),
        "label": tfds.features.ClassLabel(names=["person", "car"]),
    }),
})
```

Example records must preserve the same nesting:

```python
yield key, {
    "tokens": ["a", "small", "cat"],
    "boxes": [
        {"bbox": tfds.features.BBox(0.1, 0.2, 0.4, 0.5), "label": "person"},
    ],
}
```

## Custom connectors

Only create a custom connector when built-in connectors cannot represent the user-visible structure or encoding behavior.

A custom connector should implement or inherit support for:

- `encode_example(data)`: convert raw generator values to serialized-compatible content.
- `decode_example(data)`: convert serialized tensors to user-facing tensors or nested values.
- `get_tensor_info()`: report output shape and dtype.
- `get_serialized_info()` when serialized layout differs from decoded layout.
- `to_json_content` and `from_json_content` so prepared datasets can be loaded without original source code.
- Metadata save/load behavior if the connector depends on side files.

Prefer extending `Tensor` for a single tensor and `FeaturesDict` for a nested container.

## Testing feature connectors

Use `tfds.testing.FeatureExpectationItem` with feature test helpers when adding custom connectors or when connector behavior is non-obvious.

A feature test should cover:

- `encode_example` success and failure cases.
- Decoded dtype and shape.
- NumPy/eager behavior when relevant.
- Round-trip from saved config/proto if the connector must work after packaging.
- Decoder overrides when the connector supports custom decoding.

For ordinary dataset builders, `DatasetBuilderTestCase` also validates that `builder.info.features.get_tensor_info()` matches the element spec produced by the generated dummy dataset.

## Quick review checklist

- Features match every key yielded by `_generate_examples`.
- Label names are human-readable and complete.
- Known shapes are explicit.
- Numeric dtypes are deliberate.
- Optional or missing fields are represented consistently.
- Dummy examples exercise each feature branch, not only the easiest happy path.
- Custom connectors round-trip through metadata/config without needing the source checkout.
