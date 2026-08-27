# Training data pipeline

## SQLite selection contract

The loader opens the file named by `project.json`'s `database_path` and runs the
equivalent of:

```sql
SELECT md5, file_ext, tag_string
FROM posts
WHERE (file_ext = 'png' OR file_ext = 'jpg' OR file_ext = 'jpeg')
  AND tag_count_general >= ?
ORDER BY id;
```

The bound value is `minimum_tag_count`. Required columns are `id`, `md5`,
`file_ext`, `tag_string`, and `tag_count_general`. Extension comparison is
lowercase and exact; uppercase values and other formats are not selected.

The image root is always an `images/` directory beside the SQLite file. For an
eligible row, the derived path is:

```text
DATABASE_PARENT/images/MD5_FIRST_TWO/MD5.FILE_EXT
```

The database loader constructs this path but does not check its existence. Use
`training_preflight.py` before training. Its default image scan is bounded and
ordered by `id`; use `--max-image-checks 0` only for an intentionally complete
scan.

## Record and empty-selection failures

An existing database can still yield zero records because:

- `posts` is empty;
- every row is below `minimum_tag_count`;
- every extension falls outside lowercase `png`, `jpg`, and `jpeg`;
- fields are null or malformed;
- the configured file is a different SQLite database than intended.

Zero eligible records is a hard preflight failure. The training loop can still
advance epochs and save an effectively untrained model because the per-record
loop has no work. Likewise, an empty or null `tag_string` is not a useful
training record: it creates an all-zero target or can fail decoding of the
string value. Repair or exclude the row rather than accepting an empty target
silently.

## Tags and label vectors

`PROJECT/tags.txt` is read line by line. Surrounding whitespace is stripped and
blank lines are ignored; remaining order is preserved. That ordered list is
both the model output vocabulary and output dimension.

For each record, `tag_string` is decoded and split on spaces. The pipeline
creates a float32 vector with one element per project tag, assigning `1` when
the project tag occurs in the row tag list and `0` otherwise. Tags present in
the row but absent from `tags.txt` are ignored. Duplicate project-tag lines
produce duplicate output units and should be fixed before training.

Changing tag order or count while restoring an old checkpoint changes output
semantics and may cause shape failures. Keep the exact `tags.txt` with every
trained model.

## Image load, resize, and augmentation

The TensorFlow dataset starts from parallel arrays of derived image paths and
tag strings. It maps image loading in parallel, calls `ignore_errors()`, maps a
Python-backed transform/label function in parallel, batches without
`drop_remainder`, and prefetches with `AUTOTUNE`.

Image loading reads bytes, requests three channels, and first uses TensorFlow's
PNG decoder; the source contains a WebP fallback through TensorFlow I/O. The
SQLite query nevertheless selects `jpg` and `jpeg` as well as `png`. Treat row
selection and actual decode support as separate gates. Test each real encoding
in the chosen TensorFlow/TensorFlow-I/O environment—especially JPEG and WebP—
before a long run. A filename extension alone is not decode evidence.

Before augmentation, the image is resized with area interpolation to
`(int(image_height * pre_scale), int(image_width * pre_scale))`, preserving its
aspect ratio. `pre_scale` is the upper endpoint of `scale_range`, or `1.0` when
scaling is disabled.

For each sample, the Python transform chooses:

- scale uniformly from `scale_range`, then divides by its upper endpoint;
- rotation uniformly from `rotation_range`;
- independent x/y shifts uniformly from `shift_range`.

The helper then transforms and pads to exactly `image_width` by `image_height`.
Pixels are normalized by division by `255.0`. Null or empty range values disable
the corresponding random transform; otherwise each value must be a two-number
ordered range, and scale endpoints must be positive.

## `ignore_errors()` is not data validation

The pipeline's `ignore_errors()` can suppress upstream image read/decode errors.
Consequences include:

- a missing image can disappear from a batch without stopping the command;
- a checkpoint slice can advance by selected-record count even when fewer
  samples trained;
- throughput and `used_sample` can diverge from the database row count;
- all bad images in a slice can produce no training updates;
- successful checkpoint/model writes do not prove a usable dataset.

Preflight missing and zero-byte files, inspect format signatures, and perform a
small authorized decode/batch smoke before the expensive run. During training,
compare final `used_sample` with expected usable examples rather than relying
only on `offset` or epoch completion.

## Determinism limits

Record order begins as `ORDER BY id`. Each epoch then uses Python
`random.Random(random_seed).shuffle(image_records)`, with the seed stored in the
checkpoint and incremented after each epoch. This makes the record shuffle
resume-aware. Augmentation uses the module-level Python random generator inside
parallel `tf.py_function` calls, however, so full augmentation order is not
made deterministic by the checkpointed shuffle seed.

Do not claim bit-for-bit reproducibility solely from checkpoint restore. Record
package versions, CPU/GPU backend, thread/runtime settings, project JSON, tags,
database identity, and checkpoint lineage when reproducibility matters.
