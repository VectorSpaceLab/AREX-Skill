# Evaluation, training preflights, and metrics

This reference describes safe preflights, one-batch checks, evaluation metric interpretation, and handoff decisions before and after docTR training/evaluation runs.

## Recommended safety ladder

1. **Label/schema validation**: use `scripts/validate_doctr_labels.py` from this sub-skill. This is local and safe.
2. **Entrypoint/help check**: if the user's project or docTR source checkout provides a training/evaluation entry point, run its `--help` before any real work. This generated skill does not bundle the heavyweight source reference scripts.
3. **Dataset instantiation check**: instantiate the target dataset class with transforms and fetch one sample.
4. **DataLoader check**: build a DataLoader with `collate_fn=dataset.collate_fn` and fetch one batch.
5. **Tiny training/evaluation trial**: only if requested, run a bounded trial such as `--epochs 1`, a low batch size, and a dedicated output directory.
6. **Full run**: only after schema, batch, architecture, vocab/classes, device, and output policy are confirmed.

Do not skip directly from raw labels to full training when the data is custom or when the task uses rotated polygons/table logic.

## Local validator usage

```bash
python scripts/validate_doctr_labels.py --task detection --dataset-root TRAIN_ROOT
python scripts/validate_doctr_labels.py --task detection --dataset-root VAL_ROOT
python scripts/validate_doctr_labels.py --task recognition --dataset-root TRAIN_ROOT --warn-spaces
python scripts/validate_doctr_labels.py --task layout --dataset-root TRAIN_ROOT --strict-doc-fields
python scripts/validate_doctr_labels.py --task table --dataset-root TRAIN_ROOT
```

Useful validator options:

- `--dataset-root ROOT`: expects `ROOT/images` and `ROOT/labels.json`.
- `--img-folder DIR --labels FILE`: validate nonstandard locations.
- `--strict-doc-fields`: treat missing `img_dimensions` or `img_hash` as errors for detection/layout docs-style schemas.
- `--vocab-chars CHARS`: flag recognition/OCR labels containing characters outside a supplied custom vocab string.
- `--warn-spaces`: warn when text labels contain whitespace.
- `--max-warnings N`: cap warning output.

## One-sample dataset checks

Detection:

```python
from doctr.datasets import DetectionDataset
from doctr.transforms import Resize

train_set = DetectionDataset(
    img_folder="TRAIN_ROOT/images",
    label_path="TRAIN_ROOT/labels.json",
    img_transforms=Resize((1024, 1024)),
    use_polygons=False,
)
sample = train_set[0]
print(sample.image.shape, {k: v.shape for k, v in sample.target.items()})
print(train_set.class_names)
```

Recognition:

```python
from doctr.datasets import RecognitionDataset
from doctr.transforms import Resize

train_set = RecognitionDataset(
    img_folder="TRAIN_ROOT/images",
    labels_path="TRAIN_ROOT/labels.json",
    img_transforms=Resize((32, 128), preserve_aspect_ratio=True),
)
sample = train_set[0]
print(sample.image.shape, sample.target)
```

OCR labels:

```python
from doctr.datasets import OCRDataset
from doctr.transforms import Resize

train_set = OCRDataset(
    img_folder="TRAIN_ROOT/images",
    label_file="TRAIN_ROOT/labels.json",
    img_transforms=Resize((512, 512)),
    use_polygons=False,
)
sample = train_set[0]
print(sample.image.shape, sample.target["boxes"].shape, len(sample.target["labels"]))
```

Layout:

```python
from doctr.datasets import LayoutDataset
from doctr.transforms import Resize

train_set = LayoutDataset(
    img_folder="TRAIN_ROOT/images",
    label_path="TRAIN_ROOT/labels.json",
    img_transforms=Resize((1024, 1024), return_padding_mask=True),
    use_polygons=False,
)
sample = train_set[0]
print(sample.image.shape, sample.mask.shape if sample.mask is not None else None)
print({k: v.shape for k, v in sample.target.items()})
```

Table:

```python
from doctr.datasets import TableStructureDataset
from doctr.transforms import Resize, SampleCompose

train_set = TableStructureDataset(
    img_folder="TRAIN_ROOT/images",
    label_path="TRAIN_ROOT/labels.json",
    sample_transforms=SampleCompose([
        Resize((1024, 1024), preserve_aspect_ratio=True, symmetric_pad=True),
    ]),
    use_polygons=False,
)
sample = train_set[0]
print(sample.image.shape, sample.target["cells"].shape, sample.target["logic"].shape)
```

## DataLoader smoke check

```python
from torch.utils.data import DataLoader

loader = DataLoader(
    train_set,
    batch_size=2,
    shuffle=False,
    num_workers=0,
    collate_fn=train_set.collate_fn,
)
images, targets = next(iter(loader))
print(type(images), type(targets), len(targets))
```

Expected variants:

- Detection/OCR/layout/table targets are a list of per-sample targets because box counts vary.
- Recognition targets are a list of strings.
- Layout images may be `(images, masks)` if padding masks are returned.
- Table targets are dictionaries with `cells` and `logic` arrays.

If default collation is used accidentally, variable-size targets often raise tensor stacking errors. Always pass the dataset collation function for these workflows.

## Metrics and how to interpret them

### Recognition: `TextMatch`

`TextMatch` accumulates word-level text matching summaries:

- `raw`: exact string equality.
- `caseless`: lower-case equality.
- `anyascii`: equality after transliteration.
- `unicase`: lower-case after transliteration.

Use `raw` when exact casing/accents matter. Tolerant scores help diagnose casing/diacritic mistakes but should not replace the acceptance metric unless the task allows it.

### Detection/localization: `LocalizationConfusion`

Text detection evaluation reports:

- `recall`: matched ground-truth boxes divided by ground-truth count.
- `precision`: matched predictions divided by prediction count.
- `mean_iou`: average best IoU over predictions, rounded in the utility.

`use_polygons=True` expects `(N, 4, 2)` polygon arrays and uses polygon IoU. Otherwise boxes are `(N, 4)`.

### OCR: `OCRMetric`

`OCRMetric` combines localization matching and string matching. It returns:

- Recall dictionaries for raw/caseless/anyascii/unicase text matches.
- Precision dictionaries for the same text comparisons.
- Mean IoU for predicted boxes.

Use it when both word geometry and recognized text matter. Ensure `gt_boxes`/`pred_boxes` lengths match `gt_labels`/`pred_labels`.

### Multi-class/object detection: `DetectionMetric` and `ObjectDetectionMetric`

- `DetectionMetric` matches boxes and class labels at one IoU threshold and reports recall, precision, and mean IoU.
- `ObjectDetectionMetric` reports COCO-style `mAP@[.5:.95]`, `AP@[.5]`, `AP@[.75]`, and AP per IoU threshold. It expects prediction confidence scores.
- Layout reference scripts use COCO-style object detection metrics.

Use consistent class-index mappings between ground truth, model output, and metric update calls.

### Table: `TableCellMetric`

`TableCellMetric` matches predicted and ground-truth cells by IoU and reports:

- `recall`: matched cells divided by ground-truth cells.
- `precision`: matched cells divided by predicted cells.
- `f1`: harmonic mean of recall and precision when both are defined.
- `structure_acc`: matched cells with exactly correct logical coordinates divided by matched cells.

A table model can have high cell precision/recall but lower structure accuracy if row/column spans are wrong.

## Vocab and label acceptance checks

Before recognition/classification training:

```python
from doctr.datasets import VOCABS, encode_string

vocab = VOCABS["french"]
labels = ["Facture", "Total", "42€"]
for label in labels:
    encode_string(label, vocab)
```

If this raises `ValueError`, choose one of these outcomes:

1. Correct the label text.
2. Train/evaluate with a vocab containing all required characters.
3. Intentionally translate/normalize labels and record that the conversion is lossy.

For custom model loading later, the same vocab must be passed to the recognition model factory used with the checkpoint.

## Rotation and geometry consistency

Keep these switches aligned:

| Goal | Dataset / loader | Script flag | Metric |
| --- | --- | --- | --- |
| Straight boxes | `use_polygons=False` | omit `--rotation` | straight-box IoU |
| Rotated boxes | `use_polygons=True` | use `--rotation` | polygon IoU |
| Train rotated but validate cheaper straight boxes | training keeps polygons; validation converts straight | `--rotation --eval-straight` | straight-box validation metrics |

Do not mix straight labels with polygon-only postprocessing or polygon labels with straight-only metric assumptions without an explicit conversion.

## Training run planning

Before a real run, confirm:

- Task and available training/evaluation entry point, or the project script that will implement the docTR API loop.
- Architecture name.
- Train/validation sources and whether they are local or built-in.
- Dataset validation status.
- Vocab or class-name source.
- Input size and `Resize` strategy.
- Batch size, worker count, device, AMP, and DDP plan.
- Output directory and checkpoint retention policy.
- Resume checkpoint, if any.
- Evaluation metric and acceptance threshold.

Start small when uncertain: one epoch, low batch size, a dedicated output directory, and one validated train/validation split. Use the command-line options of the entry point available in the user's project, or implement the equivalent public-API loop described in [training-scripts.md](training-scripts.md).

## Evaluation-only planning

For evaluation-only requests:

1. Verify dataset label schema and image existence.
2. Verify model architecture and checkpoint task family.
3. Match vocab/classes and rotation flags to the checkpoint.
4. Run the selected evaluation entry point or project script with a low batch size first.
5. Record metric summary, checkpoint identifier, data split, and any skipped/empty metrics.

## Handoff to inference/model-loading skills

After training, route to model/customization or core OCR/KIE skills with:

- checkpoint file path or model registry location,
- architecture factory name,
- task family,
- class names or vocab,
- preprocessing/input size assumptions,
- rotation/table/layout flags,
- validation metrics,
- known data limitations.

Do not promise that a trained checkpoint is production-ready solely because a script completed; use held-out metrics and task-specific review.
