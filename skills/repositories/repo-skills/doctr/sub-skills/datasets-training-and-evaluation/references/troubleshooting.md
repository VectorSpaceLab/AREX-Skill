# Troubleshooting datasets, training, and evaluation

Use this when a docTR dataset, DataLoader, training script, evaluation script, or metric fails.

## Fast triage checklist

1. Is the task family correct: detection, recognition, OCR, layout, table, character classification, or orientation classification?
2. Does the split root contain the expected `images/` folder and `labels.json` file?
3. Does every key in `labels.json` point to an existing image file under `images/`?
4. Are polygons/cells shaped as four 2D points?
5. Do class-name lists match polygon counts?
6. For recognition/OCR text, are labels UTF-8 strings and compatible with the selected vocab?
7. Is `collate_fn=dataset.collate_fn` passed to DataLoader?
8. Are `use_polygons`, `--rotation`, `--eval-straight`, and metric `use_polygons` consistent?
9. Is the run accidentally downloading built-in data or pretrained weights when the user expected local/offline execution?
10. Is the backend/device valid for the current hardware?

## Validator failures

Run the local validator first:

```bash
python scripts/validate_doctr_labels.py --task detection --dataset-root DATASET_ROOT
python scripts/validate_doctr_labels.py --task recognition --dataset-root DATASET_ROOT --warn-spaces
python scripts/validate_doctr_labels.py --task layout --dataset-root DATASET_ROOT
python scripts/validate_doctr_labels.py --task table --dataset-root DATASET_ROOT
python scripts/validate_doctr_labels.py --task ocr --dataset-root DATASET_ROOT
```

Common fixes:

- **Missing image**: labels use paths relative to the `images/` folder. Fix the key spelling, extension, or nesting.
- **Malformed JSON**: rewrite with double-quoted keys/strings and valid commas. Python dict syntax with single quotes is not JSON.
- **Polygon shape error**: every polygon must be exactly `[[x, y], [x, y], [x, y], [x, y]]` with numeric values.
- **Detection `polygons` wrong type**: use either a list of polygons or a dict mapping class names to lists of polygons.
- **Layout class mismatch**: `classes` must exist and have one string per polygon.
- **Table logic mismatch**: `logic` must have one `[start_col, end_col, start_row, end_row]` entry per cell.
- **Text label type error**: recognition values and OCR `typed_words[].value` must be strings.

## Dataset constructor errors

### `expected a path to a reachable folder`

The base dataset constructor expects an existing image folder. For custom datasets, pass `img_folder="DATASET_ROOT/images"` to the dataset class. For reference scripts, pass the split root to `--train_path` / `--val_path`, because the scripts append `images` internally.

### `unable to locate ...`

Either the labels file is missing, or an image key in the label JSON does not exist under the image folder. Use the validator to list missing paths.

### `polygons should be a dictionary or list`

`DetectionDataset` accepts:

- `"polygons": [polygon, ...]` for single-class detection.
- `"polygons": {"class_name": [polygon, ...]}` for multi-class/KIE-style detection.

It does not accept a flat numeric box list or a list of objects with class fields.

### `missing 'polygons'` / `missing 'classes'`

`LayoutDataset` requires both keys in every image annotation. If you have detection-style labels, convert them to layout labels by adding `classes` and using a list of polygons.

### `number of polygons ... does not match number of classes`

For layout, the i-th class labels the i-th polygon. Add/remove class entries so lengths match, or convert to multi-class detection if labels are class-keyed.

### `cells are expected to have shape (N, 4, 2)`

`TableStructureDataset` requires quadrilateral cell polygons, not straight boxes. Convert `[xmin, ymin, xmax, ymax]` into `[[xmin,ymin], [xmax,ymin], [xmax,ymax], [xmin,ymax]]` before loading.

### `logic is expected to have shape (N, 4)`

Each table cell needs exactly four integer coordinates: `[start_col, end_col, start_row, end_row]`. Ends are inclusive and indices are zero-based.

## Recognition and vocab errors

### `Some characters cannot be found in 'vocab'`

A label contains characters absent from the selected vocab. Fix by one of:

1. choose a larger/appropriate `VOCABS` entry,
2. construct the recognition model with a custom vocab matching the labels,
3. normalize labels intentionally with `translate`, recording the loss,
4. remove invalid labels from the training set.

Do not silently drop unsupported characters if exact text recovery matters.

### Spaces in labels

Default recognition workflows do not handle spaces as regular word labels. Crop text at word level, replace/normalize spaces intentionally, or train a model/vocab specifically designed for spaces.

### Tolerant metrics look good but raw score is poor

`TextMatch` tolerant variants can hide casing/accent/transliteration mistakes. Use `raw` for exact transcription acceptance; use tolerant metrics only for diagnostics unless the user explicitly accepts tolerant matching.

## DataLoader and transform errors

### Tensor stacking or default-collate failure

Detection, OCR, layout, table, and recognition targets are variable-sized or non-tensor objects. Build DataLoaders with:

```python
loader = DataLoader(dataset, batch_size=2, collate_fn=dataset.collate_fn)
```

### Layout batch returns a tuple for images

When `Resize(..., return_padding_mask=True)` is used, collation returns `(images, masks)` plus targets. Training loops for layout models may expect the padding mask.

### Boxes outside `[0, 1]`

Custom labels are absolute pixels, but dataset pre-transforms convert to relative coordinates. If boxes remain outside `[0, 1]` after loading, check image dimensions, transform order, and whether geometry was already normalized before the loader expected pixels.

### Rotation drops boxes

`RandomRotate` can discard boxes that become invalid after rotation. Use smaller `max_angle`, set `expand=True` when appropriate, or review very small/edge-touching boxes.

### Wrong shape under `use_polygons=True`

Rotated workflows expect `(N, 4, 2)` arrays. Straight workflows expect `(N, 4)`. Keep dataset, transforms, model postprocessor, and metric flags consistent.

## Script argument mistakes

### Local paths and built-in datasets mixed

Detection/recognition training scripts require exactly one data source mode per split:

- local: `--train_path TRAIN_ROOT` and `--val_path VAL_ROOT`, or
- built-in: `--train_datasets ...` and `--val_datasets ...`.

Do not pass both local and built-in arguments for a split.

### Recognition script unexpectedly uses synthetic data

If no local path or built-in dataset is provided, recognition training uses `WordGenerator`. Pass explicit `--train_path` / `--val_path` or `--train_datasets` / `--val_datasets` if synthetic fallback is not intended.

### Layout/table scripts reject missing paths

Layout and table training require local `--train_path` and `--val_path`. Prepare both split roots before calling them.

### Checkpoint and architecture mismatch

A checkpoint trained with one architecture or vocab/class layout may not load into another. Keep `arch`, vocab/class names, and task family identical unless you intentionally remap weights.

## DDP and GPU issues

### `LOCAL_RANK` or distributed initialization confusion

Use `torchrun`, not direct `python`, for DDP. `torchrun` sets `LOCAL_RANK`, `RANK`, and related variables.

### `nccl` unavailable

`nccl` is CUDA-oriented. If CUDA/NCCL is unavailable, use single-process training or choose a backend compatible with the environment. Do not force `nccl` on CPU-only systems.

### Invalid `--device`

For single-process scripts, `--device N` must be a valid visible CUDA index. Under DDP, the scripts ignore single-device choice and use rank-local devices.

### Out of memory

Reduce batch size, input size, workers, or AMP/rotation settings. Rotated polygon metrics and large layout/table inputs are memory-intensive. For validation only, consider straight-box evaluation when appropriate.

### Unexpected CPU fallback

Scripts may warn and use CPU when no accessible GPU is found. CPU training can be very slow; confirm with the user before continuing.

## Metrics returning `None` or zero

- `LocalizationConfusion.summary()` returns `None` for recall when no ground truths exist and for precision/mean IoU when no predictions exist.
- `TableCellMetric.summary()` returns `None` for precision/F1/structure accuracy when there are no predictions or no matches.
- All-zero precision with nonzero predictions often means boxes/classes do not match at the IoU threshold.
- Table structure accuracy can be `None` even when cells exist if no cell pair passes the IoU threshold.

Investigate empty labels, model output thresholds, class mappings, and geometry scaling before interpreting such metrics as final performance.

## Synthetic generator and font issues

### Font not found

`CharacterGenerator` and `WordGenerator` validate explicitly supplied font families. Use a font that is installed/locatable in the runtime or omit `font_family` to use defaults.

### Synthetic data does not represent target domain

Synthetic samples are useful for smoke tests and bootstrapping but can be visually unlike scanned documents. Do not infer real-world accuracy from synthetic-only validation.

## Offline and network caveats

- Built-in dataset options may download datasets.
- Pretrained/evaluation defaults may download weights when `pretrained=True` and no local cache exists.
- Latency scripts can instantiate pretrained models if asked.
- The bundled validator is safe for offline/local checks and does not import model code.

When the user requires no network, validate labels locally, avoid built-in datasets, avoid pretrained defaults, and use explicit local checkpoints.
