# Data Formats

Read this when a task needs to validate or transform Tencent ML-Images data
files before training, finetuning, classification, or feature extraction.

## URL-list rows

The URL-list format shown by the project stores one image URL followed by one or
more label tokens separated by tabs:

```text
https://host/path/image.jpg\t4097:1\t4089:1\t4063:1
```

Rules:

- Column 1 is a URL.
- Remaining columns are labels. A label token may be `class_id:confidence` or
  just `class_id`.
- `class_id` is zero-based. For ML-Images the canonical class count is `11166`.
- `confidence` is a float, commonly `1`, `1.0`, `0.9`, or `0.8` in examples.
- The downloader derives a local image name from the final URL path pieces and
  writes a local image-list row using that name plus the same label tokens.

Use `scripts/validate_ml_images_lists.py --url-list <file> --num-classes 11166`
when a URL-list file looks suspicious.

## Local image-list rows

The local image list used by the TFRecord converter stores a relative image path
or image filename followed by label tokens:

```text
1557324960_1ae893fed8_o.jpg\t4097:1\t4089:1\t4063:1
```

The bundled validator accepts either tab-separated or whitespace-separated rows.
For a multi-label ML-Images TFRecord, labels are converted into a dense
`float32[num_classes]` vector. For an ImageNet-style single-label TFRecord, the
converter may store a scalar integer class id instead.

## Image-list shards

The TFRecord workflow expects a directory of list shards. Each file contains
local image-list rows. The converter writes one `.tfrecords` output shard per
input list file. The original tiny example uses two list shards with 50 rows
each, producing two TFRecord files.

Recommended pattern for future agents:

1. Put list shards under a clean directory such as `image_lists/`.
2. Put images under a separate directory such as `images/`.
3. Run validation with `--images-root` before converting.
4. Write TFRecords to a fresh directory and pass that directory to the training
   workflow as the `train` or `val` split.

## TFRecord feature schema

The repository's converters and readers use these serialized features:

| Feature | Type | Meaning |
|---|---|---|
| `width` | `int64` scalar | Decoded image width |
| `height` | `int64` scalar | Decoded image height |
| `image` | `bytes` scalar | JPEG image bytes; PNG inputs are converted to JPEG by the converter |
| `label` | `bytes` scalar for multi-label or `int64` scalar for single-label | Dense `float32` vector bytes for ML-Images multi-label training, or class id for ImageNet finetuning |
| `name` | `bytes` scalar | Image filename or relative path from the image list |

Training consumes multi-label records by decoding `label` as `float32` and
reshaping to `[class_num]`. Finetuning consumes single-label records by reading
`label` as `int64` and applying one-hot encoding to `class_num` classes.

## Dictionaries and semantic hierarchy

Two dictionary-like files appear in the project evidence:

- The ImageNet classification dictionary maps a zero-based integer id to one or
  more tab-separated name tokens. Example shape:

  ```text
  0\ttench\tTinca\ttinca
  1\tgoldfish\tCarassius\tauratus
  ```

  The classification script expects the first field as the string id and the
  second field as the displayed label name.

- The ML-Images semantic hierarchy file starts with a header and stores:

  ```text
  category_index\tcategory_id\tindex_of_parent_category\tcategory name
  0\tn00002452\t-1\tthing
  ```

  `index_of_parent_category == -1` denotes one of the hierarchy roots. The
  README describes four roots and 11,166 total categories.

## Class-count decisions

- Use `11166` for ML-Images multi-label pretraining.
- Use `1000` for ImageNet single-label classification or finetuning with the
  provided ImageNet dictionary/checkpoint path.
- If `top_k` or label ids exceed the dictionary/class count, stop and fix the
  dictionary, checkpoint, or class-count flags before running inference or
  training.
