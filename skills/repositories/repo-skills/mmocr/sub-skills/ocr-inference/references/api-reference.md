# MMOCR inference API reference

Verified package facts for this generated skill: MMOCR 1.0.1 was inspected with a CPU import stack including Torch 2.1.2+cpu, MMCV 2.1.0, MMEngine 0.10.7, and MMDetection 3.3.0. Public inferencer imports were verified by the parent workflow; the current runtime still needs its own package availability and device checks before executing inference.

## Imports

```python
from mmocr.apis import (
    MMOCRInferencer,
    TextDetInferencer,
    TextRecInferencer,
    KIEInferencer,
    TextSpotInferencer,
)
```

## Constructor signatures and roles

| Class | Constructor shape | Role |
| --- | --- | --- |
| `MMOCRInferencer` | `MMOCRInferencer(det=None, det_weights=None, rec=None, rec_weights=None, kie=None, kie_weights=None, device=None)` | MMOCR-specific wrapper for detection, recognition, OCR, and KIE chains. At least one of `det`, `rec`, or `kie` is required. `kie` is valid only with both `det` and `rec`. |
| `TextDetInferencer` | `TextDetInferencer(model=None, weights=None, device=None, scope="mmocr")` | Standard text-detection inferencer. |
| `TextRecInferencer` | `TextRecInferencer(model=None, weights=None, device=None, scope="mmocr")` | Standard text-recognition inferencer. |
| `KIEInferencer` | `KIEInferencer(model=None, weights=None, device=None, scope="mmocr")` | Standard key-information-extraction inferencer. |
| `TextSpotInferencer` | `TextSpotInferencer(model=None, weights=None, device=None, scope="mmocr")` | Standard text-spotting inferencer. |

For standard inferencers, `model` can be a model-zoo name/alias or a local config path. `weights` can be a local checkpoint path or URL. If `model` is omitted, a compatible MMEngine checkpoint may supply config metadata through `weights`; otherwise construction can fail.

## Model-name and config examples

Common model aliases and metadata names observed in MMOCR inference docs, model metadata, and tests:

| Task | Examples |
| --- | --- |
| Detection | `DBNet`, `DB_r18`, `DBNetpp`, `dbnetpp`, `dbnet_resnet18_fpnc_1200e_icdar2015`, `dbnetpp_resnet50_fpnc_1200e_icdar2015`, `FCENet`, `PSENet`, `TextSnake`, `DRRG`, `MaskRCNN` |
| Recognition | `CRNN`, `crnn_mini-vgg_5e_mj`, `SAR`, `svtr-small`, `svtr-base`, `SATRN`, `ABINet`, `ASTER`, `MASTER`, `RobustScanner` |
| KIE | `SDMGR`, `sdmgr_unet16_60e_wildreceipt`, `sdmgr_novisual_60e_wildreceipt`, `sdmgr_novisual_60e_wildreceipt_openset` |
| Text spotting | Use a compatible local text-spotting config and checkpoint; the inspected core model-index metadata did not provide a ready text-spotting alias. |

A local config path can be used wherever a model name appears:

```python
from mmocr.apis import TextDetInferencer

inferencer = TextDetInferencer(
    model="local_dbnet_config.py",
    weights="local_dbnet_checkpoint.pth",
    device="cpu",
)
```

For `MMOCRInferencer`, use task-specific weight arguments:

```python
from mmocr.apis import MMOCRInferencer

ocr = MMOCRInferencer(
    det="local_det_config.py",
    det_weights="local_det_checkpoint.pth",
    rec="local_rec_config.py",
    rec_weights="local_rec_checkpoint.pth",
    device="cpu",
)
```

## Inputs

### Non-KIE inferencers

`MMOCRInferencer`, `TextDetInferencer`, `TextRecInferencer`, and `TextSpotInferencer` accept:

- `str`: image path, image URL, or image-directory path.
- `numpy.ndarray`: an image array in BGR channel order.
- `list`/`tuple`: a batch of paths, arrays, or mixed path/array elements.

When a directory path is supplied, MMOCR processes images in that directory. When arrays are supplied, output filenames are generated from numeric image names such as `0.jpg`/`0.json`.

### `KIEInferencer`

`KIEInferencer` accepts a `dict` or `list[dict]`. Each dictionary should contain:

- `img`: image path or BGR ndarray. Required for visual KIE configs; optional for no-visual configs when `img_shape` is supplied.
- `img_shape`: `(height, width)`. Required for no-visual KIE when `img` is absent.
- `instances`: list of text-node dictionaries. Runtime source and tests use `bbox` plus `text`:

```python
{
    "img": "receipt_or_form_image",
    "instances": [
        {"bbox": [10, 20, 120, 45], "text": "TOTAL"},
        {"bbox": [125, 20, 210, 45], "text": "$12.30"},
    ],
}
```

## Call signatures and important arguments

### `MMOCRInferencer.__call__`

Core call shape:

```python
result = inferencer(
    inputs,
    batch_size=1,
    det_batch_size=None,
    rec_batch_size=None,
    kie_batch_size=None,
    out_dir="results/",
    return_vis=False,
    save_vis=False,
    save_pred=False,
    print_result=False,
    show=False,
    wait_time=0,
    pred_score_thr=0.3,
)
```

Important behavior:

- `det_batch_size`, `rec_batch_size`, and `kie_batch_size` override `batch_size` for their individual stages when not `None`.
- `print_result=True` prints the prediction dictionary without visualization arrays.
- `show=True` displays a pop-up visualization window and should be avoided in headless sessions.
- `pred_score_thr` is passed to visualization drawing. It is not a general guarantee that returned JSON predictions are filtered.
- `save_vis=True` writes visualization images under `out_dir/vis/`.
- `save_pred=True` writes JSON predictions under `out_dir/preds/`.
- If `save_vis` or `save_pred` is true, `out_dir` must be non-empty. The default is `results/`; explicit empty strings are invalid with save flags.

### Standard inferencers' `__call__`

Core call shape:

```python
result = inferencer(
    inputs,
    return_datasamples=False,
    batch_size=1,
    progress_bar=True,
    return_vis=False,
    show=False,
    wait_time=0,
    draw_pred=True,
    pred_score_thr=0.3,
    out_dir="results/",
    save_vis=False,
    save_pred=False,
    print_result=False,
)
```

Additional notes:

- `return_datasamples=True` returns MMOCR/MMEngine DataSample objects instead of JSON-serializable dictionaries. Use this only when downstream Python code needs DataSample internals.
- `progress_bar=False` is useful for automated logs.
- `draw_pred=False` disables drawing predicted boxes for detection/spotting visualization.

## Output schemas

Every inferencer returns a dictionary with:

- `predictions`: one prediction entry per input image/item.
- `visualization`: visualization arrays only when `return_vis=True`; otherwise this is usually an empty list or `None`-like path through postprocessing even if visualization files were saved.

### `MMOCRInferencer` prediction keys

Depending on initialized mode, each prediction entry can contain:

- Detection: `det_polygons`, `det_scores`.
- Recognition: `rec_texts`, `rec_scores`.
- KIE: `kie_labels`, `kie_scores`, `kie_edge_scores`, `kie_edge_labels`.

The high-level OCR examples in docs/tests also show detection boxes in internal or visualization paths, but the high-level serialized result consistently uses `det_polygons` and `det_scores` for detection output.

### Standard prediction keys

| Inferencer | Prediction keys |
| --- | --- |
| `TextDetInferencer` | `polygons`, optional `bboxes`, `scores` |
| `TextRecInferencer` | `text`, `scores` |
| `KIEInferencer` | `labels`, `scores`, `edge_scores`, `edge_labels` |
| `TextSpotInferencer` | `polygons`, optional `bboxes`, `scores`, `texts` |

## Output files

With `out_dir="mmocr_outputs"`, `save_pred=True`, and `save_vis=True`, MMOCR writes:

```text
mmocr_outputs/
├── preds/
│   └── input_stem.json
└── vis/
    └── input_stem.jpg
```

For array inputs without a file name, stems are numeric and assigned by the inferencer, for example `0.json` and `0.jpg`.

## Device behavior

- `device=None`: MMEngine chooses an available device automatically.
- `device="cpu"`: safest portable choice.
- `device="cuda:0"`, `"cuda:1"`, etc.: use only when `torch.cuda.is_available()` and the requested index exists.

Specifying CUDA in a CPU-only environment can fail during model construction or checkpoint loading. CPU inference can be slow but is a valid preflight and lightweight debugging target for small images.

## CLI argument mapping

The bundled smoke helper follows the high-level `MMOCRInferencer` argument names and accepts both hyphenated and underscore save flags:

```bash
python scripts/mmocr_inference_smoke.py image_or_folder \
  --det DBNet --rec CRNN --device cpu \
  --out-dir mmocr_outputs/ocr --save-pred --save-vis
```

By default this command validates imports, inputs, selected models, device intent, and output flags without running inference. Add `--execute` to run, and add `--allow-download` only when model-zoo download/cache behavior is acceptable.
