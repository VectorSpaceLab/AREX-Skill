# Workflows

## Purpose

Read this for the common dataset-building patterns that future agents should
reuse without reopening the source checkout.

## 1. Local images plus table labels

Use this when the user has one image file per row and scalar labels in a CSV or
TSV file.

```python
import nitrain as nt
from nitrain import readers

base_dir = "/path/to/dataset"

dataset = nt.Dataset(
    inputs=readers.ImageReader("*/img3d.nii.gz"),
    outputs=readers.ColumnReader("age", base_file="participants.csv"),
    base_dir=base_dir,
)

x, y = dataset[0]
```

Tips:
- `base_dir` lets both readers resolve relative paths from the same dataset
  root.
- Use `ColumnReader(..., is_image=True)` if the table column stores image
  paths.
- Keep the reader labels stable if later transforms need to route by name.

## 2. Folder names as labels

Use `FolderNameReader` when classes are encoded in the parent directory.

```python
dataset = nt.Dataset(
    inputs=readers.ImageReader("*/*.nii.gz"),
    outputs=readers.FolderNameReader("*/*.nii.gz", format="integer"),
    base_dir=base_dir,
)
```

Good fits:
- classification datasets with one folder per class;
- image collections where the folder name is the ground truth label;
- quick smoke datasets with no companion CSV.

## 3. Nested or in-memory data

Use `infer_reader()` when the user already has lists, arrays, or nested dicts.

```python
import numpy as np
import ants
from nitrain.readers.utils import infer_reader

imgs = [ants.from_numpy(np.zeros((16, 16))) for _ in range(4)]
reader = infer_reader({"x": imgs, "y": imgs})
```

This is the cleanest route for:
- multiple aligned image inputs;
- nested structures that should stay keyed;
- arrays and images already loaded in memory.

## 4. Built-in tiny fixture

`fetch_data('example-01')` builds a local example directory with synthetic
images and a `participants.csv` table. Use it when you need a deterministic
fixture for smoke tests, demonstrations, or helper validation.

```python
base_dir = nt.fetch_data("example-01")
```

## 5. Google Cloud storage

Use `GoogleCloudDataset` when the dataset lives in a bucket and the caller has
real credentials.

```python
dataset = nt.GoogleCloudDataset(
    bucket="my-bucket",
    inputs=readers.ImageReader("sub-*/anat/*_T1w.nii.gz"),
    outputs=readers.ColumnReader("age", "participants.tsv"),
    base_dir="datasets/project-x/ds000000",
    credentials="/path/to/service-account.json",
)
```

This path depends on bucket access and object-path correctness. Keep it
explicit in troubleshooting notes.

## 6. Partitioning and subsetting

- `dataset.select(n, random=False)` is a subset helper.
- `dataset.split(0.8)` returns train/test.
- `dataset.split((0.8, 0.1, 0.1), random=True)` returns train/test/val.

Use deterministic splitting when you need reproducible smoke checks; use random
splits only when the user explicitly wants randomized sampling.
