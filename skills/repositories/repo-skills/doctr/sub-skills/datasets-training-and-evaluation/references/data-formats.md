# Data formats and dataset APIs

This reference covers docTR dataset objects, custom JSON schemas, vocabularies, transforms, DataLoader collation, and synthetic generators for training/evaluation work.

## Dataset families

| Family | Loader or source | Target emitted by `dataset[i]` | Notes |
| --- | --- | --- | --- |
| Text detection | `DetectionDataset`; built-ins such as `CORD`, `FUNSD`, `IC03`, `IIIT5K`, `SVHN`, `SVT`, `SynthText`, and other dataset classes when `detection_task=True` | `Sample(image=tensor, target={class_name: boxes_or_polygons})` after pre-transform | Single-class labels use the default text class; class-specific polygon dictionaries support KIE-style/custom multi-class detection. |
| Text recognition | `RecognitionDataset`; built-ins with `recognition_task=True`; `WordGenerator` fallback in the recognition training script | `Sample(image=tensor, target=str)` | Labels must be UTF-8 strings compatible with the selected vocab. Spaces are not handled by the default recognition vocab workflows. |
| Full OCR labels | `OCRDataset` | `Sample(image=tensor, target={"boxes": array, "labels": list[str]})` | Use when each image has word boxes and word text labels together. |
| Layout detection | `LayoutDataset` | `Sample(image=tensor, mask=optional_padding_mask, target={class_name: boxes_or_polygons})` | Requires one class name per polygon. `class_names` reports the sorted set found in the label file. |
| Table structure | `TableStructureDataset` | `Sample(image=tensor, target={"cells": array, "logic": array})` | Cells are relative boxes by default after loading; logic is kept as integer `[start_col, end_col, start_row, end_row]`. |
| Orientation classification | `OrientationDataset`; orientation training script | `Sample(image=tensor, target=np.array([0]))` before script-specific transforms | The dataset initializes all local images with zero-degree targets; script logic handles page/crop orientation workflow. |
| Character classification | `CharacterGenerator`; character training script | `Sample(image=tensor, target=int)` | Synthetic characters are generated from the selected vocab. |
| Object/artefact detection | `DocArtefacts` or custom detection-style labels | `Sample(image=tensor, target={"boxes": array, "labels": class_ids_or_names})` depending on loader | Useful for non-text document artefact classes such as QR code, barcode, logo, photo, background. |

There is no separate custom `KIEDataset` class in the dataset API. For KIE-style detector training, use multi-class detection labels where each key under `polygons` is a semantic field/class.

## Common folder layout

Most local training/evaluation dataset roots use this shape:

```text
DATASET_ROOT/
  images/
    image_001.png
    image_002.jpg
    ...
  labels.json
```

Some classification/orientation workflows use only an image folder. For the detection/recognition/layout/table reference scripts, pass the split root (`DATASET_ROOT`), not `DATASET_ROOT/images`.

## Geometry conventions

- Polygon points are absolute pixel coordinates at label-file time: `[[x0, y0], [x1, y1], [x2, y2], [x3, y3]]`.
- For detection/layout, point order is not significant for conversion to straight boxes, but using a consistent corner order helps rotated training and human review.
- `use_polygons=False` converts each quad to a straight `[xmin, ymin, xmax, ymax]` box.
- `use_polygons=True` keeps an `(N, 4, 2)` polygon array for rotated boxes.
- Dataset pre-transforms convert geometry to relative coordinates in `[0, 1]` when appropriate.
- Table cell polygons are expected in top-left, top-right, bottom-right, bottom-left order because table logic is tied to cell layout.

## DetectionDataset labels

Constructor:

```python
from doctr.datasets import DetectionDataset

train_set = DetectionDataset(
    img_folder="DATASET_ROOT/images",
    label_path="DATASET_ROOT/labels.json",
    use_polygons=False,
)
```

Single-class detection schema:

```json
{
  "image_001.png": {
    "img_dimensions": [900, 600],
    "img_hash": "optional_sha256",
    "polygons": [
      [[10, 20], [70, 20], [70, 40], [10, 40]]
    ]
  }
}
```

Multi-class/KIE-style detection schema:

```json
{
  "invoice_001.png": {
    "img_dimensions": [1200, 900],
    "img_hash": "optional_sha256",
    "polygons": {
      "total": [
        [[880, 760], [1080, 760], [1080, 815], [880, 815]]
      ],
      "date": [
        [[80, 100], [250, 100], [250, 130], [80, 130]]
      ]
    }
  }
}
```

Loader behavior:

- If `polygons` is a list, every polygon is assigned the default text class.
- If `polygons` is a dictionary, keys become class names and values are per-class polygon lists.
- Missing image files are errors.
- `class_names` is the sorted unique class list discovered from labels.

## RecognitionDataset labels

Constructor:

```python
from doctr.datasets import RecognitionDataset

train_set = RecognitionDataset(
    img_folder="DATASET_ROOT/images",
    labels_path="DATASET_ROOT/labels.json",
)
```

Schema:

```json
{
  "word_001.png": "Invoice",
  "word_002.png": "2026-01-15",
  "word_003.png": "€42.00"
}
```

Recognition guidance:

- Save `labels.json` as UTF-8.
- Use one cropped word/string per image.
- Avoid spaces unless the selected model/vocab/training recipe is explicitly adapted for them.
- Validate labels against the selected vocab before training. Use `translate` for intentional lossy conversion, or fix labels/vocab when exact preservation is required.

## OCRDataset labels

Constructor:

```python
from doctr.datasets import OCRDataset

train_set = OCRDataset(
    img_folder="DATASET_ROOT/images",
    label_file="DATASET_ROOT/labels.json",
    use_polygons=False,
)
```

Schema:

```json
{
  "page_001.jpg": {
    "typed_words": [
      {"value": "Invoice", "geometry": [50, 60, 160, 90]},
      {"value": "Total", "geometry": [700, 780, 780, 815]}
    ]
  },
  "blank_or_unlabeled.jpg": {
    "typed_words": []
  }
}
```

Loader behavior:

- `geometry[:4]` is interpreted as a straight box `[xmin, ymin, xmax, ymax]`.
- With `use_polygons=True`, straight boxes are expanded to four-corner polygons.
- Empty `typed_words` is accepted and yields zero boxes plus an empty label list.

## LayoutDataset labels

Constructor:

```python
from doctr.datasets import LayoutDataset

train_set = LayoutDataset(
    img_folder="DATASET_ROOT/images",
    label_path="DATASET_ROOT/labels.json",
    use_polygons=False,
)
```

Schema:

```json
{
  "page_001.png": {
    "img_dimensions": [1200, 900],
    "img_hash": "optional_sha256",
    "polygons": [
      [[40, 30], [1150, 30], [1150, 100], [40, 100]],
      [[60, 160], [1100, 160], [1100, 760], [60, 760]]
    ],
    "classes": ["Header", "Text"]
  }
}
```

Hard requirements:

- `polygons` key must exist.
- `classes` key must exist.
- `len(polygons) == len(classes)`.
- Every polygon must have shape `(4, 2)`.

Use `Resize(..., return_padding_mask=True)` when a layout model expects padding masks with aspect-ratio preserving resize.

## TableStructureDataset labels

Constructor:

```python
from doctr.datasets import TableStructureDataset
from doctr.transforms import Resize, SampleCompose

train_set = TableStructureDataset(
    img_folder="DATASET_ROOT/images",
    label_path="DATASET_ROOT/labels.json",
    sample_transforms=SampleCompose([
        Resize((1024, 1024), preserve_aspect_ratio=True, symmetric_pad=True),
    ]),
    use_polygons=False,
)
```

Schema:

```json
{
  "table_001.png": {
    "cells": [
      [[20, 20], [120, 20], [120, 80], [20, 80]],
      [[120, 20], [250, 20], [250, 80], [120, 80]]
    ],
    "logic": [
      [0, 0, 0, 0],
      [1, 1, 0, 0]
    ]
  }
}
```

Hard requirements:

- `cells` shape is `(N, 4, 2)` in absolute pixel coordinates.
- `logic` shape is `(N, 4)`.
- `len(cells) == len(logic)`.
- Logic order is `[start_col, end_col, start_row, end_row]`; indices are zero-based and end indices are inclusive.

## VOCABS and encoding utilities

Use `VOCABS` when building or evaluating recognition/classification models:

```python
from doctr.datasets import VOCABS, encode_string, decode_sequence, encode_sequences, translate

vocab = VOCABS["french"]
encoded = encode_string("Facture", vocab)
assert decode_sequence(encoded, vocab) == "Facture"
```

Important utility behavior:

- `VOCABS` maps names such as `digits`, `latin`, `english`, `french`, `german`, `multilingual`, script-specific alphabets, and many language vocabularies to ordered character strings.
- `encode_string(text, vocab)` raises `ValueError` when a character is absent from the vocab.
- `decode_sequence(seq, vocab)` expects integer indices within the mapping length.
- `encode_sequences([...], vocab, target_size=..., eos=..., sos=..., pad=...)` requires EOS/SOS/PAD IDs to be outside regular vocab indices.
- `translate(text, vocab_name, unknown_char="■")` removes whitespace and normalizes or replaces unsupported characters. Use it only when lossy conversion is acceptable.

## Synthetic generators

Synthetic datasets are useful for smoke tests, character classifiers, or recognition fallback:

```python
from doctr.datasets import CharacterGenerator, WordGenerator, VOCABS
from doctr.transforms import Resize

chars = CharacterGenerator(
    vocab=VOCABS["digits"],
    num_samples=100,
    cache_samples=True,
    img_transforms=Resize((32, 32)),
)

words = WordGenerator(
    vocab=VOCABS["french"],
    min_chars=1,
    max_chars=12,
    num_samples=1000,
    cache_samples=False,
    img_transforms=Resize((32, 128)),
)
```

Generator behavior:

- `CharacterGenerator` target is an integer class index.
- `WordGenerator` target is a string.
- `font_family` may be a single font name/path or a list. If a listed font cannot be located, initialization raises an error.
- `cache_samples=True` pre-renders samples; it is deterministic over the cached list but consumes memory.

## Transforms and DataLoader

Use image transforms for image-only changes and sample transforms for image-plus-target geometry changes:

```python
from torch.utils.data import DataLoader
from doctr.datasets import DetectionDataset
from doctr.transforms import Resize, SampleCompose, RandomRotate

sample_transforms = SampleCompose([
    RandomRotate(max_angle=5, expand=False),
    Resize((1024, 1024), preserve_aspect_ratio=True, symmetric_pad=True),
])

ds = DetectionDataset(
    img_folder="DATASET_ROOT/images",
    label_path="DATASET_ROOT/labels.json",
    sample_transforms=sample_transforms,
    use_polygons=True,
)

loader = DataLoader(
    ds,
    batch_size=2,
    shuffle=True,
    num_workers=0,
    collate_fn=ds.collate_fn,
)
images, targets = next(iter(loader))
```

Rules of thumb:

- Always use `collate_fn=ds.collate_fn` for detection, OCR, layout, table, and variable-length recognition batches.
- For layout with padding masks, the batch image object may be `(images, masks)` rather than just `images`.
- `RandomRotate` and `Resize` understand both straight boxes `(N, 4)` and polygons `(N, 4, 2)`; keep shape consistent with `use_polygons`.
- `ImageTorchvisionTransform` wraps torchvision image-only transforms for sample objects.

## Local validation before loading

Run the bundled validator against local labels before instantiating dataset classes:

```bash
python scripts/validate_doctr_labels.py --task detection --dataset-root DATASET_ROOT
python scripts/validate_doctr_labels.py --task layout --dataset-root DATASET_ROOT --strict-doc-fields
python scripts/validate_doctr_labels.py --task recognition --dataset-root DATASET_ROOT --vocab-chars "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
python scripts/validate_doctr_labels.py --task table --dataset-root DATASET_ROOT
```

The validator catches missing images, malformed JSON, wrong polygon/cell shapes, class-count mismatches, non-string recognition labels, and table logic shape errors without importing docTR or starting training.
