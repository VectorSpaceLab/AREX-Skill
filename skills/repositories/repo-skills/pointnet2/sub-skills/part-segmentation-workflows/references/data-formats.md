# ShapeNetPart Data Formats

The repository uses two ShapeNetPart loaders. The training and evaluation path uses the normal all-category layout. The visualization script references an older single-category `points/points_label` layout. Validate the chosen layout before attributing failures to TensorFlow or model code.

## Normal all-category layout used by training and evaluation

`part_seg/train.py`, `part_seg/train_one_hot.py`, and `part_seg/evaluate.py` use `PartNormalDataset` from `part_dataset_all_normal.py` with the default root:

```text
data/shapenetcore_partanno_segmentation_benchmark_v0_normal/
  synsetoffset2category.txt
  train_test_split/
    shuffled_train_file_list.json
    shuffled_val_file_list.json
    shuffled_test_file_list.json
  <synset-offset>/
    <shape-id>.txt
    ...
```

`data/README.md` identifies the intended download as `shapenetcore_partanno_segmentation_benchmark_v0_normal.zip` and says to uncompress it under `data/`.

### `synsetoffset2category.txt`

Each non-empty line maps a human-readable category to a ShapeNet synset directory:

```text
Airplane 02691156
Chair 03001627
...
```

The loader builds `self.cat[category] = synset` and then builds `self.classes = dict(zip(self.cat, range(len(self.cat))))`. For the one-hot model, the class label comes from this loader. Keep the same file and loader behavior for training, checkpointing, and any patched inference path; do not invent an independent category-id order.

### Split JSON files

The loader reads:

- `train_test_split/shuffled_train_file_list.json`
- `train_test_split/shuffled_val_file_list.json`
- `train_test_split/shuffled_test_file_list.json`

For every JSON string it extracts `d.split('/')[2]` and treats that token as the `<shape-id>`. Typical entries therefore need at least three slash-separated components such as:

```json
"shape_data/02691156/1a04e3eab45ca15dd86060f189eb133"
```

The script's `trainval` split is the union of the extracted train and val id sets. `test` uses only the test id set.

### Normal sample files

Each category directory contains `<shape-id>.txt` files. `PartNormalDataset.__getitem__` loads the file with `numpy.loadtxt` and expects:

- columns 0:3: XYZ coordinates;
- columns 3:6: normals;
- last column: integer part label in the global ShapeNetPart label space.

The bundled validator checks for at least seven numeric columns. The source loader accepts all loaded rows, normalizes XYZ by centering and scaling to unit radius, samples `npoints` rows with replacement, and returns either:

- `(point_set, normal, seg)` for plain training/evaluation; or
- `(point_set, normal, seg, cls)` when `return_cls_label=True` for one-hot training.

## Global part-label ranges

`PartNormalDataset.seg_classes` maps 16 categories to the valid global labels:

| Category | Labels |
|---|---|
| Airplane | 0, 1, 2, 3 |
| Bag | 4, 5 |
| Cap | 6, 7 |
| Car | 8, 9, 10, 11 |
| Chair | 12, 13, 14, 15 |
| Earphone | 16, 17, 18 |
| Guitar | 19, 20, 21 |
| Knife | 22, 23 |
| Lamp | 24, 25, 26, 27 |
| Laptop | 28, 29 |
| Motorbike | 30, 31, 32, 33, 34, 35 |
| Mug | 36, 37 |
| Pistol | 38, 39, 40 |
| Rocket | 41, 42, 43 |
| Skateboard | 44, 45, 46 |
| Table | 47, 48, 49 |

The plain evaluator predicts 50 logits for every point, then restricts each shape to the valid labels for that shape's ground-truth category before computing IoU. This is why labels outside the category range indicate a data problem even if they are still between 0 and 49.

## Legacy single-category layout referenced by `test.py`

`part_seg/test.py` imports `PartDataset` from `part_dataset.py`. That loader expects a different layout:

```text
<legacy-shapenetpart-root>/
  synsetoffset2category.txt
  train_test_split/
    shuffled_train_file_list.json
    shuffled_val_file_list.json
    shuffled_test_file_list.json
  <synset-offset>/
    points/
      <shape-id>.pts
    points_label/
      <shape-id>.seg
```

The `.pts` file contains XYZ coordinates. The `.seg` file contains one label per point. `PartDataset` subtracts 1 from every segmentation label after loading, so this legacy path expects one-based labels on disk. It can filter categories with `class_choice`, for example `Airplane`.

The downloaded `_v0_normal` dataset used by the training scripts does **not** have this `points/points_label` shape. If a user wants visualization with the normal dataset, adapt `test.py` or write a wrapper around `PartNormalDataset` instead of pointing `PartDataset` at the normal root.

## Validator usage

From this sub-skill directory:

```bash
python scripts/validate_shapenetpart_layout.py /path/to/shapenetcore_partanno_segmentation_benchmark_v0_normal --format normal --split trainval
python scripts/validate_shapenetpart_layout.py /path/to/shapenetcore_partanno_segmentation_benchmark_v0_normal --format normal --split test --class-choice Airplane
python scripts/validate_shapenetpart_layout.py /path/to/legacy_shapenetpart --format legacy-points --split test --class-choice Airplane
```

Key options:

- `--split train|val|trainval|test`: match the source loader's split names.
- `--class-choice`: restrict validation to one or more categories; comma-separated values are accepted.
- `--allow-empty-split`: downgrade an empty selected split from error to warning.
- `--strict-labels`: require sampled labels to fall within the category's expected global label range for the normal layout, or be non-negative after the legacy loader's `-1` conversion.
- `--max-samples-per-category`: limit file-content checks so validation remains cheap on the full dataset.

A common difficult case is a directory tree that has all required folders and files, but the chosen split JSON does not include any shape id for the requested category. The validator reports that as an empty selected split rather than a missing-directory error.

## Data symptoms to map quickly

| Symptom | Likely cause | First check |
|---|---|---|
| `FileNotFoundError` or `IOError` for `synsetoffset2category.txt` | Dataset root is wrong or zip was not unpacked under the expected `data/` directory | Run the validator on the exact root the source script will use |
| Every category directory exists but train/test length is zero | Split JSON tokens do not match file basenames, or the selected category has no ids in that split | Validator output for split id counts and empty categories |
| `ValueError` from `numpy.loadtxt` | Sample file has a header, non-numeric columns, or missing XYZ/normal/label columns | Validator file-content errors |
| One-hot model trains but category conditioning seems wrong | Different `synsetoffset2category.txt` or class-id order was used between training and adaptation | Keep loader-derived class labels and avoid custom category-id tables |
| Visualization works for Airplane only or fails on other categories | `test.py` hardcodes stale single-category assumptions | Patch the visualization path using the global label ranges above |
