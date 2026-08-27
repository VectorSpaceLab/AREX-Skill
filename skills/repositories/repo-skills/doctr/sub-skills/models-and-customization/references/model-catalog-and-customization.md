# Model Catalog and Customization

This reference covers docTR's standalone PyTorch model and predictor factories, custom weights, vocabulary whitelisting, and Hugging Face Hub integration. Use it when a user is working below the full `ocr_predictor` / `kie_predictor` pipeline level.

## Factory selection map

| User need | Use | Default architecture | Main output |
|---|---|---:|---|
| Detect text boxes/polygons on pages | `doctr.models.detection_predictor` | `fast_base` | per-page text localization predictions |
| Recognize already-cropped word images | `doctr.models.recognition_predictor` | `crnn_vgg16_bn` | `(text, confidence)` tuples |
| Detect document layout regions | `doctr.models.layout_predictor` | `lw_detr_s` | per-page region boxes, class names, scores |
| Detect table cells and logical structure in table crops/pages | `doctr.models.table_predictor` | `tablecenternet` | cells plus row/column coordinates |
| Classify crop/page orientation | `doctr.models.crop_orientation_predictor`, `doctr.models.page_orientation_predictor` | MobileNetV3 orientation variants | orientation class predictions |
| Load a shared raw model from Hugging Face Hub | `doctr.models.from_hub` | read from Hub `config.json` | raw docTR model instance |
| Restrict recognition vocab | `doctr.models.utils.add_whitelist` | n/a | removable whitelist hook |

Use a **predictor factory** when inputs are NumPy images/crops and you want preprocessing and postprocessing handled. Use a **raw model constructor** when training, loading weights, compiling, exporting to ONNX, or passing a custom model into a predictor.

## Current architecture catalog

### Detection architectures

Supported by `detection_predictor` and raw constructors under `doctr.models.detection`:

- `db_resnet34`
- `db_resnet50`
- `db_mobilenet_v3_large`
- `linknet_resnet18`
- `linknet_resnet34`
- `linknet_resnet50`
- `fast_tiny`
- `fast_small`
- `fast_base`

Notes:

- Detection predictor default: `fast_base`.
- Detection input shape in model configs is generally channel-first `(3, 1024, 1024)` before predictor preprocessing.
- `assume_straight_pages=False` is for rotated/skewed documents and polygon-like geometries; `True` fits straight boxes.
- `preserve_aspect_ratio=True` and `symmetric_pad=True` are default in the standalone detection predictor.
- FAST models are reparameterized inside `detection_predictor` for lower inference latency and memory usage.

### Recognition architectures

Supported by `recognition_predictor` and raw constructors under `doctr.models.recognition`:

- `crnn_vgg16_bn`
- `crnn_mobilenet_v3_small`
- `crnn_mobilenet_v3_large`
- `sar_resnet31`
- `master`
- `vitstr_small`
- `vitstr_base`
- `parseq`
- `viptr_tiny`

Notes:

- Recognition predictor default: `crnn_vgg16_bn`.
- Recognition input shape in model configs is generally `(3, 32, 128)`; the predictor preprocesses crops to height/width `(32, 128)` with aspect-ratio preservation.
- Most built-in pretrained recognition models use the French vocabulary by default. Inspect `predictor.model.cfg["vocab"]` or `predictor.model.vocab` before applying language constraints.
- For custom vocabularies, instantiate the raw recognition model with the same `vocab` used during training before calling `from_pretrained`.

### Layout architectures

Supported by `layout_predictor` and raw constructors under `doctr.models.layout`:

- `lw_detr_s`
- `lw_detr_m`

Notes:

- Layout predictor default: `lw_detr_s`.
- Layout input shape in model configs is generally `(3, 1024, 1024)`.
- Pass `class_names=[...]` to raw layout constructors for custom layout labels before loading matching weights.
- Layout class names are sorted by the constructor; keep the exact trained class-name set with the checkpoint.

### Table structure architectures

Supported by `table_predictor` and raw constructors under `doctr.models.table_structure`:

- `tablecenternet`

Notes:

- Table predictor default: `tablecenternet`.
- Standalone `table_predictor` runs table-structure recognition on supplied table crops/pages and returns cell geometry plus logical row/column coordinates.
- In the full OCR pipeline, table recognition is a separate `detect_tables=True` workflow that also requires layout regions; route those pipeline semantics to the core OCR/KIE sub-skill.

### Classification architectures

Raw classification constructors under `doctr.models.classification` include:

- `magc_resnet31`
- `mobilenet_v3_small`
- `mobilenet_v3_small_r`
- `mobilenet_v3_large`
- `mobilenet_v3_large_r`
- `resnet18`
- `resnet31`
- `resnet34`
- `resnet50`
- `resnet34_wide`
- `textnet_tiny`
- `textnet_small`
- `textnet_base`
- `vgg16_bn_r`
- `vit_s`
- `vit_b`
- `vip_tiny`
- `vip_base`
- `vit_det_s`
- `vit_det_m`
- `starnet_s3`

Orientation-specific classification architectures:

- `mobilenet_v3_small_crop_orientation`
- `mobilenet_v3_small_page_orientation`

Only the orientation-specific MobileNetV3 variants are accepted by `crop_orientation_predictor` and `page_orientation_predictor` when `arch` is a string. Those predictor factories also accept a matching raw MobileNetV3 instance or a compiled model wrapping one.

## Standalone predictor signatures

```python
from doctr.models import (
    detection_predictor,
    recognition_predictor,
    layout_predictor,
    table_predictor,
    crop_orientation_predictor,
    page_orientation_predictor,
)

# Text detection
detection_predictor(
    arch="fast_base",
    pretrained=False,
    assume_straight_pages=True,
    preserve_aspect_ratio=True,
    symmetric_pad=True,
    batch_size=2,
    **kwargs,
)

# Text recognition on cropped word images
recognition_predictor(
    arch="crnn_vgg16_bn",
    pretrained=False,
    symmetric_pad=False,
    batch_size=128,
    **kwargs,
)

# Layout region detection
layout_predictor(
    arch="lw_detr_s",
    pretrained=False,
    assume_straight_pages=True,
    preserve_aspect_ratio=True,
    symmetric_pad=True,
    batch_size=2,
    **kwargs,
)

# Table structure recognition
table_predictor(
    arch="tablecenternet",
    pretrained=False,
    assume_straight_pages=False,
    preserve_aspect_ratio=True,
    symmetric_pad=True,
    batch_size=2,
    **kwargs,
)

# Orientation classifiers
crop_orientation_predictor(
    arch="mobilenet_v3_small_crop_orientation",
    pretrained=False,
    batch_size=128,
    **kwargs,
)

page_orientation_predictor(
    arch="mobilenet_v3_small_page_orientation",
    pretrained=False,
    batch_size=4,
    **kwargs,
)
```

Common keyword behavior:

- `pretrained=True` loads pretrained weights and may require network/cache access.
- `pretrained=False` returns random weights; load a checkpoint before real inference.
- `pretrained_backbone` is accepted by several raw model/predictor paths and defaults to `True` for many architectures unless full pretrained weights are loaded.
- `batch_size` controls predictor preprocessing/model batching; increase only after checking memory.
- `mean`, `std`, and preprocessor flags may be overridden through predictor kwargs when you know the training preprocessing.

## Raw model constructor pattern

Most raw constructors follow:

```python
from doctr.models import db_resnet50, crnn_vgg16_bn, lw_detr_s, tablecenternet

model = db_resnet50(pretrained=False, **model_kwargs)
model.from_pretrained("weights.pt")
model.eval()
```

Useful raw-model kwargs by task:

| Task | Common kwargs |
|---|---|
| Detection | `pretrained_backbone`, `assume_straight_pages`, `class_names`, `exportable` |
| Recognition | `pretrained_backbone`, `vocab`, `input_shape`, `exportable` |
| Layout | `assume_straight_pages`, `class_names`, `exportable` |
| Table structure | `assume_straight_pages`, `exportable` |
| Classification | `classes`, `num_classes`, `exportable` where implemented by the architecture |

`from_pretrained(path_or_url, **kwargs)` loads a state dict through docTR's parameter loader. Instantiate the model with the same vocabulary, class names, input shape, and head dimensions used during training before loading weights.

## Custom model loading patterns

### Custom detection model in OCR composition

```python
from doctr.models import db_resnet50, ocr_predictor

custom_det = db_resnet50(pretrained=False, pretrained_backbone=False)
custom_det.from_pretrained("detector-weights.pt")
custom_det.eval()

predictor = ocr_predictor(
    det_arch=custom_det,
    reco_arch="vitstr_small",
    pretrained=True,
)
```

### Custom recognition vocabulary

```python
from doctr.datasets import VOCABS
from doctr.models import crnn_vgg16_bn, ocr_predictor

custom_reco = crnn_vgg16_bn(
    pretrained=False,
    pretrained_backbone=False,
    vocab=VOCABS["german"],
)
custom_reco.from_pretrained("recognizer-weights.pt")
custom_reco.eval()

predictor = ocr_predictor(
    det_arch="linknet_resnet18",
    reco_arch=custom_reco,
    pretrained=True,
)
```

If a recognition checkpoint was trained with a custom vocabulary, do not load it into the default French-vocabulary architecture. The projection layer size and decoder semantics must match.

### Custom layout labels

```python
from doctr.models import lw_detr_s, ocr_predictor

layout_model = lw_detr_s(
    pretrained=False,
    class_names=["figure", "heading", "paragraph", "table"],
)
layout_model.from_pretrained("layout-weights.pt")
layout_model.eval()

predictor = ocr_predictor(
    pretrained=True,
    detect_layout=True,
    layout_arch=layout_model,
)
```

Use the same class-name set that was used to train the layout checkpoint. The exported region type names come from this model configuration.

### Custom orientation models

```python
from doctr.models import (
    mobilenet_v3_small_crop_orientation,
    mobilenet_v3_small_page_orientation,
    ocr_predictor,
)
from doctr.models.classification.zoo import (
    crop_orientation_predictor,
    page_orientation_predictor,
)

crop_model = mobilenet_v3_small_crop_orientation(pretrained=False)
crop_model.from_pretrained("crop-orientation.pt")

page_model = mobilenet_v3_small_page_orientation(pretrained=False)
page_model.from_pretrained("page-orientation.pt")

predictor = ocr_predictor(
    pretrained=True,
    assume_straight_pages=False,
    straighten_pages=True,
    detect_orientation=True,
)
predictor.crop_orientation_predictor = crop_orientation_predictor(crop_model)
predictor.page_orientation_predictor = page_orientation_predictor(page_model)
```

Orientation classifiers matter only when page/crop orientation features are active, such as non-straight pages, page straightening, or explicit orientation detection.

### Custom table structure model

```python
from doctr.models import ocr_predictor, tablecenternet
from doctr.models.table_structure.zoo import table_predictor

custom_table = tablecenternet(pretrained=False)
custom_table.from_pretrained("table-structure.pt")
custom_table.eval()

predictor = ocr_predictor(
    pretrained=True,
    detect_layout=True,
    detect_tables=True,
)
predictor.table_predictor = table_predictor(custom_table)
```

For standalone table crops, use `table_predictor(custom_table)` directly. For full-page OCR table extraction, the pipeline must also locate table regions with a layout predictor.

### Custom preprocessor

Use this only when the model was trained with non-default resizing, means, standard deviations, padding, or batch size.

```python
from doctr.models.detection.predictor import DetectionPredictor
from doctr.models.preprocessor import PreProcessor
from doctr.models import db_resnet50

model = db_resnet50(pretrained=False)
model.from_pretrained("detector-weights.pt")

predictor = DetectionPredictor(
    PreProcessor(
        (1024, 1024),
        batch_size=1,
        mean=(0.798, 0.785, 0.772),
        std=(0.264, 0.2749, 0.287),
    ),
    model,
)
```

## Vocabulary whitelisting

Use `add_whitelist` when the model already knows all candidate characters but you want decoding constrained to a subset.

```python
from doctr.datasets import VOCABS
from doctr.models import ocr_predictor
from doctr.models.utils import add_whitelist

predictor = ocr_predictor(pretrained=True)
handle = add_whitelist(predictor, [VOCABS["polish"], VOCABS["german"]])
try:
    result = predictor(doc)
finally:
    handle.remove()
```

The returned handle also works as a context manager:

```python
with add_whitelist(predictor, VOCABS["german"]):
    result = predictor(doc)
```

Signature:

```python
add_whitelist(
    model,
    vocabs,
    *,
    strategy="mask",
    mapping=None,
    verbose=False,
)
```

Accepted `model` values:

- `ocr_predictor`
- `kie_predictor`
- `recognition_predictor`
- raw recognition model

Strategies:

- `strategy="mask"` (default): forbidden character logits are set to `-inf` before decoding.
- `strategy="nearest"`: forbidden character scores are reassigned to a closest allowed character before masking.

`mapping` is only valid with `strategy="nearest"`:

- `None` or `"anyascii"`: derive mappings by transliteration, e.g. accents to base ASCII where possible.
- `"weights"`: derive nearest allowed characters from projection-weight similarity.
- `dict`: override specific `{forbidden_char: allowed_char}` mappings.

Constraints:

- Whitelisting can only restrict a model vocabulary. Characters absent from the model vocabulary are ignored, not added.
- If the whitelist shares no character with the model vocabulary, docTR raises `ValueError`.
- The hook is removable; always remove it or use a context manager when switching languages.

## Hugging Face Hub model loading and sharing

### Load from Hub

```python
from doctr.models import from_hub, ocr_predictor

custom_det = from_hub("org/doctr-detector")
custom_reco = from_hub("org/doctr-recognizer")

predictor = ocr_predictor(det_arch=custom_det, reco_arch=custom_reco)
```

Signature:

```python
from_hub(repo_id: str, **kwargs)
```

Behavior:

- Downloads `config.json` and `pytorch_model.bin` from a Hugging Face model repo.
- Reads `task` and `arch` from the config.
- Supports `classification`, `detection`, `recognition`, `layout`, and `table_structure` tasks.
- Reconstructs task-specific metadata such as recognition `vocab`, recognition `input_shape`, classification `classes` / `num_classes`, and layout `class_names`.
- Passes `**kwargs` to the Hub download call, so use options such as revision pinning or local-file mode when needed.

### Push to Hub

```python
from doctr.models import login_to_hub, push_to_hf_hub
from doctr.models import recognition

login_to_hub()
model = recognition.crnn_mobilenet_v3_large(pretrained=False)
model.from_pretrained("recognizer-weights.pt")

push_to_hf_hub(
    model,
    model_name="doctr-crnn-mobilenet-v3-large-custom",
    task="recognition",
    arch="crnn_mobilenet_v3_large",
)
```

Signatures:

```python
login_to_hub() -> None
push_to_hf_hub(model, model_name: str, task: str, **kwargs) -> None
```

Push constraints:

- Provide either `arch=...` or a training `run_config` with an `arch` attribute.
- `task` must be one of `classification`, `detection`, `recognition`, `layout`, or `table_structure`.
- The architecture must belong to the task's supported architecture list.
- Existing Hub repositories are not overwritten by this helper.
- Pushing requires Hugging Face credentials and Git LFS availability; do not perform it without explicit user intent.

## Accepted custom instances in predictor factories

Predictor factories accept either an architecture string or a compatible model object:

| Factory | Accepted raw/compiled model classes |
|---|---|
| `detection_predictor` | DBNet, LinkNet, FAST, or a compiled module wrapping one |
| `recognition_predictor` | CRNN, SAR, MASTER, ViTSTR, PARSeq, VIPTR, or a compiled module wrapping one |
| `layout_predictor` | LWDETR or a compiled module wrapping one |
| `table_predictor` | TableCenterNet or a compiled module wrapping one |
| `crop_orientation_predictor` / `page_orientation_predictor` | MobileNetV3 orientation model or a compiled module wrapping one |

If the object type is not compatible, docTR raises `ValueError("unknown architecture ...")`.

## Related references

- For CUDA/MPS, half precision, compile, and ONNX details: [optimization-and-export.md](optimization-and-export.md)
- For failure modes: [troubleshooting.md](troubleshooting.md)
