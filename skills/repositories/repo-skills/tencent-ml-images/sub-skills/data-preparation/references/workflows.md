# Data Preparation Workflows

These workflows replace the original short shell examples with safe commands
against bundled helper scripts. They are designed for a user's own checkout or
data workspace and do not depend on the checkout used to create this skill.

## 1. Validate source lists before doing any writes

```bash
python scripts/validate_ml_images_lists.py \
  --url-list train_urls_tiny.txt \
  --image-list train_im_list_tiny.txt \
  --dictionary dictionary_and_semantic_hierarchy.txt \
  --num-classes 11166 \
  --images-root images \
  --max-rows 100
```

Interpretation:

- `errors == 0` means the checked rows have parseable labels and in-range class
  ids.
- Missing images are errors unless `--allow-missing-images` is used.
- Dictionary row counts lower than `--num-classes` are warnings unless the task
  requires complete class lookup.

## 2. Dry-run a URL download plan

Always dry-run before allowing network writes:

```bash
python scripts/download_urls.py \
  --url-list train_urls_tiny.txt \
  --im-list train_im_list_tiny.out.txt \
  --save-dir images \
  --invalid-url-file invalid_url.txt \
  --num-threads 8 \
  --limit 10 \
  --dry-run
```

The dry run prints the derived output filename for each URL without contacting
the network. After the user approves network access and output paths, remove
`--dry-run`. Expect many historical public image URLs to be expired; treat
those as data availability issues rather than code failures.

## 3. Convert local image-list shards to TFRecords

Prepare directories like this:

```text
image_lists/
  shard_000.txt
  shard_001.txt
images/
  image_a.jpg
  image_b.jpg
tfrecords/
```

Then run:

```bash
python scripts/make_tfrecords.py \
  --index-dir image_lists \
  --tfrecord-dir tfrecords \
  --images-dir images \
  --num-classes 11166 \
  --one-hot true
```

For ImageNet-style single-label finetuning records, use `--one-hot false` and
ensure each row has exactly one integer class id after the image path.

Safety defaults:

- Existing output shard files are not overwritten unless `--overwrite` is
  supplied.
- `--max-files N` can limit conversion during smoke checks.
- Conversion requires TensorFlow 1.x or a compatible TensorFlow runtime exposing
  TFRecord and image-decode APIs.

## 4. Route converted data to training

For ML-Images pretraining, arrange the converted shards under a data root with
`train` and `val` split directories:

```text
ml-images/
  train/
    0.tfrecords
    1.tfrecords
  val/
    0.tfrecords
```

Then move to [../../resnet-training/SKILL.md](../../resnet-training/SKILL.md)
for command construction and training flags. Do not begin full training merely
because TFRecords were created; verify class count, image size, data format,
log/model directories, and runtime budget first.

## 5. What not to run by default

- Do not start bulk URL downloads without explicit network approval.
- Do not overwrite an existing TFRecord directory while testing list parsing.
- Do not use the full external ML-Images, OpenImages, or ImageNet datasets as a
  smoke test.
- Do not assume TensorFlow 2 behavior matches the original TensorFlow 1.x
  scripts until a tiny conversion passes.
