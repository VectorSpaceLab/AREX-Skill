# MMOCR inference workflows

This reference distills MMOCR inference behavior for future agents that need to run OCR tasks without re-reading repository docs or source files.

## Choose the inferencer

| Task | Preferred API | When to use | Typical model spec |
| --- | --- | --- | --- |
| Text detection | `MMOCRInferencer(det=...)` or `TextDetInferencer(model=...)` | Find text regions and scores. | `DBNet`, `DB_r18`, `DBNetpp`, `dbnetpp`, `FCENet`, `PSENet`, `TextSnake`, or a local text-detection config path. |
| Text recognition | `MMOCRInferencer(rec=...)` or `TextRecInferencer(model=...)` | Read text from cropped word/text-line images. | `CRNN`, `SAR`, `svtr-small`, `svtr-base`, `SATRN`, `ABINet`, `ASTER`, `MASTER`, or a local text-recognition config path. |
| OCR chain | `MMOCRInferencer(det=..., rec=...)` | Detect text, crop detections, then recognize text. | Detection model plus recognition model. Quick combinations include `DBNet`+`CRNN`, `DBNet`+`SAR`, and `DBNetpp`+`svtr-small`. |
| KIE chain | `MMOCRInferencer(det=..., rec=..., kie=...)` | Detect and read receipt/form text, then classify/relate text nodes. | Detection+recognition plus `SDMGR` or `sdmgr_unet16_60e_wildreceipt`. |
| Direct KIE | `KIEInferencer(model=...)` | Run KIE when boxes and text are already available. | `SDMGR`, `sdmgr_novisual_60e_wildreceipt`, or a local KIE config path. |
| Text spotting | `TextSpotInferencer(model=...)` | Use an end-to-end text-spotting model that directly predicts regions and text. | Prefer a compatible local text-spotting config+checkpoint; no core text-spotting model name was identified in the inspected model-index metadata. |

Use `MMOCRInferencer` for fast chaining and user-facing OCR. Use standard inferencers (`TextDetInferencer`, `TextRecInferencer`, `KIEInferencer`, `TextSpotInferencer`) when integrating one task into custom Python code or when direct task-specific output schemas are easier to consume.

## Model and checkpoint selection

MMOCR accepts two model-spec styles:

1. **Model-zoo name or alias** such as `DBNet`, `CRNN`, `SAR`, `SDMGR`, `svtr-small`, or a full metadata name such as `dbnet_resnet18_fpnc_1200e_icdar2015`.
2. **Local config path** to a `.py` config. Pair it with the corresponding checkpoint path through `weights` for standard inferencers, or `det_weights`, `rec_weights`, and `kie_weights` for `MMOCRInferencer`.

A model-zoo name without a supplied local checkpoint can trigger a download/cache lookup during real inference. In offline, reproducible, or bandwidth-limited runs, pass local checkpoints explicitly:

```python
from mmocr.apis import MMOCRInferencer

ocr = MMOCRInferencer(
    det="local_dbnet_config.py",
    det_weights="local_dbnet_checkpoint.pth",
    rec="local_crnn_config.py",
    rec_weights="local_crnn_checkpoint.pth",
    device="cpu",
)
```

Passing a local config path without weights constructs a randomly initialized model unless the checkpoint/config loading path supplies weights separately; this is normally unsuitable for useful OCR predictions.

## Headless OCR chain

Use this pattern on servers or CI where pop-up GUI windows are unavailable:

```python
from mmocr.apis import MMOCRInferencer

ocr = MMOCRInferencer(det="DBNet", rec="CRNN", device="cpu")
result = ocr(
    "image_or_folder",
    batch_size=1,
    det_batch_size=1,
    rec_batch_size=4,
    out_dir="mmocr_outputs/ocr",
    save_pred=True,
    save_vis=True,
    return_vis=False,
    print_result=True,
    show=False,
)

for item in result["predictions"]:
    print(item.get("rec_texts", []))
```

Expected high-level OCR prediction keys include `det_polygons`, `det_scores`, `rec_texts`, and `rec_scores`. Saved JSON files go under `mmocr_outputs/ocr/preds/`; saved visualization images go under `mmocr_outputs/ocr/vis/`.

## Detection only

```python
from mmocr.apis import TextDetInferencer

inferencer = TextDetInferencer(model="DBNet", device="cpu")
result = inferencer(
    "image_or_folder",
    batch_size=2,
    out_dir="mmocr_outputs/det",
    save_pred=True,
    save_vis=True,
    show=False,
    pred_score_thr=0.3,
)

first = result["predictions"][0]
polygons = first.get("polygons", [])
scores = first.get("scores", [])
```

`pred_score_thr` is a visualization threshold for drawing predictions. Do not treat it as proof that low-score items were removed from every returned or dumped data structure unless the downstream code explicitly checks the returned values.

## Recognition only

```python
from mmocr.apis import TextRecInferencer

inferencer = TextRecInferencer(model="CRNN", device="cpu")
result = inferencer(
    ["word_crop_1.jpg", "word_crop_2.jpg"],
    batch_size=8,
    out_dir="mmocr_outputs/rec",
    save_pred=True,
    show=False,
)

for pred in result["predictions"]:
    print(pred["text"], pred["scores"])
```

Recognition inputs should already be cropped text images. For whole-scene images, use a detection+recognition OCR chain instead.

## KIE chain through `MMOCRInferencer`

```python
from mmocr.apis import MMOCRInferencer

kie = MMOCRInferencer(det="DBNet", rec="SAR", kie="SDMGR", device="cpu")
result = kie(
    "receipt_or_form_image",
    det_batch_size=1,
    rec_batch_size=4,
    kie_batch_size=1,
    out_dir="mmocr_outputs/kie",
    save_pred=True,
    save_vis=True,
    show=False,
)

pred = result["predictions"][0]
print(pred.get("kie_labels", []), pred.get("kie_edge_labels", []))
```

KIE through `MMOCRInferencer` is only valid when both detection and recognition are also initialized. MMOCR builds KIE instances from detection boxes and recognized text. If detection returns no boxes, KIE can fail before producing useful KIE outputs.

## Direct `KIEInferencer` with existing boxes and text

Use direct KIE only when boxes/text are already available or when a KIE-specific pipeline expects structured inputs:

```python
from mmocr.apis import KIEInferencer

kie_input = {
    "img": "receipt_or_form_image",
    "instances": [
        {"bbox": [10, 20, 120, 45], "text": "TOTAL"},
        {"bbox": [125, 20, 210, 45], "text": "$12.30"},
    ],
}

inferencer = KIEInferencer(model="SDMGR", device="cpu")
result = inferencer(kie_input, out_dir="mmocr_outputs/direct_kie", save_pred=True, show=False)
```

For no-visual KIE configs, provide either `img` or `img_shape`; for visual KIE configs, provide `img`. Instance dictionaries use `bbox` and `text` keys.

## Text spotting notes

`TextSpotInferencer` is available as a standard inferencer and returns polygons/bboxes/scores plus recognized `texts`. The high-level `MMOCRInferencer` documentation described text-spotting OCR as not yet part of its chain interface. Prefer `TextSpotInferencer` only when you already have a compatible text-spotting config and checkpoint:

```python
from mmocr.apis import TextSpotInferencer

spotter = TextSpotInferencer(
    model="local_textspotting_config.py",
    weights="local_textspotting_checkpoint.pth",
    device="cpu",
)
result = spotter("image_or_folder", out_dir="mmocr_outputs/spot", save_pred=True, save_vis=True, show=False)
```

If the text-spotting model depends on custom project components, route component registration and implementation questions to `../model-api-components/`.

## Safe CLI preflight and opt-in execution

The bundled helper provides an adapted, safer CLI surface for inference preflight. It imports MMOCR inferencers, prints package versions, validates common model names or local config paths, checks the input path when supplied, checks device intent, and does not download weights by default.

From this sub-skill directory:

```bash
python scripts/mmocr_inference_smoke.py image_or_folder --det DBNet --rec CRNN --device cpu
```

To actually execute through the helper, opt in explicitly. Use local checkpoints for no-download execution:

```bash
python scripts/mmocr_inference_smoke.py image_or_folder \
  --det local_dbnet_config.py --det-weights local_dbnet_checkpoint.pth \
  --rec local_crnn_config.py --rec-weights local_crnn_checkpoint.pth \
  --device cpu --out-dir mmocr_outputs/ocr --save-pred --save-vis --execute
```

If you intentionally want MMOCR to use model-zoo names and fetch or resolve cached pretrained weights, add `--allow-download` with `--execute`.
