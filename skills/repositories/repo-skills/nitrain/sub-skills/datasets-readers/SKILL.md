---
name: datasets-readers
description: "Build Nitrain datasets from files, CSV/TSV columns, folder labels,
  in-memory data, example fixtures, and Google Cloud inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Datasets and readers

Use this sub-skill when a user needs to turn imaging files or tabular labels
into a `nitrain.Dataset`, infer a reader from nested Python objects, load the
built-in example fixture, or connect a dataset to Google Cloud storage.

## What belongs here

- `Dataset` creation from local filesystem paths or in-memory objects.
- Reader selection for image files, CSV/TSV columns, folder names, nested
  reader composition, and automatic inference.
- `fetch_data('example-01')` and the local tiny fixture it creates.
- `GoogleCloudDataset` and reader behavior that depends on cloud storage.

## What does not belong here

- Transforms, samplers, `Loader`, or Keras batching: use
  `sub-skills/preprocessing-and-loading/`.
- Architectures, trainers, pretrained weights, or framework training logic: use
  `sub-skills/models-training/`.
- Prediction and explanation post-processing: use
  `sub-skills/prediction-and-explanation/`.

## Typical user requests

- "Build a dataset from images and participants.csv"
- "Read labels from folder names"
- "Infer readers from nested lists or dictionaries"
- "Create the example-01 fixture"
- "Use GoogleCloudDataset for a bucket-backed dataset"

## Working pattern

1. Decide whether the input source is local files, in-memory data, or Google
   Cloud storage.
2. Pick the smallest reader that matches the data shape.
3. Use `base_dir` for directory-relative files and `base_file` for CSV/TSV
   columns.
4. Use `infer_reader()` when the user already has nested lists, arrays, or
   dictionaries and does not want to spell out reader classes manually.
5. Keep output labels explicit so later transforms and samplers can route by
   name.

## Read these references

- [references/api-reference.md](references/api-reference.md) for verified
  constructor signatures and return behavior.
- [references/workflows.md](references/workflows.md) for canonical
  dataset-building patterns and example snippets.
- [references/troubleshooting.md](references/troubleshooting.md) for missing
  files, mismatched lengths, malformed patterns, and GCS credential issues.

## Smoke check

After installing dependencies, run the bundled helper [scripts/check_install.py](../../scripts/check_install.py):

```bash
python scripts/check_install.py --mode datasets
```

Use this when you want to confirm the reader and dataset surface before moving
on to preprocessing or training.

## Key decision points

- Use `ImageReader` for file patterns that should resolve to ANTs images.
- Use `ColumnReader` for scalar labels or image paths stored in a table.
- Use `FolderNameReader` when folder names carry labels or classes.
- Use `MemoryReader` when data is already in memory.
- Use `ComposeReader` for multiple inputs that should stay aligned.
- Use `GoogleCloudDataset` only when bucket access and credentials are real.

## Common outcomes

- `Dataset.__getitem__` returns `(x, y)` pairs, and slices return sequences.
- `Dataset.split()` returns train/test or train/test/val partitions.
- `ImageReader`, `ColumnReader`, `FolderNameReader`, and `MemoryReader` all
  support `select()` for subset reuse.

## Watch for these signals

- "No file found" or "No filepaths found" usually means the pattern, base
  path, or exclude filter is wrong.
- Length mismatch warnings mean the reader mappings did not align.
- GCS failures usually come from credentials or object-path errors, not from
  the core Nitrain API.

## Before handing off

If the request grows into sampling, augmentation, batching, or model training,
hand off to the relevant sibling sub-skill instead of expanding this one.
